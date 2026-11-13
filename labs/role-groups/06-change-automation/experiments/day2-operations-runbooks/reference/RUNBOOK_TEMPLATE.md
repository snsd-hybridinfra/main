# Runbook Template

Every authoritative runbook starts with one JSON-compatible metadata block.

```json runbook-metadata
{
  "runbook_id": "RB-<phase>-<number>",
  "title": "<required>",
  "phase": "<required>",
  "related_packages": ["<package or governance action>"],
  "owner_domain": "<required>",
  "supported_target_types": ["REPOSITORY_LOCAL"],
  "procedure_status": "DESIGN_SPECIFICATION",
  "validation_status": "NOT_VALIDATED",
  "runtime_required": false,
  "live_execution_permitted": false,
  "required_authority": "<required>",
  "evidence_authority": "NONE",
  "last_reviewed": "YYYY-MM-DD",
  "limitations": ["<required>"]
}
```

Allowed procedure statuses are `DESIGN_SPECIFICATION`, `IMPLEMENTED`,
`PARTIALLY_IMPLEMENTED`, and `NOT_IMPLEMENTED`. Allowed validation statuses
are `NOT_VALIDATED`, `VALIDATED_LOCAL`, `PARTIALLY_RUNTIME_VALIDATED`,
`VALIDATED_RUNTIME`, and `BLOCKED`.

Each exact command must be inside a JSON command metadata block. Use `commands`
only when every listed command has the same classification.

```json command-metadata
{
  "command": "<exact command or unavailable contract>",
  "command_status": "PLANNED_NOT_IMPLEMENTED",
  "execution_owner": "<USER|CODEX_OR_AUTOMATION|OPERATOR>",
  "approval_required": true,
  "runtime_target": "<REPOSITORY_LOCAL|NON_PRODUCTION_LAB|NONE>",
  "expected_effect": "<required>",
  "evidence_output": "<required>",
  "rollback_reference": "<required>",
  "executable": false
}
```

Allowed command statuses are `AVAILABLE_READ_ONLY`,
`AVAILABLE_MUTATING_APPROVAL_REQUIRED`, `PLANNED_NOT_IMPLEMENTED`,
`LIVE_RUNTIME_REQUIRED`, `PHYSICAL_USER_ACTION`, and
`PROHIBITED_IN_CURRENT_PHASE`.

## Purpose

<required>

## Scope

<required>

## Related Phase

<required>

## Related Package or Governance Action

<required>

## Supported Target Types

<required>

## Current Procedure Status

<required>

## Current Validation Status

<required>

## Evidence Authority

<required>

## Required Authority

<required>

## User-Performed Physical or Approval Steps

<required>

## Codex or Automation-Managed Steps

<required>

## Prerequisites

<required>

## Inputs

<required>

## Secret Inputs

<required>

## Service Impact

<required>

## Security Impact

<required>

## Preflight Checks

<required>

## Procedure

<required>

## Expected Output

<required; describe expected structure without inventing a result>

## Validation

<required>

## Pass Criteria

<required>

## Stop Conditions

<required>

## Failure Handling

<required>

## Rollback

<required>

## Evidence

<required>

## Escalation

<required>

## Known Limitations

<required>

## Related Architecture

<required>

## Related Runbooks

<required>
