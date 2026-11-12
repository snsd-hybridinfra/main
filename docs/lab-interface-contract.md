# Lab Integration Contract v1

**Scope:** `labs/role-groups/` (7 groups) · **Status:** design only

The existing `labs/NN-...` directories remain canonical. A role group is a **shared operations contract**, not a claim that all members are already runnable or integrated.

## Required per-lab fields
- `lab_id`: fixed ID and immutable canonical repository path
- `role_group`: exactly one primary group from [manifest](../labs/role-groups/manifest.json); secondary links may exist but do not own the code
- `source_commit`: upstream repository/SHA and modification/redaction record
- `execution_mode`: `REFERENCE_ONLY`, `OFFLINE_SAFE`, `DISPOSABLE_VM`, `EXTERNAL_LAB_APPROVED`. Default is `REFERENCE_ONLY` for imported labs.
- `inputs`: synthetic input fixtures, schema, secrets boundary and permitted IP/DNS scope
- `outputs`: versioned evidence schemas with deterministic filenames and declared test meaning
- `dependency_contract`: upstream roles, versions, network ports and interface promises
- `validation_gates`: normal, denied, failure, rollback/recovery, idempotency and security/privacy
- `evidence`: timestamp, command/check, exact runtime location, synthetic-vs-real flag, source hash, sensitivity scan and limitations
- `status`: `SOURCE_EXTRACTED` → `LOCAL_VALIDATED` → `GROUP_INTEGRATION_VALIDATED` (never promote based solely on imported artifacts)

## Execution/privilege boundary
A read-only collector must not share write credentials with deployment, repair or restore actions. Destructive actions require isolated targets, explicit authorization, reviewed target identifiers and verified rollback. A prior project's approval or test results are not inherited by a newly composed lab.

## Group-level integration acceptance
1. Validate every participating lab's own synthetic or isolated reproducibility.
2. Use immutable fixtures and normalized input/output schemas; confirm policies and error semantics.
3. Execute group normal/deny/failure/recovery as **new tests**, not a union of historical screenshots.
4. Record dependency versions, portability constraints, RTO/RPO or timing only when measured.
5. Publish a separate report that distinguishes `PASS`, `FAIL`, `BLOCKED`, `SKIPPED`.
6. Only then consider moving a shared implementation into the role-group directory and retiring redundant copies after link checks.

## Link preservation
Do not bulk-move `labs/01-51/` while they carry historical citations/evidence. The role indexes reference canonical files. Any later physical move needs a file-move plan, link rewrite, CI test, git mv semantics and preserved provenance.
