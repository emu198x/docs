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
