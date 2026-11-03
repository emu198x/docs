# Commodore PET

Four fixed owners cover the original 8 KiB assembly-320008 board and three
later 32 KiB configurations. All reach BASIC READY and execute typed arithmetic
with identified original firmware. They do not represent the whole PET family.

| Machine owner | Profile ID | Firmware and keyboard | Native frame |
|---|---|---|---|
| `machine-commodore-pet-2001-320008` | `commodore-pet-2001-320008-8k` | Original assembly 320008, BASIC 1, graphics keyboard | 16,640 CPU clocks |
| `machine-commodore-pet-2001n-32k` | `commodore-pet-2001n-32k` | 2001N/3032 discrete video, BASIC 2, graphics keyboard | 16,640 CPU clocks |
| `machine-commodore-pet-4032` | `commodore-pet-40col` | 4032 50 Hz CRTC, BASIC 4, graphics keyboard, editor 901498-01 | 20,000 CPU clocks |
| `machine-commodore-pet-8032` | `commodore-pet-80col` | 8032 50 Hz CRTC, BASIC 4, UK business keyboard, exact editor 901474-04 | 19,992 CPU clocks |

These are the stable rasters programmed by the qualified editors, measured
against VICE 3.10. Other software can reprogram a CRTC. The 8032 fetches two
characters per CRTC address at the same 1 MHz machine cadence; it does not
clock the CRTC twice per CPU cycle. Its 25 ten-line rows occupy 250 active lines.

The old 40/80 profile IDs remain, but they now select coherent CRTC machines.
Use the new discrete profile for BASIC 2. Firmware contents never silently
select different hardware.

## Firmware

Place the matching parts in a directory and pass `--rom-dir`, or use
`--kernal`, `--basic`, `--editor` and `--char` explicitly. The default directory
is `~/.emu198x/roms/commodore-pet/`; each profile searches part-specific filenames.
The four firmware IDs and their environment overrides remain available.

| Part | 2001N/3032 | 4032 | 8032 |
|---|---|---|---|
| KERNAL, 4 KB | `kernal-2.901465-03.bin` | `kernal-4.901465-22.bin` | same BASIC-4 KERNAL |
| BASIC | `basic-2.901465-01-02.bin`, 8 KB at C000 | `basic-4.901465-23-20-21.bin`, 12 KB at B000 | same BASIC-4 image |
| Editor, 2 KB | `edit-2-n.901447-24.bin` | `edit-4-40-n-50Hz.901498-01.bin` | `edit-4-80-b-50Hz.901474-04.bin` |
| Characters, 2 KB | `characters-2.901447-10.bin` | same character ROM | same character ROM |

Multiple archived 901474-04 dumps exist. The qualified 8032 editor has SHA-1
`66887061b6c4ebef7d6efb90af9afd5e2c3b08ba`; its name alone is insufficient.
The [verification inputs](../../plans/2026-10-31-pet-board-owners/reference-runs.json)
record full SHA-256 identities. No ROM images are distributed here.

```sh
cargo run --release -p emu198x-commodore-pet -- \
  --model commodore-pet-2001n-32k --rom-dir /path/to/pet-roms \
  --headless --frames 120 --screenshot pet.png
```

## Implemented surfaces and saves

The shared runner provides a native window, headless capture, script and MCP
surfaces. Graphics and business layouts drive the PIA's binary row select and
active-low column inputs. Business symbols close the required base and Shift
contacts. VIA CB2 produces queued audio, and PRG autoload waits until frame 120.

Version-6 saves retain installed firmware, CPU/chip/RAM state, video phase and
pixels, held contacts, pending PRGs and undelivered audio. Foreign board state
and malformed firmware/framebuffer payloads are rejected before installation.
Version 5 is rejected before decoding because it omits the live second PIA.
All six v5 specimens remain immutable and hash-checked. Older versions are
also rejected. Reset uses the firmware restored with the machine.

## Evidence and limits

