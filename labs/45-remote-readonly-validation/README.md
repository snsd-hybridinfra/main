# Lab 45: Bounded Remote Read-Only Validation & Evidence Pipeline

**Status:** `SOURCE_EXTRACTED / NOT_REVALIDATED`. All **33 source files** under `tools/live-validation/` were copied as reference-only scripts and examples, outside a root workflow or executable pipeline.

## Value
- Read-only EVE-NG, Cisco router and OpenStack validation command design
- Forced SSH commands, dedicated keys, constrained sudo, validator identity
- Telemetry capture, redaction, scheduled/continuous validation and evidence proofing
- Safe failure signals and rollback-approval gates before any host-side installation

## Important safety boundary
The source directory mixes **read-only diagnostic routines** with **remote installer, host configuration, persistence and scheduled validation** commands. The latter may modify SSHD, sudo, firewall, service units, files, VM configuration, or evidence storage. **Do not execute any referenced script on a host or workstation without separate source audit, identity verification, rollback and isolated target.** Renamed public samples are not proof of read-only behavior.

The source tools expect original repository paths, operators, alias/hostnames, SSH keys and installed packages. They are intentionally **not marked runnable** in this destination.
One known old management address prefix was converted to a documentation-only `192.0.2.0/24` example; this source copy is not byte-identical.

## Independent lab objective
Build a local fake-SSH/console target and test exactly allowed diagnostics, explicit rejection of arbitrary commands, untrusted host keys, token/log redaction, bounded output and evidence freshness. Use [Lab 33 EVE assurance](../33-eve-network-assurance/README.md) and [Lab 22 continuous verification](../22-continuous-verification/README.md) as reference interfaces only.

**Source:** `snsd-hybridinfra/snsd-multicloud-ops@fd5b2286a68da180fd51ecb247516c960cc7d4ef`. No remote or device commands were run.
