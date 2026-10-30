# Nintendo Entertainment System (NES)

## Status: separate NTSC and PAL boards, shared runtime

The implemented NTSC and PAL boards have fixed machine owners over shared
NES wiring. Both use the existing native runner, headless session and browser
family. Cartridge media, input peripherals and FDS compatibility remain
configurations of those execution paths.

| Board | Machine owner | Machine and profile ID |
|---|---|---|
| NES NTSC | `machine-nintendo-nes-ntsc` | `nintendo-nes-ntsc` |
| NES PAL | `machine-nintendo-nes-pal` | `nintendo-nes-pal` |

Each owner has seven direct tests. The original chip/mapper regressions live
in `common-nintendo-nes`; they are shared evidence. A separate Famicom
motherboard is not established by the NTSC profile's existing FDS support.

Native saves use version 3. They retain CPU open bus, PPU per-bit refresh
timestamps and the colour/emphasis mirror needed for the first resumed
composite-video field. Version 2 saves are rejected before payload decoding
because the omitted state cannot be recovered exactly. Both regional profiles
keep their existing IDs and aliases; loaded foreign-board states are rejected
without changing the live machine. Empty states keep the selected profile.
The published browser player has its own release version; this native format
change does not update an older browser bundle's save format.

Pads, Four Score and Zapper configurations survive restore. Battery-backed
PRG RAM survives reset and snapshots; the native UI loads and flushes `.sav`
sidecars. An FDS save carries its adapter BIOS, and reset after restoring into
a blank runtime reuses that restored BIOS. This supports the existing FDS
execution path without claiming independent Famicom hardware qualification.

## Hardware overview

- **CPU:** Ricoh 2A03 (6502 variant, no BCD mode, built-in audio)
- **Clock:** 21.477272 MHz master (NTSC), CPU at ÷12 (1.789773 MHz), PPU at ÷4 (5.369318 MHz)
- **Video:** PPU (2C02) — 256×240, 2 pattern tables (CHR ROM/RAM), 4 nametables, 64 sprites (8 per scanline), scrolling, palette of 64 colours (25 on screen)
- **Audio:** 2A03 built-in — 2 pulse channels, 1 triangle, 1 noise, 1 DPCM sample channel
- **Input:** Two controller ports (D-pad + A/B/Select/Start)
- **Storage:** Cartridge with mapper hardware (many variants)

## Implementation status

- **6502 CPU / 2A03 variant** — done and validated by `nestest`
- **PPU** — dot-driven 2C02 path with nametable mirroring and frame output
- **APU** — 5-channel 2A03 audio with host-side channel controls
- **Mapper system** — NROM, MMC1, UxROM, CNROM, MMC3, MMC5, AxROM, Color Dreams, VRC2a, Action 53, BxROM/BNROM, NINA-001, Sunsoft-4, and Camerica/Codemasters are implemented; the remaining long-tail mappers are compatibility-driven
- **iNES/NES 2.0** — ROM format parsing with mapper detection

## Automated test ROM checks

The headless `emu198x-nes` runner (`--no-default-features` skips the graphics stack) can assert Blargg-style test ROM output written at `$6000`. A passing ROM exits successfully and includes `test_result` in the JSON report; running, reset-requested, failed, or non-Blargg ROMs return a non-zero exit code.

```sh
cargo run --release -p emu198x-nes --no-default-features -- --rom apu_test.nes --frames 3000 --assert-blargg
cargo run --release -p emu198x-nes --no-default-features -- --smoke-root path/to/blargg/rom_singles --frames 1200 --assert-blargg --smoke-report tmp/nes-apu-blargg-report.json
```

## Board scope and qualification

NTSC and PAL are selectable fixed boards with their own CPU/PPU ratios and
APU tables. Dendy and separate Famicom board revisions are not established by
these two owners. The NTSC profile retains the existing FDS execution path.

The direct board tests prove those execution and preservation paths; they do
not establish complete commercial-library compatibility. The ledger below is
a dated measurement. Check current source tests and issue evidence before
using an old result to select an accuracy fix.

## Test-ROM ledger (2026-06-07)

Landed as `#[ignore]`-gated ledger tests in `crates/common-nintendo-nes/tests/`.
Run with `cargo test -p common-nintendo-nes --test <file> -- --ignored`.

