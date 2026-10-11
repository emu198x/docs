# Preserve iNES trainers in existing cartridge RAM

Lane: best-in-class campaign. The existing loader accepts the trainer flag and
skips its file bytes, but never initializes cartridge RAM with them.

## Confirmed evidence

A 56-case matrix covers seven existing RAM-backed mappers (0, 1, 3, 4, 5,
34/NINA-001, 68), iNES/NES 2.0, battery on/off, and trainer present/absent.
All 28 trainer cases lose the data; all 28 no-trainer controls pass. A full CPU
guest copies every byte of $7000-$71FF into internal RAM, proving the same
28 failures through the machine bus. These are original synthetic images;
no retail-board identity is inferred from a header flag.

The full Mesen core agrees with the expected bytes in 54 of 56 cases. Its two
MMC5 battery/trainer cases also lose the data. The adjacent reference source
explains a plausible cause: BaseMapper loads the trainer into RAM before calling
LoadBattery; MMC5's override creates a zero-filled temporary vector and copies it
over saved RAM even when no battery data was read. That source was not used to
build the prebuilt binary, so it is supporting evidence, not a proven binary
trace. This exception is retained explicitly rather than treating Mesen as a
universal trainer oracle.

## Sources

The format author's specification at
https://fms.komkon.org/EMUL8/NES.html (the .NES File Format section), checked
2026-10-11, assigns header byte 6 bit 2 to a 512-byte trainer at $7000-$71FF and
places its payload immediately before PRG ROM. This is a container convention,
not a claim about an original cartridge's circuitry.

Implementation precedent: Mesen2 Core/NES/BaseMapper.cpp and
Mappers/Nintendo/MMC5.h; FCEUX src/ines.cpp initializes all 512 CPU addresses and
installs an override when writes cannot retain the bytes. The latter is a wider
compatibility strategy; introducing such an overlay here would require a
separate approved architecture/snapshot change.

## Bounded correction to execute

1. Add failing parser tests in `crates/format-nintendo-nes-ines/tests/trainers.rs`:
   all supported existing RAM-backed mappers, both headers and battery values;
   exact 512-byte placement, unchanged surrounding RAM/PRG/CHR, no-trainer
   controls, truncation, and snapshot round trips after guest RAM writes.
2. In `crates/format-nintendo-nes-ines/src/format.rs`, initialize the already
   allocated RAM through the existing `save_ram`/`restore_save_ram` interface.
   Copy only $1000-$11FF of that RAM, preserving the remaining bytes. Do not
   manufacture CPU register writes, bypass mapper write protection at runtime,
   or allocate a new persistent memory region.
3. Add CPU-guest regressions in `crates/machine-nintendo-nes/tests/trainer_loading.rs`.
   Verify all 512 bytes, normal guest writes, and save/restore retaining the
   modified RAM rather than reapplying the original trainer.
4. Run affected parser/machine/runtime suites, all-target Clippy and formatting.
   Require exact-head CI and a verified merge before calling the fix landed.

There is no mapper-state or public-signature change in this correction. RAM-less
boards and separately declared NES 2.0 RAM sizes remain explicit unsupported
breadth, not justification for fabricating a universally readable overlay.
Snapshot/schema work for four-screen RAM and MMC5 CHR remains separately pending.

## Status

The correction is implemented locally. Both new parser and guest regressions
failed before it. All 56 corrected guest captures now match every byte. Parser,
machine and runtime suites report 197 passes, zero failures and 135 ignored
tests. Affected all-target Clippy and workspace formatting pass. Exact-head CI and merge verification are pending. The unrelated
inspection-mirroring correction merged in source PR #1732; this change is rebased on that verified main.

The format-author fact is recorded in the primary library at
`reference/by-system/nintendo-nes/ines-trainer-loading.md`, umbrella commit
`211e0cdc` (local, not pushed). See [the evidence bundle](2026-10-11-nes-trainer-evidence/README.md).


Source [PR #1733](https://github.com/emu198x/emu198x/pull/1733), exact tested head
`0c08720430217f6402ed5bcab5a2a00fb2fec188`, is pushed with CI running.
The local 197-pass count includes the five inspection regressions merged in
#1732. Both affected package checks and all-target Clippy were rerun after rebasing.
