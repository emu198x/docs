# SNES regional split verification

Steve approved v2 on 2026-11-01. Source PR #2221 implements the two fixed owners,
complete firmware envelopes, a strict loaded-v1 reader and blank-v1 rejection.
The former red blank-save regression is green. See verification.json and the
compressed logs for local results, controls, immutable fixture hashes and limits.

Source branch: refactor/snes-fixed-board-owners. Docs PR #169 and site PR #41
are the companion surfaces. Repository CI, merge receipts and live verification
are recorded separately after they finish. Do not infer merge or live status
from local checks. No historical-software or original-firmware qualification
was added; the available tests use project-written cartridges and IPL programs.

Primary checkouts and unrelated worktree records remain untouched. Task-only
worktrees and disposable caches are removed after remote retention is verified.
The umbrella primary checkout remains on model/spectrum-solidcraft.
