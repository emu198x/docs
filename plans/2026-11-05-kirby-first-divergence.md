# Trace the Kirby title-sequence disagreement (#2182)

Engineering-frontier qualification. Agreed scope: reproduce current main and
find the first divergent event before proposing a hardware behaviour change.

1. Verify the original game, boot ROM and pinned SameBoy source identities.
   Reuse `docs/plans/2026-10-28-game-boy-commercial-screens/{emu_probe.rs,sameboy_probe.c}`
   in an isolated source worktree. Compare all three checkpoints and retain
   hashes/counts, never game or boot bytes.
2. Extend the diagnostic probes to compare consecutive real LCD fields and
   bounded machine observations. Separate framebuffer differences from CPU,
   memory or timing differences. Keep all observers out of shipping code.
3. Trace the earliest relevant divergence through the existing Game Boy common
   machine, PPU/CPU crates and pinned SameBoy implementation. Consult primary
   references and existing decisions before drawing hardware conclusions.
4. Retain reproducible observers, source identities and results under
   `plans/2026-11-05-kirby-first-divergence/`. Verify the comparison can fail
   with a deliberate negative control. Record limits and the proposed next
   action; agree any behaviour change separately.
5. Commit and push the evidence. Inspect and safely remove the task worktree,
   build caches, extracted local fixtures and task-owned processes.

Task-owned paths: `/private/tmp/198x-kirby-first-divergence` (source worktree),
`/private/tmp/198x-kirby-build`, `/private/tmp/198x-kirby-evidence` (bounded
outputs and local-only extracted inputs). Preserve unrelated worktrees,
`tools/__pycache__/` and the existing ZIP compatibility draft.

## Diagnosis

All nine original game/checkpoint hashes reproduce on current main. The first
post-boot game-visible divergence is the LY read at `$0150`: Emu198x returns
153 (internal line 153, dot 424), SameBoy returns zero. The fourth instruction
boundary already differs in A; the sixth fetch takes a different branch.
A diagnostic CPU-read override, enabled only after BOOT unmaps and late in
internal line 153, makes all three Kirby checkpoints match the unchanged
reference exactly. It does not move the oscillator, scanline or frame clock.

Retained 720 consecutive field comparisons, source/fixture identities,
observers, exact counterfactual hashes and three failing evidence controls in
`2026-11-05-kirby-first-divergence/`. A fresh capture rebuild reproduces the
report exactly. Passive observers preserve the baseline checkpoints. Ruff and
`git diff --check` pass. No production change or exact early reset edge is
qualified here; LYC/STAT effects require separate evidence and design agreement.

After removing every diagnostic edit, both explicitly enabled existing
commercial screenshot/replay tests pass: 2 passed, 0 failed, 0 ignored.
The source worktree has no tracked, untracked or ignored changes. Its base
commit remains the actual main HEAD. All diagnostic changes are retained as
an observer patch and example in the docs evidence, not in shipping source.

## Cleanup

Evidence commit `33593eb` is pushed and verified on `origin/main`. The source
worktree was inspected for tracked, untracked and ignored files (none), with
its base commit retained on main. Removed it through `git worktree remove`
and deleted its empty task branch. Verified no task-owned probe/build process
remained, then removed the build cache and local-only capture/input directory.
All three declared task paths are absent. Unrelated worktrees and local files
are preserved. #2182 remains open pending a qualified production fix.