The original owner has five direct tests; each later owner has seven. Shared tests cover memory decode,
character banks/inversion, paired fetches, retrace wiring, business modifiers,
malformed saves and exact continuations. Current v6 tests compare native fields, sample bits, clocks and final state.
The three later owners retain their frozen native output comparisons, while
legacy state bytes are rejected rather than decoded as current.
A corrupt continuation fails that gate.

Exact original ROM sets reach READY within the existing 120-frame budget.
After `PRINT3+4`, the three later owners match VICE's complete screen RAM and every active
monochrome pixel: 64,000 for each 40-column board and 160,000 for the 8032.
Host palette and presentation borders are outside that comparison. Original
BASIC-2 keyboard tests and PRG autoload pass on the explicitly discrete board.
See the [retained comparison](../../plans/2026-10-31-pet-board-owners/README.md)
and [source PR #2219](https://github.com/emu198x/emu198x/pull/2219).

Both onboard 6520 PIAs are present. Second-PIA data/DDR readback, ATN/SRQ
inputs, disconnected-bus NDAC/DAV/NRFD/EOI resolution and IRQ wiring are
implemented and guest/restore tested. Shared PIA pulse/handshake output phases,
external IEEE-488 devices and cassette remain incomplete. The validated CRTC
rasters use the existing counter stages; full MOS 6545 personality/interlace is
not qualified. Other original static-RAM assemblies and RAM fittings, 60 Hz CRTC models,
SuperPET and other family members remain separate work in #355 and related
issues. Native menu interaction and host audio-device output were not tested
in this slice.

The pinned public browser package still contains the old hybrid PET contract.
The corrected machine pages omit a player until a corrected package is
published and qualified; matching old profile strings alone are insufficient.


## Original PET 2001 assembly 320008

Commodore schematic 320026 sheets 2/3 identifies assembly 320008 with 6540
ROMs, 6550 SRAM and its 8 KiB population. Common logic sheet 320130 provides
the two PIAs, VIA and IEEE drivers. Other original static-RAM assemblies
remain distinct machines. See the [primary schematic and parts-list navigation](https://github.com/stevehill1981/198x/tree/main/reference/by-system/commodore-pet).

This owner fits 8 KiB at 0000–1FFF, retains the last driven bus value in RAM
holes, mirrors the 1 KiB display over 8000–8FFF, and decodes independent
PIA/VIA select lines over E800–EFFF. Multiple selected chips share a read or
receive a write. It has no CRTC. PIA1 CA2 controls blanking; its native image
uses white on black. Later owners retain their mappings and green presentation.

The four runtime firmware parts assemble the original socket images:

| Runtime part | Socket images |
|---|---|
| `basic-1.901447-09-02-03-04.bin` | C000: 901447-09.h1 (or initial 901447-01.h1), C800: 02.h5, D000: 03.h2, D800: 04.h6 |
| `edit-1-n.901447-05.bin` | E000: 901447-05.h3 |
| `kernal-1.901447-06-07.bin` | F000: 901447-06.h4, F800: 901447-07.h7 |
| `characters-1.901447-08.bin` | 901447-08.a2 |

Both C000 revisions reach READY with 7167 bytes free and execute physically
entered `PRINT 3+4`. Tests identify every complete ROM before assembly,
exercise 63 printable contacts plus Space through BASIC 1, run a PRG using
its original zero-page/keyboard-buffer map, and compare exact v6 continuation.
Missing or changed inputs fail the explicit fixture-backed run. No ROM is
distributed.

With the revised C000 ROM, VICE 3.10 (ROM patches disabled) matches all 1,000
screen bytes and every one of 64,000 active monochrome pixels after the same
command. Both C000 revisions produce identical qualified native frames in
Emu198x. A real headless CLI capture also matches the runtime's complete RGBA
frame byte-for-byte. Native menu interaction and analogue output are not
established by this check.

Use `--model commodore-pet-2001-320008-8k` with the assembled firmware directory.
See [source PR #2269](https://github.com/emu198x/emu198x/pull/2269) and the
[qualification evidence](../../plans/2026-11-03-board-qualification-evidence/pet-original/README.md).
This advances #355 and #349; neither broader family/device issue is complete.
