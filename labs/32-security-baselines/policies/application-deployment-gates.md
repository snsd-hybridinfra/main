# ZT-APP-001 deployment gates

| Gate | Owner | Pass criteria | Current pilot result | Evidence |
|---|---|---|---|---|
| APP-GATE-0 Inventory Ready | Repository maintainer | Owner, criticality, source, workload, and deployment method are present | PASS | Application and workload inventories |
| APP-GATE-1 Source Validation | Repository maintainer | Repository validation, secret scan, syntax, and dependency definition pass | PASS | Built-in scan and Compose parse |
| APP-GATE-2 Artifact Validation | Software risk owner | Valid SBOM, vulnerability assessment, immutable digest, and provenance state | PARTIAL | Direct-image SBOM only; scanner, digest, and signature gaps open |
| APP-GATE-3 Deployment Readiness | Lab platform operator | Privilege, secrets, exposure, resources, health, and rollback are reviewed | PASS_WITH_EXCEPTION | Alloy UID 0 exception bounded by dropped capabilities and read-only root |
| APP-GATE-4 Runtime Acceptance | Lab platform operator | Existing workload healthy, expected path passes, unsafe path is not accepted, logs observable, evidence sanitized | PENDING_LIVE_RECHECK | No restart or deployment permitted |
| APP-GATE-5 Continuous Review | Package approver | Repeatable dependency, image, drift, inventory, and exception review | NOT_IMPLEMENTED | Requires later CV/RV/SCH packages |

Any missing required evidence fails the corresponding gate. Waivers require an
owner, expiry, rationale, compensating control, and package approver. A design
or configuration result cannot satisfy APP-GATE-4, and a checksum is not a
signature.
