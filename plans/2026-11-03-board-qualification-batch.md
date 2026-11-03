# Board qualification continuation

Engineering-frontier accuracy work approved on 2026-11-03: #2237, #52,
#2200 and the original PET 2001 part of #355, in that order. Diagnose existing
failures before adding hardware. Use the Rust skill; keep unrelated checkouts
and the other active sessions untouched.

## Amiga #2237

1. Reproduce both PAL mixed-chip white screens with unchanged Kickstart 1.3
   using runtime-commodore-amiga/examples/fixed_ocs_boot_capture.rs. Retain
   firmware identity, native frame hash and PC/chip-state observations.
2. Compare the failing boot loop with NTSC mixed-chip, PAL rev-5 and 2.04
   controls. Consult emulators/amiga/WinUAE and the primary Amiga references
   before changing hardware. Narrow the first differing observation.
3. Write the root cause and bounded correction here before production edits.
   Expected touch points are common-commodore-amiga-ocs and the implicated
   chip crate only after evidence identifies them. No proposed schema change.
4. Require a failing focused regression, original-ROM non-monochrome boot,
   native-clock and save/restore checks, relevant affected suites and CI.

## Timex #52

Reconsult the TS2068 technical manual, shared ULA/SCLD decisions and Fuse.
Reproduce both ROM startups before modifying rendering. Distinguish documented
modes and colour/brightness evidence; pixel tests must use independent output.
Verify BASIC commands, selected timing and deterministic restore for both
owners. Identify exact files and compatibility effects before code changes.

## Sony HB-10P #2200

First establish the board RAM mirror, I/O masks and chip identities from
primary Sony documentation. openMSX is implementation precedent only. Write
focused positive/negative guest probes. Agree any v10 compatibility change
before implementing it; C-BIOS alone cannot qualify the Sony board.

## Original PET 2001 #355

First identify a concrete original board, ROM map and chiclet keyboard from
primary sources and VICE. Write its proposed owner/profile and save contract
before adding it. Existing 2001N/4032/8032 coverage must remain exact; broader
PET/IEEE/interlace work is outside this bounded addition.

## Workspaces and completion

Source: /private/tmp/198x-qualification-source, branch
fix/board-qualification-batch. Docs: /private/tmp/198x-qualification-docs,
branch docs/board-qualification-batch. Build cache:
/private/tmp/198x-qualification-target. Diagnostics:
/private/tmp/198x-qualification-evidence. Record each root cause, verification
and outstanding limit in durable docs/issues. Commit and push each completed
correction; merge only after required checks pass. Retain diagnostic evidence
and verified remote commits before removing worktrees/caches. Do not delete
unrelated work or the earlier locked investigations.

## #2237: the original capture already contains the graphic

No production hardware or runtime correction is needed. The unchanged source
reproduces RGBA SHA-256
`f28bfeb54f3397f7983077641057b561e150627267c133eaeafbd7552624d436`,
the very value previously labelled white. Both an independent stdlib
zlib/PNG-filter decoder and ImageMagick decode four colours: 21,212 black,
15,200 purple (119/119/204), 3,628 grey (187/187/187), and 402,328 white pixels.
The purple disk body occupies x=294..493, y=142..305. Native ARGB, captured RGBA
and the decoded PNG agree. The inspection viewer shows the original PNG as
white but displays a lossless re-encoding correctly. This is an inspection-path
failure; its decoder mechanism is not established. No emulator fault has been
reproduced. The original files and their hashes must remain intact.

The two strict `kick13_pal_mixed_boot` tests pass for the A500 rev-6a PAL and
A2000CR rev-6 PAL at 650 fields, checking the full original firmware hash,
full-frame identity, actual coloured pixels, native/capture/PNG agreement,
white-frame and one-byte-mutation rejection, and two exact resumed fields plus
complete state equality. A fixture-free test decodes the exact original PNG,
checks the graphic and executes both rejection controls on normal CI runs.
No dependency, CPU/chip behaviour or save-layout change is introduced.

[Evidence](2026-11-03-board-qualification-evidence/) retains the original capture,
its receipt, strict test output and the lossless inspection copy. The older
native evidence's white-screen wording is historical and disproven here.
