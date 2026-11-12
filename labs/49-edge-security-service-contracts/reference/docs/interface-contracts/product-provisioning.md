# Product provisioning contract

The provider-bound execution-profile catalog is `terraform/catalog.json`. Its
five fixed profiles are `DEV-OS-VM-S/M/L` and `DEV-OS-K3S-S/M`. The
user-facing authority is the repository-level
`docs/platform/composite-service-catalog.yaml`: requesters select one approved
composite blueprint and bounded inputs. The current local API still exposes an
execution profile only through a service-authorized internal endpoint. The
public API and portal expose approved blueprints. `VM_APPLICATION_STACK`
persists its immutable manifest and carries it through approval to independent
runner verification; blueprints with an unimplemented component are rejected.
The legacy direct-profile request route is disabled by default and exists only
for explicit local compatibility tests.

Until that resolver exists, requesters supply only a lowercase project name,
an approved purpose, one internal execution profile, and one allowed duration.

CPU, memory, storage minimum, provider module, image, flavor, network, security
groups, key pair, and artifact digest are server-owned. Attempts to supply
unsupported parameters or a mismatched fixed runtime specification are denied.

The lifecycle uses three independent but correlated state machines:

```text
Request/Grant: PENDING -> APPROVED -> GRANTED -> REVOKED or EXPIRED
                       \-> REJECTED
                       \-> CANCELLED

Resource:      PROVISIONING -> RUNNING -> TERMINATING -> TERMINATED
                    |             |              \-> TERMINATION_FAILED -> TERMINATING
                    \-> PROVISION_FAILED -> PROVISIONING or TERMINATING

Runner job:    QUEUED -> PLANNING -> APPLYING -> SUCCEEDED
                    \-> explicit failure -> reviewed retry or destroy
```

Resource callbacks update the resource projection and `resource_status`; they
do not impersonate request or Grant transitions. The request remains
`APPROVED` until successful post-apply validation causes the Grant service to
issue a Grant and project `GRANTED`.

Grant issuance requires both successful apply and post-apply validation. k3s
then runs the approved Ansible configuration and requires
`bootstrap_status=READY`. Configuration failure automatically queues immediate
Terraform destroy inside the runner; rollback failure remains explicit. Revoke
or expiry blocks the Grant before queuing ordinary destroy. Failure states do
not issue a Grant.

Ordinary destroy and automatic rollback require a post-destroy Terraform state
read with no resources in the root or nested modules. Residual resources,
invalid state or an unavailable state read keep failure explicit:
`TERMINATION_FAILED / DESTROY_FAILED` for ordinary destroy and
`PROVISION_FAILED / ROLLBACK_FAILED` for automatic rollback. The runner cleans
its temporary workspace but retains the external state for reviewed recovery.
Local fake-command tests do not establish OpenStack resource-absence evidence.

Runner job identity, approved request/product/version inputs and all ownership
tags must agree. The state key is fixed to the same request; only `APPLY` and
`DESTROY` are executable. Absolute work and state roots must be disjoint and
outside Git, with credentials and SSH trust/key material outside the work
root. Path redirection and existing workspaces fail closed before commands or
file writes. Rejected jobs cannot clean another invocation's workspace. A
previous workspace remains an operator recovery item; only the current run's
exclusively created workspace is cleaned automatically.
