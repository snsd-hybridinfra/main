#!/usr/bin/env python3
"""Run a deterministic local Hub-to-Spoke cache experiment."""
import argparse
import hashlib
import json
import shutil
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


def write_dataset(hub: Path, file_count: int, file_size: int):
    manifest = {}
    for index in range(file_count):
        seed = hashlib.sha256(f"synthetic-dataset-{index}".encode()).digest()
        content = (seed * ((file_size // len(seed)) + 1))[:file_size]
        path = hub / f"shard-{index:02d}.bin"
        path.write_bytes(content)
        manifest[path.name] = hashlib.sha256(content).hexdigest()
    return manifest


def fetch_from_hub(hub: Path, cached: Path, latency_seconds: float):
    time.sleep(latency_seconds)
    shutil.copyfile(hub / cached.name, cached)
    return cached.stat().st_size


def read_epoch(hub: Path, cache: Path, manifest, latency_seconds: float, repair_corrupt=False):
    hits = 0
    misses = 0
    origin_requests = 0
    origin_bytes = 0
    verified = 0
    integrity_failures = 0
    repaired_files = 0
    started = time.perf_counter()

    for name, expected_hash in sorted(manifest.items()):
        cached = cache / name
        if not cached.exists():
            misses += 1
            origin_requests += 1
            origin_bytes += fetch_from_hub(hub, cached, latency_seconds)
        else:
            actual_hash = hashlib.sha256(cached.read_bytes()).hexdigest()
            if actual_hash == expected_hash:
                hits += 1
                verified += 1
                continue
            integrity_failures += 1
            if repair_corrupt:
                origin_requests += 1
                origin_bytes += fetch_from_hub(hub, cached, latency_seconds)
                repaired_files += 1

        actual_hash = hashlib.sha256(cached.read_bytes()).hexdigest()
        if actual_hash == expected_hash:
            verified += 1

    elapsed = time.perf_counter() - started
    total_bytes = sum((cache / name).stat().st_size for name in manifest)
    return {
        "duration_ms": round(elapsed * 1000, 3),
        "throughput_mib_s": round((total_bytes / 1024 / 1024) / elapsed, 3),
        "cache_hits": hits,
        "cache_misses": misses,
        "cache_hit_rate": round(hits / len(manifest), 3),
        "origin_requests": origin_requests,
        "origin_bytes": origin_bytes,
        "verified_hashes": verified,
        "total_files": len(manifest),
        "integrity_failures": integrity_failures,
        "repaired_files": repaired_files,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path)
    parser.add_argument("--files", type=int, default=8)
    parser.add_argument("--file-size-kib", type=int, default=512)
    parser.add_argument("--wan-latency-ms", type=float, default=60.0)
    args = parser.parse_args()
    if args.files < 2 or args.file_size_kib < 1 or args.wan_latency_ms < 1:
        parser.error("files >= 2, file-size-kib >= 1, and wan-latency-ms >= 1 are required")

    workspace = Path(tempfile.mkdtemp(prefix="news-lab12-"))
    hub = workspace / "hub"
    cache = workspace / "spoke-cache"
    hub.mkdir()
    cache.mkdir()

    try:
        manifest = write_dataset(hub, args.files, args.file_size_kib * 1024)
        cold = read_epoch(hub, cache, manifest, args.wan_latency_ms / 1000)
        warm = read_epoch(hub, cache, manifest, args.wan_latency_ms / 1000)

        corrupt_path = cache / sorted(manifest)[0]
        original = corrupt_path.read_bytes()
        corrupt_path.write_bytes(b"corrupt" + original[7:])
        corrupted_hash = hashlib.sha256(corrupt_path.read_bytes()).hexdigest()
        integrity_failure_detected = corrupted_hash != manifest[corrupt_path.name]
        recovery = read_epoch(hub, cache, manifest, args.wan_latency_ms / 1000, repair_corrupt=True)
        post_recovery = read_epoch(hub, cache, manifest, args.wan_latency_ms / 1000)

        assertions = {
            "cold_epoch_fetches_every_file_from_hub": (
                cold["cache_misses"] == args.files
                and cold["cache_hits"] == 0
                and cold["origin_requests"] == args.files
            ),
            "warm_epoch_reads_every_file_from_cache": (
                warm["cache_hits"] == args.files
                and warm["cache_misses"] == 0
                and warm["origin_requests"] == 0
            ),
            "all_cold_and_warm_hashes_match": (
                cold["verified_hashes"] == args.files
                and warm["verified_hashes"] == args.files
            ),
            "warm_epoch_is_faster_than_cold_epoch": warm["duration_ms"] < cold["duration_ms"],
            "cache_corruption_is_detected": integrity_failure_detected,
            "corrupt_file_is_refetched_once": (
                recovery["integrity_failures"] == 1
                and recovery["repaired_files"] == 1
                and recovery["origin_requests"] == 1
                and recovery["verified_hashes"] == args.files
            ),
            "repaired_cache_returns_to_warm_state": (
                post_recovery["cache_hits"] == args.files
                and post_recovery["origin_requests"] == 0
                and post_recovery["integrity_failures"] == 0
                and post_recovery["verified_hashes"] == args.files
            ),
        }
        passed = all(assertions.values())

        result = {
            "tested_at": datetime.now(timezone.utc).isoformat(),
            "scope": "local-filesystem-hub-spoke-cache-emulation",
            "source": {
                "article": "https://aws.amazon.com/blogs/machine-learning/multi-region-training-with-amazon-sagemaker-hyperpod-and-qumulo/",
                "published": "2026-09-25",
            },
            "environment": {
                "runtime": "local Python filesystem experiment",
                "dataset_files": args.files,
                "file_size_kib": args.file_size_kib,
                "dataset_mib": round(args.files * args.file_size_kib / 1024, 3),
                "modeled_latency_ms_per_cold_fetch": args.wan_latency_ms,
            },
            "cold_epoch": cold,
            "warm_epoch": warm,
            "corruption_and_recovery": {
                "corrupted_file": corrupt_path.name,
                "integrity_failure_detected": integrity_failure_detected,
                "recovery_epoch": recovery,
                "post_recovery_epoch": post_recovery,
            },
            "assertions": assertions,
            "passed": passed,
            "not_validated": [
                "AWS Regions, VPC Peering, route tables, or security groups",
                "Qumulo Hub, Spoke, Cloud Data Fabric, or NVMe cache",
                "NFS TCP 2049 or SageMaker HyperPod",
                "Actual WAN latency, cache prefetch, GPU utilization, throughput, or cost",
                "Concurrent readers, partial writes, or origin outage during repair",
            ],
        }
        rendered = json.dumps(result, ensure_ascii=False, indent=2)
        if args.evidence:
            args.evidence.parent.mkdir(parents=True, exist_ok=True)
            args.evidence.write_text(rendered + "\n", encoding="utf-8")
        print(rendered)
        return 0 if passed else 1
    finally:
        shutil.rmtree(workspace)


if __name__ == "__main__":
    raise SystemExit(main())
