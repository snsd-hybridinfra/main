# Resource Cleanup Impact Classification Matrix

| Resource Category | Cleanup Signal | Dependency Risk | Cost Impact | Required Evidence | Approval Requirement | Final Judgment |
|---|---|---|---|---|---|---|
| Compute instance placeholder | idle/expired | placeholder | retired-numbered-case | owner/rollback | Required | CLEANUP_READY |
| Persistent volume placeholder | unattached | backup risk | retired-numbered-case | retention/recovery | Required | CLEANUP_REVIEW_REQUIRED |
| Public IP placeholder | unused | route risk | retired-numbered-case | owner/dependency | Required | CLEANUP_READY |
| Load balancer placeholder | unused | traffic risk | retired-numbered-case | dependency/rollback | Required | CLEANUP_REVIEW_REQUIRED |
| Object storage placeholder | empty | retention risk | retired-numbered-case | retention/recovery | Required | CLEANUP_REVIEW_REQUIRED |
| NAT gateway placeholder | idle | network risk | retired-numbered-case | dependency/rollback | Required | CLEANUP_REVIEW_REQUIRED |
| Managed database placeholder | idle | Critical | retired-numbered-case | retention/recovery | Required | CLEANUP_BLOCKED |
| Kubernetes namespace placeholder | expired | workload risk | placeholder | dependency/recovery | Required | CLEANUP_REVIEW_REQUIRED |
| Kubernetes workload placeholder | unused | service risk | placeholder | dependency/rollback | Required | CLEANUP_REVIEW_REQUIRED |
| Monitoring storage placeholder | expired | evidence risk | retired-numbered-case | retention/recovery | Required | CLEANUP_REVIEW_REQUIRED |
| Backup artifact placeholder | expired | restore risk | placeholder | retention/recovery | Required | CLEANUP_REVIEW_REQUIRED |
| Temporary lab resource placeholder | expired | Low | retired-numbered-case | owner/rollback | Required | CLEANUP_READY |

Critical dependency blocks cleanup; missing owner/retention requires review; cleanup is never automatic.
