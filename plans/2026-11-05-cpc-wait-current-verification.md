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

## Verified diagnosis

Current main reproduces the original v5 baseline with CPU 0.8; changing only
the two CPC CPU requirements/edges to 0.9 fails with
`amstrad-cpc464: full v5 state`. Retained fresh after-tick traces confirm
internal divergence at edge 2 and IORQ/WR release at 81 versus 87 on all
three models. All machine clocks and WAIT/IRQ inputs agree for all 600 edges.
The new bounded trace, observer, source checks and failing controls are in
[`2026-11-05-cpc-first-clock/`](2026-11-05-cpc-first-clock/README.md).

The existing PR applies cleanly to current main. Integration commit
`06be84c7fc7ea704b9ef2ee9e0503f90ae64bdd3` has tree
`2e46a049d10aaf8e31e92f3e39c99163e44cbd59`. All eighteen frozen-file
hashes and the CPU graph pass the existing public verifier. Fresh 104
common/runtime/board tests, 14 headless-runner tests, Clippy and formatting
pass. The PR remains at checked head `322c672fbd7765aa91c4b4271849795a803ae3bc`;
all hosted checks passed and GitHub reports it mergeable/CLEAN.

## Merge and cleanup

PR #2296 merged at 11:36:18 UTC as
`9d9f756a681c9a04a64f44fbd18ad05f52e82895`; #2284 closed automatically.
The merged tree exactly equals the verified integration tree above. The
public specimen/CPU-graph verifier also passes on the actual merged checkout.
[Post-merge CI run 42020321431](https://github.com/emu198x/emu198x/actions/runs/42020321431)
completed successfully on that exact merged commit, including all four test
shards and the final Test check. No failed jobs remain.

All three task-owned temporary paths are removed and verified absent. Before
removing the linked worktree, inspected tracked/untracked/ignored files (none),
rechecked all twelve old specimen hashes and confirmed its integration commit
is retained by `verify/cpc-wait-current` in the main repository. No build/test
process remains. The bounded trace, observer and controls are committed in
the docs repo. Source `tools/__pycache__/`, the unrelated ZIP draft, and the
other locked worktrees are preserved.
