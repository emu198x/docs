# Sega Mega Drive / Genesis

The family runtime runs project-written Mega Drive and Master System cartridges
on three fixed regional owners. It provides native windows, script and MCP
control, video, stereo audio, controller input and version-2 live saves.
Synthetic tests establish these paths; they do not establish commercial-game
compatibility or complete hardware accuracy.

| Board | Machine/profile ID | Machine crate |
|---|---|---|
| Japan, domestic NTSC | `sega-mega-drive-japan` | `machine-sega-mega-drive-japan` |
| Americas, overseas NTSC | `sega-genesis` | `machine-sega-genesis` |
| Europe, overseas PAL | `sega-mega-drive-europe` | `machine-sega-mega-drive-europe` |

The family runner remains `emu198x-sega-mega-drive`. Its catalogue IDs
`mega-drive-japan`, `genesis` and `mega-drive-europe`, and their full profile-ID
aliases, retain their existing meanings. The aggregate `sega-mega-drive` registry
entry is retired; it does not describe a fourth board. The site redirects that
old system page to the existing default Genesis profile.

## Implemented paths

- The 68000 and Z80 share the console wiring, with bus request/reset handling,
  sound RAM, the Z80 bank window and master-clock dividers.
- The VDP supplies native frame boundaries, video, DMA and interrupt paths.
  Runtime output follows the active H32/H40 geometry and television standard.
- YM2612 and SN76489 output is mixed into 48 kHz stereo packets.
- Three- and six-button pad protocol state lives in the hardware payload;
  individual button events preserve other held controls across restore.
- Raw Mega Drive images and interleaved SMD images load through the runtime.
  Master System headers or an explicit `master-system` cartridge type select
  Power Base Converter mode. The converter remains a configuration of the
  regional board, with mapper state and Z80 execution preserved in saves.
- Version-2 envelopes retain their original bytes and model IDs. A restore
  validates market, VDP standard and memory geometry before changing runtime
  time or cartridge caches. Cartridge and converter selection survive reset,
  restore into a blank runtime and family switching.
- Script/MCP queries and 68000 debug stepping/disassembly use the family runtime.
  No system BIOS is required by the currently modelled cartridge path.

## Evidence and limits

`test-data/sega-mega-drive/board-split-v2/` contains project-written cartridges,
original complete version-2 envelopes and continued output for all three markets
in native and converter modes. The checks compare every framebuffer pixel,
dimension, timestamp, stereo sample bit and final save, including restored
partial fields and a six-button pad handshake. A deliberately corrupted expected
output must fail.

Each owner also has direct fixture-free tests for guest video and version-register
reads, controller input/restore, 68000-to-Z80 handoff, Power Base banking, foreign
state rejection and partial-field continuity. Shared chip/component tests remain
in `common-sega-mega-drive`; those results are not credited exclusively to one
regional board.

The extraction preserves the existing CPU, VDP, sound, bus and mapper algorithms.
It does not newly validate additional motherboard revisions, TMSS, sound-chip
revisions or commercial cartridges. Cartridge SRAM, TMSS and additional waits
between the Z80 and the 68000 bus remain work under [#2034](https://github.com/emu198x/emu198x/issues/2034).
Sega CD, 32X and network peripherals are not modelled by these owners.

## Clocks and source

The implemented master clocks are 53,693,175 Hz for NTSC and 53,203,424 Hz for PAL.
The 68000 and Z80 derive their clocks at master ÷7 and master ÷15. Machine time
counts master clocks; native frame requests stop at the VDP's completed boundary,
including when execution starts partway through a field.

Sega's *Software Manual*, system I/O/version register at `$A10001` (printed page
71, revision 02/20/92), specifies separate domestic/overseas and NTSC/PAL bits.
Provenance: `reference/by-system/sega-megadrive/1990-sega-genesis-software-manual.txt`.
This split separates the three combinations the engine already models.

## Crates and launch

`common-sega-mega-drive` owns the shared engine, I/O, converter and legacy
serialized state. The three machine crates bind fixed regional wiring;
`runtime-sega-mega-drive` owns the family catalogue, snapshots, input and debug
surface. CPU, VDP and sound chips remain separate component crates.

```sh
cargo run --release -p emu198x-sega-mega-drive -- \
  --model genesis --cart game.bin --frames 120 --screenshot frame.png
```

Use `--model mega-drive-japan` or `--model mega-drive-europe` for the other two
owners. Save filenames use the unchanged profile ID, so the machine-registry
split does not move existing saved files.
