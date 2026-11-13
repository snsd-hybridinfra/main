# Security Rule Misconfiguration Criteria

| Misconfiguration Type | Evidence Source | Unsafe Pattern | Expected Safe Pattern | Operational Impact | Required Rollback | Related Baseline Scenario | Evidence Reference |
|---|---|---|---|---|---|---|---|
| SSH exposed to unrestricted source | rule sample | unrestricted source placeholder | SSH restricted to bastion or approved admin CIDR placeholder | public admin exposure | replace source | retired-numbered-case | rollback sample |
| Database port exposed to unrestricted source | rule sample | unrestricted source placeholder | DB port restricted to application subnet placeholder | public data path | replace source | retired-numbered-case-retired-numbered-case | rollback sample |
| Kubernetes API exposed to unrestricted source | policy sample | unrestricted source placeholder | Kubernetes API restricted to management CIDR placeholder | control-plane exposure | restrict source | retired-numbered-case | rollback sample |
| Internal service exposed publicly | rule sample | public source placeholder | Internal service not publicly exposed | internal API exposure | remove public rule | retired-numbered-case-retired-numbered-case | rollback sample |
| Azure NSG Any-to-Any allow rule | NSG sample | Any-to-Any placeholder | rejected unless explicitly approved placeholder | broad Azure exposure | remove exception | retired-numbered-case | rollback sample |
| OpenStack security group broad ingress rule | SG sample | broad ingress placeholder | approved source placeholder | broad private-cloud exposure | restrict ingress | retired-numbered-case | rollback sample |
| Kubernetes NetworkPolicy allow-all ingress placeholder | policy sample | allow-all placeholder | namespace/service selector placeholder | workload exposure | restore policy | retired-numbered-case | rollback sample |
| Egress any-any exception placeholder | rule sample | egress any-any placeholder | explicit approved destination placeholder | uncontrolled egress | remove exception | retired-numbered-case | rollback sample |
| Missing description / change reference | metadata | missing reference | owner, reason, expiry, approval, change reference placeholders | ungoverned change | complete metadata | retired-numbered-case | decision record |
| Missing rollback evidence | evidence | no rollback proof | every temporary exception has rollback evidence | unresolved risk | capture proof | retired-numbered-case | validation summary |
