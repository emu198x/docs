# MMC5 CHR latch observation cartridge

This cartridge exposes the uncertain low write bits through ordinary CPU
register writes and buffered PPU reads. It records observations, not a guessed
pass condition for those bits. No physical MMC5 run has been made.

The existing Emu198x core completes all 32 rows and reproduces 17 incorrect
static selections. A full run through the local Mesen core selects all 32
static pages correctly. Both cores return the raw input after switching to
1 KiB mode, reflecting their known register-retention simplification. Agreement
on that column does **not** establish correct hardware behaviour.

## Build and run

The installed ca65 and ld65 tools build the original assembly. Python uses
only its standard library. The generated image has 32 KiB PRG and 256 KiB
CHR, with an iNES mapper-5 header. Program execution stays in the final 8 KiB
PRG window. Cartridge RAM, IRQs, sound and sprites are unused.

```sh
python3 build.py /tmp/mmc5-observation-build
```

The output is `mmc5-chr-observe.nes`. Expected SHA-256:
`93a272c200ea6a332506203423ca410c56fb02533a8e86b6764d6e8870d5a4b4`.
ROM bytes, object files, rendered frames and third-party binaries are not
committed. The font and test program are original.

To reproduce both emulator runs, use a clean source checkout, the vendored
Mesen source and an existing compatible `MesenCore.dylib`:

```sh
python3 verify.py /path/to/emu198x /path/to/Mesen2 \
  /path/to/MesenCore.dylib /tmp/mmc5-observation-verification
```

This macOS verification harness requires Python 3.13+, the source checkout's
Rust toolchain, clang++ and cc65. It builds the ROM twice, builds the current
NES machine library, compiles the two hosts, runs Mesen twice, checks all rows,
and corrupts one CHR complement byte to verify both hosts return an error.
It records the exact emulator revision, ROM hash and Mesen binary hash.
The Mesen core was prebuilt locally; this probe does not prove that binary's
build revision merely by identifying the adjacent source checkout.

## Measurement

Rendering is disabled while taking measurements. Each physical 1 KiB CHR page
starts with its page number and that number's one's complement. All page
numbers exercised here fit in eight bits.

For each write-time mode 0–3 and input 0–7, the CPU:

1. Writes the mode to $5101 and the input to $5127, with $5130 initially zero.
2. Reads $1C00 through $2007, discarding the first buffered read. This is the
   unchanged-mode control. $5127 supplies this address in all four modes.
3. Changes $5101 to 3 without another bank write, then reads $1C00 and $1C01.
   These expose the physical page and its complement in 1 KiB mode.
4. Sets the PPU address again and repeats the buffered page read.

The read checks catch stale-buffer, complement and unstable-read faults.
Mode 3 provides eight unchanged-mode controls. The static expected page is
`(input << (3 - mode)) + (7 >> mode)`: the second term accounts for $1C00's
position within the larger bank. The 32-case matrix covers all combinations
of the three low input bits, but it does not claim coverage of all registers,
upper-bank bits, sprite/background selection, reset state or every CPU byte.

The two uncertain paths are AF4's input/enable and AF5's input. The isolated
SVG overlay does not resolve them independently of the schematic annotations.
The source is the [die-tracing repository at the inspected revision](https://github.com/benboldtumd/mmc5-decap/tree/2f592e68c60097b93c27b15dcdeebf676b10dc0b).
No inferred zero-fill or inversion is used as a low-bit oracle here.

## Reading the screen

Columns are input values 00–07. Rows 0–3 mean 8, 4, 2 and 1 KiB write modes.
All reported values are hexadecimal physical 1 KiB page numbers.

- **MODE THEN 1K WITHOUT WRITE** shows the retained-register observation.
- **MODE WITHOUT CHANGE** shows the static control taken before switching.
- **READ CHECK ERRORS** must be 00, and **DONE** must appear.

For a hardware capture, record the actual MMC5/MMC5A marking, board identity,
console model and image hash, and photograph the entire screen. The cartridge
image needs a compatible board or test fixture with a genuine MMC5/MMC5A and
the stated PRG/CHR payloads. A flash cartridge emulating mapper 5 supplies
another implementation's result, not a measurement of the Nintendo chip.
Board-specific programming instructions are outside this probe.

The internal-RAM report can also be captured without interpreting glyphs:

| CPU address | Meaning |
| --- | --- |
| $0400–$041F | Retained pages, row = mode × 8 + input |
| $0420–$043F | Unchanged-mode pages |
| $0440–$045F | Complement bytes |
| $0460–$047F | Repeated retained-page reads |
| $04F0 | $A5 once all samples are stored |
| $04F1 | $A5 once the screen is ready |
| $04F2 | Read-check error count |
| $04F3–$04F6 | ASCII `M5C1` |
| $04F7 | Completed row count, decimal 32 |

## Recorded verification

`emu198x.csv`, `mesen.csv` and `summary.json` record the verified run. The
source head is `ad4790beda679afab6c826fcb9ed8e8f07b01877`. Static mismatches
by mode are 7, 6, 4 and 0. Both 32-row runs pass complement, repeated-read and
1 KiB controls; the Rust host additionally checks that every displayed value
matches its sampled RAM byte. The full framebuffer was rendered and inspected.

The deliberately broken image changes page 0's complement from $FF to $00.
Both hosts exit 1: Emu198x reports `guest read controls failed`; Mesen reports
`reference completion, static-page or read control failed`. The successful
observations therefore depend on checks that can fail.

Ruff and Rust formatting checks pass; the Rust host compiles with warnings
denied. This adds reproducible test equipment, not a mapper correction or a
hardware validation claim. The parent snapshot-v2 proposal remains pending.
