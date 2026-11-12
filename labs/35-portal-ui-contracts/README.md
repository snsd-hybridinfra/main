# Lab 35: Self-Service / Admin Portal UI Contracts

**State:** `SOURCE_EXTRACTED / NOT_REVALIDATED`. This lab preserves the main internal user/admin portal shells (10 files), not a deployed UI.

## Experiment
Design user-facing request and administrator approval screens with distinct authentication contexts and contract checks. Stub all network calls; never use the source auth configuration as proof of security.

## Included
- `source/admin-portal/`: admin screen (login, approval, grants, monitoring), static assets and Nginx examples
- `source/user-portal/`: standalone user portal shell and assets

## Deliberately not duplicated
The original source also includes `user-portal/eclipse/`, marked in `eclipse/upstream-source.json` as imported from a **separate team project** `Project-Team-Eclipse/ecl2-portal`. Until reuse/redistribution rights are verified, this lab includes a provenance pointer rather than republishing that team's detailed UI source or image assets. Do not present their work as an individual contribution.

Upstream provenance (as recorded in the source): `Project-Team-Eclipse/ecl2-portal` commit `e8c4c1d26b9177929a0e04b7b9db1d6885ac5215`.

## Revalidation
1. Test static front-end code parsing with mock request/approval APIs from Labs 27 and 28.
2. Assert that production mode cannot activate demo identities or mock approval successes.
3. Evaluate session expiry, role boundaries, CSRF protections and status/error handling.
4. Run on loopback only in a disposable local environment. No real Keycloak, Pomerium, customer users or live backend endpoints.

**Source:** `snsd-hybridinfra/snsd-multicloud-ops` commit `fd5b2286a68da180fd51ecb247516c960cc7d4ef`.
