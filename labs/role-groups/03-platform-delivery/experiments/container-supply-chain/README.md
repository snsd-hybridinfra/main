# Lab 25: Container Build Supply Chain & Restricted Runner

**Status: `MIGRATED / NOT_REVALIDATED`**. This lab is a self-contained **source reference collection**, not a working GitHub Actions or registry pipeline.

## Reusable concerns
- `source/container_pipeline.py`: build pipeline orchestration / integrity checks, **requires an explicit sandbox review before execution**
- `source/runner-bundle/`: installation and egress control templates, **DO NOT EXECUTE ON THE HOST** without a disposable VM, backup and a review of firewall/system-wide changes
- `source/*lock.json`: content/digest lock references from the original setup
- `reference/`: original GitHub workflow, validator and test source, stored **outside `.github/workflows/` so no CI/CD job is activated by import**

## Validation goals
1. Rebuild a small test image, produce an SBOM, perform dependency/vulnerability checks, verify manifest/digest and signature policy where supported.
2. Document a reproducible failure for an untrusted image/digest or policy mismatch.
3. If trialing a restricted runner, isolate it in a disposable VM with *no production network*, no company tokens, no kubeconfig, and no registry publish permissions.
4. Keep screenshots/outputs synthetic or redacted. Never claim an untouched reference pipeline is production-ready.

**Source:** `snsd-hybridinfra/snsd-multicloud-ops` at `fd5b2286a68da180fd51ecb247516c960cc7d4ef`. Original portal, service registry and runner image assumptions are not automatically available.
