# Investigate controls encountered during M.U.L.E. study captures

Lane: engineering-frontier validation. No chip or timing changes are planned.

1. Reproduce C64 keyboard input without game media using the shared script runner. Capture decoded screen text and a screenshot, with press/release input and idle controls.
2. Compare manual input events with the shared typing verb and inspect their route through the C64 runtime. Identify workflow mistakes before changing the emulator.
3. Keep Atari setup input acceptance separate from the later failure to reach play. Inspect existing reports; record a narrowly scoped issue if the failure remains reproducible.
4. Preserve sanitized scripts, exact source revision, observations and uncertainty. Exclude firmware and commercial game bytes.
5. Run applicable checks for any justified fix; otherwise publish an investigation record and linked issue. Remove task builds and worktrees after retaining commits remotely.

Files: this plan; a companion evidence record under `plans/2026-10-18-mule-control-investigation/`. Source changes require a demonstrated failure and separate exact file list.

## Demonstrated C64 import discrepancy

Direct import leaves $AE/$AF zero. The M.U.L.E. PRG unpacker reads that pair; VICE 3.10's `c64memsc.c::mem_set_basic_text` sets it to the exclusive payload end. Compare normal disk loading and then correct the import context in `crates/format-commodore-c64-prg/src/lib.rs`, preserving the existing BASIC relink behavior. Add tests where the payload end differs from the BASIC stub end, plus a wrapping boundary case. Verify red before fix, green after; run package Clippy and rebuild the runner to repeat the actual game launch.
