# Preserve MMC5 CHR bank register contents across mode changes

This is best-in-class campaign work under
[issue #92](https://github.com/emu198x/emu198x/issues/92). No production code
has changed. The probes confirm incorrect static bank selection and a second
fault when a written bank survives a mode change.

## Evidence

The source head is `f3604fa2e752dabe1e6a4274d6fd41e3b4bbdf95`.
The [probe bundle](2026-10-11-mmc5-chr-register-evidence/README.md) contains
64 static cases, 34 wrong, and 16 retained-register cases, twelve wrong.
The latter start in 1 KiB mode with 8 KiB-aligned physical bases and widen
the window without rewriting the register. All four unchanged-mode controls
pass. No unresolved low write bits contribute to these failures.

`chr_reg_for_addr` discards low register bits in larger modes;
`chr_index` then multiplies the result by the current window size. Meanwhile
the write path retains the raw CPU byte and upper bits, independently of the
write-time mode. Both sides need correction: masking alone is insufficient.

Compiled Mesen2 `UpdateChrBanks` confirms the static expectations. Its raw
register storage, FCEUX and NES_MiSTer share the mode-change simplification.
The circuit authority is Ben Boldt's die-derived schematic, revision
`2f592e68c60097b93c27b15dcdeebf676b10dc0b`, PDF pages 21 and 23:
mode-dependent input wiring feeds ten-bit latches, and mode changes select
output passthrough bits without rewriting those latches. The primary note is
`reference/by-topic/nes-mappers/2026-mmc5-chr-register-observations.md`.

## Proposed design

1. Keep the existing `chr_banks: [u16; 12]` storage, but store physical
   ten-bit latch values. Decode the CPU byte and $5130 through the write-time
   CHR mode in `crates/format-nintendo-nes-ines/src/mappers/mmc5.rs`.
2. Select registers using the existing window table. Derive addresses from
   retained physical bits and the current PPU offset, rather than rescaling
   the stored value. Changing $5130 alone must not rewrite a bank register.
3. Preserve those values through `MapperSnapshot::Mmc5`. Although the field
   widths stay unchanged, their meaning changes. Advance the NES runtime
   envelope in `crates/runtime-nintendo-nes/src/snapshot.rs` from v1 to v2
   and reject v1. Old saves do not contain the write-time modes needed for a
   reliable conversion.
4. Add public mapper regressions for static modes, retained bases, upper-bit
   write capture, register independence and save/restore between writes and
   mode changes. Files: `crates/format-nintendo-nes-ines/tests/parser.rs`,
   a focused `tests/mmc5_chr_registers.rs`, and
   `crates/runtime-nintendo-nes/tests/snapshot_roundtrip.rs`. Update the
   version lock `snapshot_envelope_version_is_locked_at_v1` in
   `crates/runtime-nintendo-nes/tests/boot_invariants.rs`.
5. Run affected parser/machine/runtime tests, all-target Clippy, formatting,
   then guarded source PR CI. Keep #92 open: this does not establish complete
   MMC5 graphics, IRQ or mapper coverage.

The alternative is to remove only the low-bit masks. It fixes the initial
static failures but demonstrably leaves the retained-register failures.
We recommend the physical-register correction.

## Validation requirement before implementing uncertain bits

The wiki leaves some low write bits unspecified. The schematic annotates
AF4's enable polarity and labels AF5's input with a question mark. Trace
those connections against the die annotations or a primary hardware test
before choosing their values. Do not substitute zeroes or copy another
emulator's raw-register representation to get the suite green. The confirmed
widening failures already justify the retained representation independently
of how this remaining low-bit question is resolved.

## Approval boundary

Await approval for the changed serialized meaning and NES snapshot v2.
AGENTS.md requires agreement for “Breaking changes to APIs or data schemas”.
The proposed ten-bit representation is concrete; approval does not waive the
remaining low-bit validation requirement above.

## Hardware observation cartridge

The traced AF4/AF5 inputs remain uncertain. Build a standalone observation
cartridge in `2026-10-11-mmc5-chr-register-evidence/hardware/` before assigning
those bits. This is test preparation; the snapshot approval remains pending.

1. `observe.s` writes $5127 with values 0–7 in each of the four modes,
   reads the current window through $2007, changes to 1 KiB without another
   bank write, and reads the retained physical page twice plus its complement.
   Keep all 32 observations in internal RAM and display the two page matrices.
2. `build.py` and `observe.cfg` use the installed ca65/ld65 tools to produce
   an iNES mapper-5 cartridge with 32 KiB PRG and 256 KiB synthetic CHR.
   Each physical 1 KiB page starts with its index and one's complement.
   The display font is original, and no third-party ROM bytes are included.
3. `run.rs` executes the cartridge on the existing full NES machine, verifies
   completion, every row, repeat/complement controls, and the screen's tile
   contents. Save raw observations and a framebuffer. Perturb one control to
   prove verification rejects bad output; an emulator run is not hardware
   evidence for the unresolved bits.
4. Document the on-screen layout and cartridge requirements. A genuine MMC5
   or MMC5A result, with chip/board identity and an unambiguous photograph,
   remains necessary before treating the low-bit values as measured facts.
