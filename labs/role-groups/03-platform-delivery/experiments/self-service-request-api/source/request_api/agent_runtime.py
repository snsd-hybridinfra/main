from __future__ import annotations

import copy
import json
import re
from datetime import datetime, timezone
from typing import Any

from .agent_jobs import RUNTIME_CLASS, canonical_digest


REDIS_STREAM = "mini-ona.jobs.v1"
REDIS_CONSUMER_GROUP = "mini-ona-workers-v1"
DEAD_LETTER_STREAM = "mini-ona.jobs.dlq.v1"
APPROVED_IMAGE_PATTERN = re.compile(
    r"^registry\.internal/mini-ona/agent@sha256:[0-9a-f]{64}$"
)


class RuntimeGateError(RuntimeError):
    pass


def activate_sandbox_bundle(
    bundle: dict[str, Any],
    *,
    source_digest: str,
    decision_id: str,
    approved_source_digest: str,
    image_reference: str,
    expires_at: datetime,
) -> tuple[dict[str, Any], str]:
    if canonical_digest(bundle) != source_digest or approved_source_digest != source_digest:
        raise RuntimeGateError("sandbox activation digest mismatch")
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9_-]{7,63}", decision_id):
        raise RuntimeGateError("sandbox activation decision identifier is invalid")
    if expires_at.tzinfo is None or expires_at <= datetime.now(timezone.utc):
        raise RuntimeGateError("sandbox activation decision is expired")
    if not APPROVED_IMAGE_PATTERN.fullmatch(image_reference):
        raise RuntimeGateError("sandbox image is not an approved digest-pinned image")
    pod = bundle.get("job", {}).get("spec", {}).get("template", {}).get("spec", {})
    if pod.get("runtimeClassName") != RUNTIME_CLASS:
        raise RuntimeGateError("sandbox RuntimeClass differs from the approved class")
    if bundle.get("runtime_authorized") is not False or bundle.get("deployable") is not False:
        raise RuntimeGateError("sandbox source bundle must be inert")

    active = copy.deepcopy(bundle)
    active["runtime_authorized"] = True
    active["deployable"] = True
    active["activation"] = {
        "decision_id": decision_id,
        "approved_source_digest": approved_source_digest,
        "expires_at": expires_at.astimezone(timezone.utc).isoformat(),
    }
    job = active["job"]
    job["metadata"]["annotations"]["platform.snsd/runtime-authorized"] = "true"
    job["metadata"]["annotations"]["platform.snsd/activation-decision"] = decision_id
    job["spec"]["template"]["spec"]["containers"][0]["image"] = image_reference
    return active, canonical_digest(active)


class RedisStreamsAdapter:
    def __init__(self, client: Any, *, stream: str = REDIS_STREAM, group: str = REDIS_CONSUMER_GROUP):
        self.client = client
        self.stream = stream
        self.group = group

    @classmethod
    def from_url(cls, redis_url: str, **kwargs: Any) -> "RedisStreamsAdapter":
        if not redis_url.startswith(("redis://", "rediss://")) or "@" in redis_url.split("://", 1)[1].split("/", 1)[0]:
            raise RuntimeGateError("Redis URL must not embed credentials")
        import redis

        return cls(redis.Redis.from_url(redis_url, decode_responses=True, **kwargs))

    def ensure_group(self) -> None:
        try:
            self.client.xgroup_create(self.stream, self.group, id="0", mkstream=True)
        except Exception as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    def publish(self, envelope: dict[str, Any], envelope_digest: str) -> str:
        if canonical_digest(envelope) != envelope_digest:
            raise RuntimeGateError("queue envelope digest mismatch")
        if envelope.get("runtime_authorized") is not False:
            raise RuntimeGateError("queue envelope must remain runtime unauthorized")
        forbidden = {"token", "secret", "credential", "prompt", "source_code", "command"}
        if any(word in json.dumps(envelope, sort_keys=True).lower() for word in forbidden):
            raise RuntimeGateError("queue envelope contains a prohibited field")
        return str(
            self.client.xadd(
                self.stream,
                {
                    "job_id": envelope["job_id"],
                    "envelope_digest": envelope_digest,
                    "payload": json.dumps(envelope, sort_keys=True, separators=(",", ":")),
                },
                maxlen=10_000,
                approximate=True,
            )
        )

    def claim(self, consumer: str, *, block_ms: int = 1000) -> tuple[str, dict[str, Any]] | None:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,62}", consumer):
            raise RuntimeGateError("Redis consumer name is invalid")
        messages = self.client.xreadgroup(
            self.group,
            consumer,
            {self.stream: ">"},
            count=1,
            block=block_ms,
        )
        if not messages:
            return None
        _, entries = messages[0]
        message_id, fields = entries[0]
        payload = json.loads(fields["payload"])
        if canonical_digest(payload) != fields["envelope_digest"]:
            raise RuntimeGateError("claimed queue envelope digest mismatch")
        return str(message_id), payload

    def acknowledge(self, message_id: str) -> int:
        return int(self.client.xack(self.stream, self.group, message_id))


class KubernetesSandboxController:
    def __init__(self, core_api: Any, batch_api: Any, networking_api: Any):
        self.core_api = core_api
        self.batch_api = batch_api
        self.networking_api = networking_api

    @classmethod
    def from_default_context(cls) -> "KubernetesSandboxController":
        from kubernetes import client, config

        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()
        return cls(client.CoreV1Api(), client.BatchV1Api(), client.NetworkingV1Api())

    def apply(self, bundle: dict[str, Any], bundle_digest: str) -> str:
        if canonical_digest(bundle) != bundle_digest:
            raise RuntimeGateError("active sandbox bundle digest mismatch")
        if bundle.get("runtime_authorized") is not True or bundle.get("deployable") is not True:
            raise RuntimeGateError("sandbox bundle is not authorized for deployment")
        activation = bundle.get("activation", {})
        if not activation.get("decision_id"):
            raise RuntimeGateError("sandbox activation decision is missing")
        expires_at = datetime.fromisoformat(str(activation.get("expires_at", "")))
        if expires_at <= datetime.now(timezone.utc):
            raise RuntimeGateError("sandbox activation decision expired before apply")
        namespace = bundle["namespace"]
        pod = bundle["job"]["spec"]["template"]["spec"]
        if pod.get("runtimeClassName") != RUNTIME_CLASS:
            raise RuntimeGateError("sandbox RuntimeClass is not approved")
        image = pod["containers"][0]["image"]
        if not APPROVED_IMAGE_PATTERN.fullmatch(image):
            raise RuntimeGateError("sandbox image is not approved")

        namespace_body = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": namespace,
                "labels": {
                    "platform.snsd/workload": "ai-agent-sandbox",
                    "pod-security.kubernetes.io/enforce": "restricted",
                },
            },
        }
        created_namespace = False
        try:
            self.core_api.create_namespace(body=namespace_body)
            created_namespace = True
            self.core_api.create_namespaced_resource_quota(namespace, body=bundle["resource_quota"])
            self.networking_api.create_namespaced_network_policy(namespace, body=bundle["network_policy"])
            self.batch_api.create_namespaced_job(namespace, body=bundle["job"])
        except Exception:
            if created_namespace:
                self.core_api.delete_namespace(namespace)
            raise
        return namespace

    def cleanup(self, namespace: str) -> None:
        if not re.fullmatch(r"agent-job-[0-9a-f]{12}", namespace):
            raise RuntimeGateError("refusing to delete a non-agent namespace")
        self.core_api.delete_namespace(namespace)
