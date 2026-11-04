# Dizzy 128K loading investigation

Lane: Spectrum launch-hardening. Investigate emu198x/emu198x#1924.

1. Identify the unmodified TOSEC TZX, English 128K ROM pair, current source
   revision and reference build. Record hashes and bounded reproduction commands
   in `plans/2026-11-04-dizzy-128k-loading/` without committing ROMs or media.
2. Run the shared `crates/emu198x-spectrum` headless runner with the reported
   128K menu Tape Loader path and a 48K control. Capture terminal CPU/tape state
   and screens; require positive title-screen evidence for successful loading.
3. Run the same inputs through Fuse, distinguishing real tape playback from
   fast loading and the 128K menu loader from 48K BASIC. Consult vendored Fuse
   source before changing hardware behaviour.
4. Locate the first meaningful divergence. Make a narrowly explained fix only
   if emulator behaviour is demonstrated wrong; otherwise record the exact
   compatibility or evidence limitation. Select exact implementation files
   after reproduction identifies the owner.
5. Add a regression for the demonstrated invariant, prove it fails before the
   fix, and run affected tests, formatting and Clippy. Repeat the original game
   reproduction and preserve the 48K control.
6. Commit and push task changes in their owning repositories, preserving
   unrelated work. Remove task-owned temporary builds/processes after retaining
   durable evidence.

## Result

The exact Tape Loader failure reproduces in Fuse with tape traps, fastload,
loader detection and loader acceleration disabled. Both engines retain the
same damaged bootstrap at `$5B00`: this image overwrites the 128 BASIC RAM
paging routines and then executes its clearing loop with the wrong entry state.

Selecting 48 BASIC on the same 128K, waiting for its reset and typing `LOAD ""`
reaches the title. The entire 6,912-byte screen agrees with Emu198x's 48K run
and Fuse's 128K/48 BASIC run. K starts the game and reaches the first room.
Sinclair's original manual prescribes 48 BASIC for 48K tapes.

No emulator code changed. The evidence, exact input identities, replay
scripts, reference observer patch and checks are in
[`2026-11-04-dizzy-128k-loading/`](2026-11-04-dizzy-128k-loading/README.md).
