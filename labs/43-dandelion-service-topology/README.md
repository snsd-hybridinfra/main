# Lab 43: OpenStack Service Topology & HA Boundaries

**State: `REFERENCE_EXTRACTED / NOT_REVALIDATED`.** Team Dandelion design and a small WordPress example image are retained as source material. Historical status markers and phase plans are not proof of live availability or failover.

## Independent lab targets
- Map Client → HAProxy → Web/WordPress → MariaDB, plus Control/Ansible, Monitoring and Backup/Restic boundaries.
- Describe security-group ingress/egress allow and deny paths; verify isolated OpenStack fake-node routes before services.
- Build synthetic WordPress container using `reference/docker/wordpress/` after updating image digest and reducing container privileges.
- Run HA/DR experiments for proxy outage, Web replica failure, database writer/replica conditions, and backup-node isolation.

## Included
`reference/docs/` holds source architecture, network design, Ansible execution/provisioning design and validation plan. `reference/docker/wordpress/` includes the Dockerfile and PHP config.
Some source Markdown references images that were **not migrated**; images, screenshots and PowerPoint may contain private node identifiers or team contributions.

## Limitations
No independent HAProxy configuration file was present in the source repository. The documents describe a target HAProxy/MariaDB/Monitoring layout, **not a complete importable HA stack**. The original Ansible orchestration was selectively extracted in [Lab 16](../16-openstack-ansible-operations/README.md).
Network samples were generalized and may require additional adjustments before parsing. No cloud credentials, real asset addresses or automated infrastructure changes are intended.

## Attribution
Team Dandelion source: `snsd-hybridinfra/dandelion-cloud-automation@22a21c02973e696a9a07c91da3bc2ea033881ea6`. Keep the team's distinct contributions and original commit history.