- **`mmc3_test` 5/6** (`blargg_ppu.rs`) — scanline-IRQ A12 counter. Was 0/6: the
  PPU only notified the mapper of A12 edges while rendering, so the `$2006`-driven
  counter clocks the suite uses during forced blank were dropped. Now notifies on
  every edge with the PPU cycle, and the MMC3 filter measures A12 low-duration
  (Mesen's `_a12LowClock`). `6-MMC6` is intentionally unreachable — it tests the
  MMC3 rev-A IRQ behaviour that contradicts `5-MMC3`, and the two ROMs share
  identical mapper-4 headers (no per-ROM chip database here).
- **`ppu_read_buffer` PASS** (`blargg_ppu.rs`) — Bisqwit's ~80-sub-test `$2007`
  read-buffer suite. See the corrected note below.
- **`cpu_dummy_reads` PASS** (`blargg_legacy.rs`) — 6502 dummy reads on
  abs,X / (zp),Y / (zp,X). Older shell, no `$6000`; graded by scanning the
  ascii.chr nametable for "Passed".
- **sprite_hit 11/11 + sprite_overflow 5/5** (`ppu_onscreen.rs`) — 2005 suites
  graded via the `$f8` result byte; sprite-0-hit and overflow timing all pass.

## Known unknowns / disproven hypotheses

- **CORRECTED: `test_ppu_read_buffer.nes` now passes via `$6000`.** The earlier
  (2026-06-01) "reports via screen + audio, not `$6000`" conclusion was wrong: the
  ROM *does* write the `$6000` shell block, but it's CNROM (mapper 3) and the
  mapper port carried no `$6000` work RAM, so the signature never landed and the
  run looked like an endless "running"/VISUAL state. Adding 8 KiB WRAM at
  `$6000-$7FFF` on CNROM (as NROM already does) makes it report `Some(0)` — and
  the `$2007` read-buffer behaviour itself was already correct (2026-06-07).
  *Lesson:* a `None`/VISUAL verdict from the `$6000` harness can mean the cart's
  mapper lacks `$6000` WRAM, not a real PPU/CPU bug — check the mapper first.
- **Open: the 01-implied culprit** — `cpu_test5` is 10/11; the one implied/NOP
  opcode side-effect that fails the stricter CRC is not yet isolated. (The earlier
  "2/20 CRC probe" figure was stale.)
- **Open: the 5 FAIL ROMs** in the 155-sweep — individual causes not catalogued
  on this page.
- **Verification targets** — exact PPU/APU timing claims are from secondary
  knowledge; confirm against the NESdev wiki + Visual2C02/Visual2A03, not just
  passing test ROMs.

## Validated against

- `nestest` 8991/8991; Blargg-style `$6000` test ROMs; the 155-ROM smoke sweep.
  Super Mario Bros. renders.
- Per-suite ledgers (2026-06-07): `mmc3_test` 5/6, `ppu_read_buffer`,
  `cpu_dummy_reads`, sprite_hit 11/11, sprite_overflow 5/5, `ppu_vbl_nmi` 10/10,
  `instr_test-v5`, `instr_misc`, `oam_read`, `cpu_exec_space` (see the test-ROM
  ledger above; harnesses in `crates/common-nintendo-nes/tests/`).
- Reference: Mesen2, fceux, nestopia (`emulators/nes/`).

## Timing & cycle-accuracy

- **Master clock & dividers** — 21.477272 MHz NTSC. CPU = ÷12 (1.789773 MHz);
  PPU = ÷4 (5.369318 MHz) — the 3:1 PPU:CPU relationship.
- **Timing model realised** — strong: a **dot-driven 2C02 PPU** interleaved with
  the CPU at the 3:1 ratio. The remaining timing gaps are specific DMA/edge cases,
  not the core model.
- **CPU timing** — 2A03 cycle-accurate (§62; nestest 8991/8991 + Tom Harte prove
  the ISA).
- **Distance to full cycle-accuracy** — OAMDMA odd-cycle penalty + DMC sample-DMA
  interleave; `cpu_timing_test6`; the `blargg_nes_cpu_test5` 01-implied case.

## Tooling & drivability

- **Script / MCP** — `--script` + `--mcp`; Blargg `$6000` assertion + smoke-matrix.
- **Native window** — yes (primary tier): shared `wgpu` `raw`/`lcd`/`crt`,
  keyboard/gamepad.
- **Disassembler** — pending the Asm198x shared 6502 disassembler.

## Peripherals & connectivity

- **Emulated now** — cartridge mappers, pads, Zapper, Four Score and the
  existing NTSC FDS disk path.
- **Other period peripherals** — R.O.B. and Power Pad require their own
  implementation and qualification.
- **Internet-capable** — **Yes (Japan)**: the **Famicom Modem / Famicom Network
  System** (1988) ran stock-trading and betting services — a real, documented,
  emulatable modem. Modern flash-cart WiFi is also feasible. Marginal in the West.

## Crates

| Crate | Role | Status |
|-------|------|--------|
| `mos-6502` | Shared 6502 core with 2A03 mode | Done |
| `ricoh-ppu-2c02` | NES PPU | Ported |
| `ricoh-apu-2a03` | NES APU | Ported |
| `format-nintendo-nes-ines` | iNES parser + NROM/MMC1/UxROM/CNROM/MMC3/MMC5/AxROM/Color Dreams/VRC2a/Action 53/BxROM/NINA-001/Sunsoft-4/Camerica mappers | Active |
| `common-nintendo-nes` | Shared wiring and core regression tests | Active |
| `machine-nintendo-nes-ntsc` | Fixed NTSC board and direct tests | Active |
| `machine-nintendo-nes-pal` | Fixed PAL board and direct tests | Active |
| `runtime-nintendo-nes` | Shared shell runtime | Active |
| `emu198x-nes` | Native verifier shell | Active |

## Road to 100%

The dated test-ROM ledger records its original measurements. Current failures
and compatibility work should be verified against the source tests and live
issues before choosing the next accuracy change. Regional separation does not
by itself qualify every board revision, mapper or peripheral.
