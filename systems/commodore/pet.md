# Commodore PET

Three implemented 32K configurations have fixed machine owners over shared PET
wiring. All three reach BASIC READY and execute typed arithmetic with matching
manufacturer firmware. They do not represent the whole PET family.

| Machine owner | Profile ID | Firmware and keyboard | Native frame |
|---|---|---|---|
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

Version-5 saves retain installed firmware, CPU/chip/RAM state, video phase and
pixels, held contacts, pending PRGs and undelivered audio. Foreign board state
and malformed firmware/framebuffer payloads are rejected before installation.
Version 4 is rejected before decoding because it omits state needed for exact
continuation. Reset uses the firmware restored with the machine.

## Evidence and limits

Each fixed owner has seven direct tests. Shared tests cover memory decode,
character banks/inversion, paired fetches, retrace wiring, business modifiers,
malformed saves and exact continuations. Project-written v5 fixtures compare
the first three resumed native fields, sample bits, clocks and final state.
A corrupt continuation fails that gate.

Exact original ROM sets reach READY within the existing 120-frame budget.
After `PRINT3+4`, all three match VICE's complete screen RAM and every active
monochrome pixel: 64,000 for each 40-column board and 160,000 for the 8032.
Host palette and presentation borders are outside that comparison. Original
BASIC-2 keyboard tests and PRG autoload pass on the explicitly discrete board.
See the [retained comparison](../../plans/2026-10-31-pet-board-owners/README.md)
and [source PR #2219](https://github.com/emu198x/emu198x/pull/2219).

Second PIA, IEEE-488 drives and cassette remain incomplete. The validated CRTC
rasters use the existing counter stages; full MOS 6545 personality/interlace is
not qualified. BASIC-1/chiclet machines, other RAM fittings, 60 Hz CRTC models,
SuperPET and other family members remain separate work in #355 and related
issues. Native menu interaction and host audio-device output were not tested
in this slice.

The pinned public browser package still contains the old hybrid PET contract.
The three corrected machine pages omit a player until a corrected package is
published and qualified; matching old profile strings alone are insufficient.
