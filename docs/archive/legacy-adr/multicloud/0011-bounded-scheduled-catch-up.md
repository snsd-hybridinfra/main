# ADR: Bounded Scheduled Catch-Up

- Status: Accepted for the bounded laboratory
- Date: 2026-08-11
- Scope: ZT-SCH-001 scheduler availability remediation

## Context

The daily ZT-SCH-001 task used a limited interactive token without stored
credentials and disabled `StartWhenAvailable`. Six scheduled candidates from
2026-08-03 through 2026-08-08 failed because the fixed OpenStack SSH target was
unavailable. Later daily triggers produced no candidate when the interactive
session was unavailable at 09:00; Windows recorded refused execution requests.
The package therefore needed a recoverable availability path without expanding
the task to SYSTEM, S4U, stored credentials, or infrastructure mutation.

Microsoft documents `StartWhenAvailable` as allowing a timed task to be queued
after its scheduled time, normally with a delayed start. The authoritative
reference is the [TaskSettings.StartWhenAvailable property](https://learn.microsoft.com/en-us/windows/win32/taskschd/tasksettings-startwhenavailable).

## Decision

Enable `StartWhenAvailable` for the existing daily 09:00 task while retaining
the current-user limited interactive token and zero stored credentials. The
runner independently permits execution only from 09:00 through 11:00 local
time. It writes no attempt marker outside that window. The exclusive lock,
one-attempt-per-local-date rule, zero restart count, and no automatic retry,
remediation, infrastructure mutation, repository mutation, history append,
maturity update, or phase completion remain unchanged.

Scheduled-runtime recovery is evaluated against the latest three due scheduled
dates. Historical failures and misses remain reported, but do not make EC5
permanently unreachable after three new consecutive, correlated, sanitized
successes. Every successful candidate still requires explicit correlation and
review before acceptance.

## Evidence and Runtime Boundary

Updating the task definition is configuration evidence only. It does not run
the live validator, create a successful scheduled execution, establish EC5,
assign maturity, or complete Phase 1. Runtime output remains ignored and must
be sanitized.

## Rollback

Disable or uninstall the task using the existing explicit approval paths, or
perform a separately reviewed definition update that restores
`StartWhenAvailable=false`. Preserve all ignored runtime evidence and Git
history.

## Rejected Alternatives

SYSTEM execution, S4U, stored passwords, wake-to-run, unrestricted late
execution, automatic retry, and automatic infrastructure startup were rejected
because they expand privilege, authentication, physical-system, or retry scope.
