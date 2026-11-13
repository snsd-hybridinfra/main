# Lab 47: Repository Quality Gates & Change Documentation

**Status:** `REFERENCE_EXTRACTED / NOT_REVALIDATED`. Team Dandelion repository validation scripts, review checklists and a GitHub Actions **reference document** were extracted.

## Reusable pieces
- `reference/tools/validate_repository.py`: source-specific inventory and file hygiene checks
- `reference/tools/update_doc_images.py`: document image/reference mutation helper; treat as **not safe to run unchanged**
- `reference/.github/workflows/project-automation.yml.reference.txt`: original CI workflow as inert text, not activated in `main/.github/workflows/`
- `reference/docs/`: review, pre-run, validation planning and source scope controls

## Why inert?
The original CI requests `contents: write` and can automatically commit/push generated documents. It is not appropriate for a new labs-first repository without scoping and least-privilege review.
Some scripts assume the exact original team repository layout, images and owners, so copying them does not establish a passing CI gate.

## Next
1. Reimplement repository-neutral checks that validate READMEs, source provenance, relative links, missing fixture imports and intentionally excluded secrets.
2. Run only in a temporary fixture repo; record expected failures and true positives separately.
3. Add minimal read-only CI permissions after testing. Publishing, auto-commit and remote writes should remain disabled until independently approved.

**Source:** `snsd-hybridinfra/dandelion-cloud-automation@22a21c02973e696a9a07c91da3bc2ea033881ea6`. Respect team authorship and preserve original revision history.
