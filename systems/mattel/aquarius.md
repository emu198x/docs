# Mattel Aquarius

## Status: Boots BASIC and plays cartridge games

Renders text correctly and auto-starts cartridge games to their title screens —
Astrosmash, Snafu, Burgertime, Night Stalker, Utopia and Tron all reach play.
Z80A + Microsoft BASIC ROM (8 KB) + separate 2 KB character ROM, 4 KB internal
RAM, optional 16 KB expansion.

The family runtime selects two fixed regional board owners: `mattel-aquarius`
(NTSC, the existing default) and `mattel-aquarius-pal`. Both retain version-4
live saves and use the same firmware directory. Expansion RAM and the Mini
Expander remain configurations.

## What works

- **Z80A core** — shared `emu198x-zilog-z80` at 3.579545 MHz.
- **Text rendering** — glyphs from the separate 2 KB character-generator ROM
  (`aq2.u5`), not the BASIC ROM. BASIC boots to "BASIC / Press RETURN".
- **Cartridge auto-start** — the BIOS cart-detect descrambles correctly and
  jumps to `$E010`; six game carts verified to title screens (validated:
  `cart_detect_reaches_cart_entry`, `cart_descrambles_and_renders`).
- **Software-lock scrambler** — port `$FF` sets an 8-bit pattern; all external-bus
  bytes (`$4000-$FFFF`) are XORed with it on read and write. Transparent for RAM,
  descrambling for cart ROM.
- **16 KB cart mapping** — carts map at the top of memory by size (8 KB at
  `$E000`, 16 KB at `$C000`).
- **Speaker audio** — port `$FC` bit 0 is sampled into the runtime’s 48 kHz mono
  output. Port `$FF` controls the software lock and does not drive the speaker.
- **Live saves** — CPU, AY, firmware, character ROM, cartridge, RAM and video
  state resume from version-4 payloads. Restore checks the selected regional
  board before changing the runtime; reset retains the restored firmware,
  cartridge and RAM expansion.
- **Controllers** — read through the Mini Expander AY-3-8910 I/O ports.

## Not implemented / accuracy gaps

