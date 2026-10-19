# Investigate native Amiga Save after a disk swap (#1877)

Lane: Amiga best-in-class campaign. Preserve the active learner game.

## Scope and decision gate

Investigate before choosing a fix, as requested. No runtime behavior changes
until the evidence and proposed approach have been reviewed.

1. Reproduce using the retained private Save requester snapshot in an isolated
   output directory. Record drive/CIA state immediately before and after
   `load_media`, then after guest execution. Verify both source ADFs unchanged.
2. Trace `runtime-commodore-amiga/src/runtime.rs`, variant mount functions,
   `peripheral-commodore-amiga-floppy/src/lib.rs`, and native export. Compare
   disk-change behavior with vendored WinUAE and existing references/archives.
3. Separate disk-change notification from write/export correctness: compare
   byte-identical exports without guest writes, and an explicit eject/run/insert
   diagnostic. Validate actual exported filesystem contents, not tool success.
4. Report demonstrated causes, remaining uncertainty and a bounded fix design
   for approval. Then add regression tests that fail before the approved fix.
5. After approval, implement in the owning source crate, run focused tests,
   formatting and Clippy. Validate native Save, valid exported program, cold
   boot, native Load and game execution; preserve licensed media privately.
6. Push verified commits and PRs, update #1877 and curriculum evidence. Remove
   task worktrees and build outputs only after remote proof; retain any needed
   private repro with its removal condition.

## Resources

Source worktree: `/private/tmp/198x-amiga-disk-change`.
Docs worktree: `/private/tmp/198x-amiga-disk-docs`.
Private evidence: `output/bank-or-risk-playtest/save-repro-1877/` at umbrella.
Reuse the previous task build cache while investigating, then remove it.
No dependencies, architectural changes or public licensed fixtures planned.

## Investigation result

The [retained evidence](2026-10-19-amiga-native-save-investigation/README.md)
is complete. Native Save, cold boot, native Load, syntax check, run, roll and
bank work through the existing explicit-notification route. The generic
route remains defective. Implementation is deferred at the user’s request
to investigate further before choosing a change. No emulator source changed.
