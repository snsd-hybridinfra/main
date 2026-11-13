# ZT-AUTO-001 Rollback

Rollback is a repository and ignored-runtime cleanup operation only. Normal
implementation does not execute rollback, and no virtual machine, network,
identity, telemetry, workload, data, or system change was made by the package.

1. Confirm the target diff contains only ZT-AUTO-001 catalogs, policy,
   schemas, tools, wrapper, tests, documentation, telemetry-model additions,
   tracking records, and reviewed evidence.
2. Disable a package action by making it non-executable and removing workflow
   references before removing its fixed handler. Never replace it with a
   generic command path.
3. Remove package-owned action, workflow, integration, and approval catalogs
   together with their six schemas only after dependent records are removed.
4. Remove the Python tools, PowerShell wrapper, fixtures, and tests as one
   reviewed unit. Preserve all validators invoked by those tools.
5. Revert only the ZT-AUTO-001 telemetry event and source additions. Preserve
   endpoint, workload, data, system, visibility, and correlation definitions.
6. Keep committed execution evidence as historical truth unless an explicit
   evidence-governance decision marks it superseded; never rewrite a past
   execution as successful.
7. Runtime proposals, plans, locks, and execution records may be deleted only
   after their exact ignored path is reviewed. Incomplete and failed records
   are retained by default for diagnosis.
8. Re-run repository, taxonomy sync, report, package, secret, scenario-lock,
   and Git-diff validation after rollback.

There is no optional CI rollback because no workflow was added. Rollback must
preserve OpenStack, EVE-NG, the router, identity services, telemetry services,
endpoint tooling, application workloads, data assets, system baselines,
operator access, and all predecessor-package evidence. It must not restart,
reconfigure, isolate, delete, rotate, or restore any live target.
