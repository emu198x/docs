# Oric-1 / Atmos

## Status: Boots to BASIC `Ready`; keyboard types

Oric-1 BASIC 1.0 and Atmos BASIC 1.1 both reach their distinct banners and
`Ready`. The [firmware correction evidence](../../plans/2026-11-03-oric1-firmware-correction.md)
records exact ROM identities and the ROM-specific STR$ behaviour. 6502 + VIA-6522 + AY-3-8912 + custom video ULA (inline) — no new
chip crate.

## Board identity

The manufacturer's *Service Manual for the Oric-1 and Oric Atmos
Microcomputers* (1984), pp. 10–11 and 46, identifies BN0130 as the main PCB
assembly for both 48K Oric-1 and Atmos. Both contain 64 KiB of physical DRAM,
with ROM selected over the upper 16 KiB. The 16K Oric-1 uses the different
BN0135 assembly and is not an implemented profile.

A product name or ROM revision does not identify every physical board.
Pages 22–23 distinguish PCB layout issues from electrical circuit issues;
leaflets 52/53/56/63(b), pp. 69–72, document fitted changes including cassette
loading and power-up initialization. The present ROM profiles do not qualify
every such population. Revision-specific owners remain open under #2144.

The [primary-source audit](https://github.com/stevehill1981/198x/pull/294)
records the assembly numbers, fitted changes and transcription ambiguities.

The [complete original schematic audit](https://github.com/stevehill1981/198x/pull/297)
identifies BN0130 **circuit issue 7**, C/N63, dated 24-2-84, and supplies the
R26-to-IC22-pin-8 connection for that drawing. It still does not identify the
physical PCB issue or every fitted amplifier/modification population. The
[qualification matrix](../../plans/2026-11-03-oric-board-qualification.md)
records what is established and what remains before fixed owners can be named.

## What works

- **Boot to BASIC** (2026-06-04) with BASIC 1.1 UK (16K, md5 `3202…b629`, MAME
  `oric1`). Boot test asserts the banner in TEXT screen RAM (`$BB80`).
- **Keyboard** — sense on VIA PB3 (column on PB0-2, row mask on port A), 8×8
  matrix wired (2026-06-05); types `HELLO`, RETURN executes.
- **AY-via-VIA wiring** — VIA port A = AY data bus, CA2 = BDIR, CB2 = BC1; software
  drives one of four (BDIR,BC1) modes per AY op.
- **Display** — TEXT + HIRES with serial-attribute rendering, BBC-compatible
  8-colour 3-bit RGB palette.

## Not implemented / accuracy gaps

- **RAM-under-ROM** — 64K allocated, writes reach RAM even at ROM addresses, but
  ROM wins on reads; bank-switching to expose RAM at `$C000-$FFFF` not modelled.
- **TAP cassette loader** — donor has the `.tap` parser; not yet wired into the
  binary.
- **Snapshot** deferred. **No native window.**

## Known unknowns / disproven hypotheses

- **DISPROVEN (donor): keyboard sense model.** Fixed to sense on VIA PB3 (column
  PB0-2, row mask on port A) and wired the 8×8 matrix (2026-06-05) — the boot
  itself was clean first-try, no code changes.
- **Verification targets** — RAM-under-ROM banking; a real raster-split demo
  against the Oric reference (`emulators/oric/oricutron/`) to confirm the
  per-scanline split point.

## Validated against

- MAME `oric1` BASIC 1.1 ROM → `Ready` (banner asserted in `$BB80`).
- Reference: Oricutron (`emulators/oric/oricutron/`) — IJK joystick + AY-via-VIA.

## Timing & cycle-accuracy

- **Master clock & dividers** — 6502 at ~1 MHz; the custom video ULA generates the
  display from screen RAM.
- **Timing model realised** — **per-scanline**: `run_frame` runs the CPU a raster
  line at a time and renders each visible display line from RAM at the moment the
  beam scans it (display at raster 65..289, Oricutron `vid_start`). Mid-frame
  changes — raster splits, per-line serial-attribute and TEXT/HIRES mode changes —
  now land on the right rows. (2026-06-08; was end-of-frame.)
- **CPU timing** — 6502 cycle-accurate (§62).
- **Distance to full cycle-accuracy** — sub-scanline ULA fetch timing (the
  per-line render samples RAM at line start, not per character cell);
  RAM-under-ROM banking.

## Tooling & drivability

- **Script / MCP** — `--script` + `--mcp`.
- **Native window** — headless only (extended tier).
- **Disassembler** — pending the Asm198x shared 6502 disassembler.

## Peripherals & connectivity

- **Emulated now** — keyboard, AY sound, TEXT/HIRES display.
- **Period peripherals (emulatable)** — the Microdisc/Jasmin disk units, printer,
  the IJK joystick interface, cassette.
- **Internet-capable** — **Marginal**: a strong French scene with period modems
  and Minitel/telematics access via the serial path; no prioritised modern device,
  but a serial-modem bridge fits the platform's history.

## Crates

| Crate | Role |
|-------|------|
| `mos-6502` | CPU |
| `mos-via-6522` / `gi-ay-3-8912` | VIA · PSG |
| `machine-oric-atmos` (video ULA inline) / `runtime-…` / `emu198x-oric-atmos` | wiring + runner |

## ROMs

Both profiles need a 16 KiB BASIC/OS image. Oric-1 requires `oric1-rom`,
uses `EMU198X_ORIC1_ROM`, and searches `oric-1.rom`, `oric1.rom`, then
`basic10.rom`. Atmos retains `oric-rom`, `EMU198X_ORIC_ROM`, and searches
`atmos.rom`, `oric.rom`, then `basic11b.rom`. The shared directory remains
`~/.emu198x/roms/oric/` (or `--rom-dir` / `EMU198X_ORIC_ROM_DIR`).

A directory containing only `oric.rom` no longer satisfies Oric-1. A bare
`--rom PATH` binds to the final `--model` in either argument order; explicit
`--rom ID=PATH` must name that model's firmware ID. Custom/localised ROMs
remain accepted. These ROM profiles do not identify physical PCB revisions.

The opt-in `runtime-oric-atmos` real-ROM tests require
`EMU198X_ORIC_REFERENCE_ROM_DIR` containing `basic10.rom` and `basic11b.rom`.
They check complete SHA-256 identities before boot, then the exact BASIC
version banner, `Ready`, and keyboard-entered `PRINTASC(STR$(1))`: BASIC 1.0
returns `2`, BASIC 1.1 returns `32`. Wrong-ROM, mutated-byte and incorrect
behaviour controls must reject. No firmware bytes are bundled.

## Launch

```sh
cargo run --release -p emu198x-oric-atmos -- --frames 200 --screenshot oric.png
```
