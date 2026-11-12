# Database recovery boundary

The portal retains separate request, control, and identity databases. Backups
use the checked-in restic scripts and external runtime credentials. Recovery is
operator-directed: stop writes, preserve the original, restore into isolation,
validate schema and permissions, rotate affected credentials, verify service
readiness, then approve traffic transfer.

No endpoint switch or credential rotation is automatic. The current scripts
and static tests do not establish a live backup, successful restore, RPO/RTO, or
Phase 1 recovery acceptance.
