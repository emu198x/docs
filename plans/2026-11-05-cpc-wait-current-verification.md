# Verify the retained CPC WAIT diagnosis against current main

Engineering-frontier work for #2284. The requested bounded diagnosis already
exists in source PR #2296 and the 2026-11-04 evidence. Verify it rather than
create a competing implementation. The approved v6 policy is recorded in
`2026-11-04-cpc-wait-qualification.md` and the PR decision. Earlier authorisation
to merge completed work remains applicable after verification.

1. Reproduce the CPU 0.8 baseline on current main (`79b5fc12e`) using
   `crates/runtime-amstrad-cpc/src/board_baseline_tests.rs`. Hash the original
   v4/v5 specimens before any experiment.
2. In `/private/tmp/198x-cpc-first-clock`, instrument an isolated copy of
   `crates/common-amstrad-cpc/src/lib.rs` around its existing CPU tick. Record
   at most 100 half-cycles with the project-written synthetic firmware.
   Compare CPU 0.8 and published 0.9 without changing any machine clock/phase.
   Retain the observer patch and bounded structured results in this docs repo.
3. Verify the first sequencer difference and first physical signal difference
   against yesterday's `first-io-edges.json`, the two published CPU sources,
   the held CPC firmware guide, and vendored Arnold/Caprice32/MAME. Distinguish
   observed CPU differences from physical-hardware qualification limits.
4. Remove diagnostic instrumentation. Apply the existing PR to current main
   in the task worktree and run frozen-file/CPU-graph verification, CPC common/
   runtime/board and headless-runner tests, Clippy and formatting. Original
   specimen bytes remain unchanged. Review the existing save-policy change.
5. With verified integration and green required PR checks, merge the existing
   checked head by normal rebase policy. Confirm the resulting tree matches
   the locally verified integration, follow required CI, and record results.
6. Push the evidence and remove task worktree, build cache and bounded logs
   after verifying commit retention. Preserve all unrelated work.

Task-owned temporary paths: `/private/tmp/198x-cpc-first-clock`,
`/private/tmp/198x-cpc-first-clock-target`, and
`/private/tmp/198x-cpc-first-clock-evidence`. No user firmware is published.
