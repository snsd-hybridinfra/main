from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from request_api.agent_jobs import build_sandbox_bundle
from request_api.agent_runtime import (
    KubernetesSandboxController,
    RedisStreamsAdapter,
    RuntimeGateError,
    activate_sandbox_bundle,
)


JOB_ID = str(UUID(int=1))
IMAGE = "registry.internal/mini-ona/agent@sha256:" + "d" * 64


def inert_bundle():
    return build_sandbox_bundle(
        job_id=JOB_ID,
        repository_alias="approved_repo_01",
        source_commit="a" * 40,
        task_digest="sha256:" + "b" * 64,
        environment="TEST",
        size="STANDARD",
    )


def activated_bundle():
    bundle, digest = inert_bundle()
    return activate_sandbox_bundle(
        bundle,
        source_digest=digest,
        decision_id="RUNTIME_APPROVAL_001",
        approved_source_digest=digest,
        image_reference=IMAGE,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )


def test_activation_requires_digest_decision_expiry_image_and_runtime_class() -> None:
    bundle, digest = inert_bundle()
    active, active_digest = activated_bundle()
    assert active["runtime_authorized"] is True
    assert active["deployable"] is True
    assert active["job"]["spec"]["template"]["spec"]["runtimeClassName"] == "kata-qemu-runtime-rs"
    assert active["job"]["spec"]["template"]["spec"]["containers"][0]["image"] == IMAGE
    assert active_digest.startswith("sha256:")

    for values in (
        {"source_digest": "sha256:" + "0" * 64},
        {"decision_id": "bad"},
        {"image_reference": "docker.io/untrusted/latest"},
        {"expires_at": datetime.now(timezone.utc) - timedelta(seconds=1)},
    ):
        kwargs = {
            "source_digest": digest,
            "decision_id": "RUNTIME_APPROVAL_001",
            "approved_source_digest": digest,
            "image_reference": IMAGE,
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
            **values,
        }
        with pytest.raises(RuntimeGateError):
            activate_sandbox_bundle(bundle, **kwargs)


class FakeRedis:
    def __init__(self):
        self.added = []
        self.claimed = []
        self.acked = []

    def xgroup_create(self, *args, **kwargs):
        return True

    def xadd(self, stream, fields, **kwargs):
        self.added.append((stream, fields, kwargs))
        self.claimed.append((stream, [("1-0", fields)]))
        return "1-0"

    def xreadgroup(self, *args, **kwargs):
        result, self.claimed = self.claimed, []
        return result

    def xack(self, stream, group, message_id):
        self.acked.append((stream, group, message_id))
        return 1


def test_redis_stream_adapter_publishes_claims_and_acknowledges_digest_bound_envelope() -> None:
    fake = FakeRedis()
    adapter = RedisStreamsAdapter(fake)
    adapter.ensure_group()
    envelope = {
        "job_id": JOB_ID,
        "repository_alias": "approved_repo_01",
        "source_commit": "a" * 40,
        "runtime_authorized": False,
    }
    from request_api.agent_jobs import canonical_digest

    digest = canonical_digest(envelope)
    assert adapter.publish(envelope, digest) == "1-0"
    message_id, claimed = adapter.claim("worker-001")
    assert message_id == "1-0"
    assert claimed == envelope
    assert adapter.acknowledge(message_id) == 1
    assert fake.acked[0][2] == "1-0"

    with pytest.raises(RuntimeGateError):
        adapter.publish({**envelope, "command": "unsafe"}, canonical_digest({**envelope, "command": "unsafe"}))
    with pytest.raises(RuntimeGateError):
        adapter.claim("INVALID_CONSUMER")


class FakeCore:
    def __init__(self, fail_quota=False):
        self.calls = []
        self.fail_quota = fail_quota

    def create_namespace(self, body):
        self.calls.append(("create_namespace", body["metadata"]["name"]))

    def create_namespaced_resource_quota(self, namespace, body):
        self.calls.append(("quota", namespace))
        if self.fail_quota:
            raise RuntimeError("synthetic quota failure")

    def delete_namespace(self, namespace):
        self.calls.append(("delete_namespace", namespace))


class FakeBatch:
    def __init__(self):
        self.calls = []

    def create_namespaced_job(self, namespace, body):
        self.calls.append((namespace, body["metadata"]["name"]))


class FakeNetwork:
    def __init__(self):
        self.calls = []

    def create_namespaced_network_policy(self, namespace, body):
        self.calls.append((namespace, body["metadata"]["name"]))


def test_kubernetes_controller_applies_in_order_and_rolls_back_namespace_on_failure() -> None:
    active, digest = activated_bundle()
    core, batch, network = FakeCore(), FakeBatch(), FakeNetwork()
    controller = KubernetesSandboxController(core, batch, network)
    namespace = controller.apply(active, digest)
    assert namespace.startswith("agent-job-")
    assert [call[0] for call in core.calls] == ["create_namespace", "quota"]
    assert network.calls and batch.calls
    controller.cleanup(namespace)
    assert core.calls[-1] == ("delete_namespace", namespace)
    with pytest.raises(RuntimeGateError):
        controller.cleanup("default")

    failing_core = FakeCore(fail_quota=True)
    failing = KubernetesSandboxController(failing_core, FakeBatch(), FakeNetwork())
    with pytest.raises(RuntimeError, match="synthetic quota failure"):
        failing.apply(active, digest)
    assert failing_core.calls[-1][0] == "delete_namespace"

    inert, inert_digest = inert_bundle()
    with pytest.raises(RuntimeGateError):
        controller.apply(inert, inert_digest)
