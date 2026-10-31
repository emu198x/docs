# Atari ST fixed configuration owners

Continue the approved #2144 programme in the engineering-frontier lane. The
existing four profiles become fixed `machine-atari-520st-pal`,
`machine-atari-520st-ntsc`, `machine-atari-1040st-pal` and
`machine-atari-1040st-ntsc` owners over `common-atari-st`. Retain the family
runtime, runner, profile IDs, TOS firmware identity and host-supplied firmware
contract. Colour/monochrome monitors stay peripherals. These names identify
the implemented bank/clock configurations; they do not qualify every ST,
STF, STFM motherboard revision, drive, modulator or PSU arrangement.

1. Confirm the existing model/bank and PAL/NTSC identities against the local
   Atari reference library and scanned schematics. Follow the binding
   `each-machine-has-its-own-machine-crate.md` distinction between board
   wiring and same-board RAM fitting. The three donor archives named in
   RULES.md are absent. Obtain and register Hatari before any chip/timing
   correction; no algorithms change as part of a mechanical extraction.
2. Add `runtime-atari-st/src/board_baseline_tests.rs`. Freeze complete original
   v1 states and three continued native frames, sample bits, clock deltas and
   final states for all four profiles, colour and monochrome, using
   project-written synthetic TOS, active video/sound/inputs and mounted
   modified disks. Compare direct and restored execution at partial fields;
   deliberately corrupt a fixture to prove failure. Exercise reset, monitor
   changes, wrong hardware under a matching header and missing firmware.
   Reproduce fidelity bugs before fixing them; ask before a schema change.
3. Move raw `machine-atari-st` wiring and its regressions to `common-atari-st`.
   Add fixed generic board binding with checked model, master clock, physical
   RAM banks and framebuffer geometry. Keep firmware external and preserve
   original v1 bytes if the baseline permits it. Expose named CPU/chip and
   register operations without replaceable whole-engine access. Add seven or
   more exclusive direct tests per owner. Add closed dispatch in
   `runtime-atari-st/src/machine.rs`, following CPC/NES/Mega Drive, and adapt
   input, debug, pointer, queries, snapshots and runner imports. Write the
   narrow runtime-shape override in `knowledge/decisions/`.
4. Give each owner its registry/evidence root, regenerate status, and run
   common/owner/runtime/runner/fleet tests, strict Clippy/rustdoc and
   registry/fixture/ignore/status guards. Retain unverified hardware limits.
   Check available original/free TOS through the fixed owners; record exact
   identities and output. No new registry dependencies.
5. Update current docs and public system routes. Map only exact variants
   present in the pinned browser player; retain the old family URL as a
   default-profile redirect. Preserve existing capture ownership and create
   model-specific evidence where it actually runs. Check site tests, build,
   accessibility and live route/player/image results. Merge only green exact
   heads, inspect CI ownership counts, update #2144 and retain receipts.
6. Verify every task commit remotely, inspect tracked/untracked/ignored files
   and process ownership, then remove all task worktrees, build caches,
   experiments and helpers. Preserve the primary checkouts and unrelated
   locked worktree records.

Old failure modes: header/payload board mismatch; wrong physical bank layout;
first resumed frame/audio/clock drift; lost disks or write protection through
reset or monitor replacement; stale host TOS or monitor state; held control
changes; shared evidence misattributed to a board; browser fallback to another
profile. A firmware-less v1 state remains unable to restore into a blank
runtime; TOS content identity is not encoded in that existing format.