- **Held controller history after restore** — version-4 saves retain the current
  electrical controller byte but omit the host’s logical button mirror. The
  next press/release can clear another held control; opposing-direction history
  cannot be recovered from that byte. Tracked in [#2205](https://github.com/emu198x/emu198x/issues/2205).

- **Mapper view / port `$FD`** — MAME has a second memory layout (cart at
  `$0000`, BIOS relocated) switched via `$FD`. We implement only the default
  layout; software that switches it is unhandled.
- **Expansion RAM region** — modelled at `$4000-$7FFF`; MAME's external region is
  `$4000-$BFFF`. Not exercised by tested carts.

## Known unknowns / disproven hypotheses

- **Open: BIOS periodically blanks the whole screen** for a wide stretch of
  frames (~100+) in its idle loop — `render_display` then catches an all-backdrop
  frame. Surfaced when the region/clock fix shifted the boot-test sampling point
  off a "drawn" frame (the test now keeps the best frame across the run). A real
  Aquarius shows `READY` steadily, so this is a suspected render/screen-RAM bug,
  not real behaviour — separate from the clock work. (2026-06-08.)
- **DISPROVEN: "Astrosmash not drawing is a per-game quirk."** It stalled blank
  on *every* 16 KB cart, not just Astrosmash — a system-level bug, the scrambler
  (below). (2026-06-06.)
- **DISPROVEN: "cart-detect fails, so carts fall to BASIC."** Detection actually
  *succeeded*; the corruption was a fictitious per-frame NMI whose `$0066` vector
  sits inside the detect loop. The base Aquarius wires no periodic interrupt (per
  MAME, IRQ/NMI come only from the expansion port). (Fixed `5196c74a`.)
- **Root cause of the blank-cart reboot (resolved):** the missing scrambler XOR.
  The BIOS derives the lock pattern from the cart checksum and `OUT ($FF),A`
  before `JP $E010`; without the XOR applied to reads, the cart entry read as
  garbage (`$39` = `ADD HL,SP; RST $30` → reset) and reboot-looped. (Fixed
  `5196c74a`.)
- **Open: no-cart RUN/playability depth.** BASIC boots to the prompt; typing
  full programs into BASIC isn't exercised here.

## Validated against

- MAME `aquarius.cpp` — `scrambler_w` + the `$4000-$FFFF` bus XOR handlers; the
  expansion-only IRQ/NMI wiring (no VBlank interrupt); the mapper view.
- MAME `aquarius.zip` `aq2.u5` — the standard character generator.
- Six TOSEC cart games (`.../Mattel/Aquarius/Games/[BIN]`) to title screens.

## Timing & cycle-accuracy

- **Master clock & dividers** — single 7.15909 MHz crystal; Z80A at ÷2 =
  3.579545 MHz (MAME `7.15909_MHz_XTAL / 2`). The common engine’s existing regional
  timing is fixed by each owner: NTSC (262 lines, ~59.7 Hz — the default)
  or PAL (313 lines, ~50.1 Hz); the frame is
  458 × lines ÷ 2 T-states. The core previously hardcoded 3.5 MHz / PAL-50 Hz,
  running the NTSC machine ~20% slow with the CPU ~2% off; fixed 2026-06-08.
  **No periodic CPU interrupt** — the base machine wires neither IRQ nor NMI
  (per MAME; only the expansion port can assert them). This is load-bearing: a
  fictitious per-frame NMI corrupted cart-detect (fixed `5196c74a`).
- **Timing model realised** — relaxed: the 40×25 character display renders
  **end-of-frame** (mid-frame char/colour writes show next frame).
- **CPU timing** — Z80 cycle-accurate (§62).
- **Distance to full cycle-accuracy** — per-scanline display; correct external-bus
  (scrambler) timing is already modelled and validated.

## Tooling & drivability

- **Script / MCP** — `--script` + `--mcp`; `run_until_pc` + the gated cart-boot
  probes cover cartridge detection and descrambling.
- **Native window** — shared `emu198x-ui` window with keyboard and Mini Expander
  controller input; select the board at launch with `--model`. Live switching
  is not advertised by this runtime.
- **Disassembler** — pending the Asm198x shared Z80 disassembler.

## Peripherals & connectivity

- **Emulated now** — cartridge (with the software-lock scrambler), keyboard,
  Mini-Expander AY controllers.
- **Period peripherals (emulatable)** — the Mini Expander (AY + 2 controller
  ports), 4K/16K RAM cartridges, cassette, the Aquarius printer.
- **Internet-capable** — **No**: a low-end 1983 machine with cassette I/O and no
  period or practical modern net path.

## Crates

| Crate | Role |
|-------|------|
| `emu198x-zilog-z80` | CPU |
| `emu198x-gi-ay-3-8910` | Mini Expander PSG + controller ports |
| `common-mattel-aquarius` | shared original engine, serialized state and component tests |
| `machine-mattel-aquarius` | fixed NTSC board owner |
| `machine-mattel-aquarius-pal` | fixed PAL board owner |
| `runtime-mattel-aquarius` | shared-shell runtime |
| `emu198x-mattel-aquarius` | native, script and MCP runner |

## ROMs

- BIOS: `~/.emu198x/roms/mattel-aquarius/aquarius.rom` (8 KB), or
  `$EMU198X_AQUARIUS_BIOS`.
- Character ROM: `~/.emu198x/roms/mattel-aquarius/aquarius-char.rom` (2 KB, from
  MAME `aq2.u5`), or `--char` / `$EMU198X_AQUARIUS_CHAR`.
- Carts: TOSEC `.../Mattel/Aquarius/Games/[BIN]` (zipped).

## Launch

```sh
cargo run --release -p emu198x-mattel-aquarius -- \
  --model mattel-aquarius-pal \
  --cart "Astrosmash (1982)(Mattel).bin" --frames 400 --screenshot astro.png
```

The extraction preserves the existing clock, scanline and palette algorithms.
The shared reference library lacks a primary service manual, so the split is
not new evidence that those timing values match every physical revision.

Fixture-free tests give each board independent boot, guest input, cartridge/RAM
and native-boundary evidence. Complete original-engine state, pixel and audio
fixtures live in `test-data/mattel-aquarius/board-split-v4/`; optional local
manufacturer-ROM tests live in `runtime-mattel-aquarius/tests/local_firmware.rs`.
