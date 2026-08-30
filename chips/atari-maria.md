# Atari MARIA display processor

MARIA is the Atari 7800's video processor. This page distils the current
`atari-maria` crate against Atari's *7800 Software Guide*; it describes what
Emu198x implements, not everything the hardware can do.

Primary provenance:
`reference/by-system/atari-7800/atari-7800-software-guide.txt` and
`reference/by-system/atari-7800/atari-7800-reference.md`.

## A time-limited object system

MARIA has no player/missile or fixed-sprite layer. For each raster it follows a
Display List List (DLL), then a Display List (DL), and uses DMA to compose Line
RAM from horizontally positioned graphics pieces. Later pieces overwrite
earlier ones. The hardware therefore limits objects by the time available to
load one scanline, not by a fixed object count.

The real chip double-buffers Line RAM and builds a line one raster before it is
shown. Emu198x represents the current line as a 320-pixel colour-index buffer,
then resolves it through the NTSC or PAL palette into an ARGB32 framebuffer.

## Display structures

A three-byte DLL entry contains the DLI flag, two holey-DMA flags, a four-bit
`OFFSET`, and the display-list address. `OFFSET + 1` is the zone height, and
the offset also selects successive graphics pages down the zone.

Within the display list:

- A four-byte header supplies graphics address, palette/width, and horizontal
  position. A zero second byte terminates the list and returns time to SALLY.
- A five-byte extended header can select indirect addressing and a per-entry
  160/320 write mode.
- Direct mode reads sequential graphics bytes with the zone's page offset.
- Indirect mode reads character numbers and combines them with `CHBASE` and the
  zone offset. `CW` optionally fetches a second graphics byte per character.
- Holey DMA makes reads from selected address windows transparent.

## `CTRL` (`$3C`)

| Bits | Name | Current meaning |
|---|---|---|
| 7 | CK | Colour kill: retain luminance and force hue zero. |
| 6–5 | DM | DMA mode; `10` and `11` enable display DMA. |
| 4 | CW | Fetch two graphics bytes per indirect character. |
| 3 | BC | Border control; not separately modelled yet. |
| 2 | Kangaroo | Disable transparency; not implemented yet. |
| 1–0 | RM | Read-mode selection; the full mode matrix is incomplete. |

This mapping fixed the 7800's black-screen failure. The old model treated bit
7 as DMA enable and bit 6 as colour kill. Games setting `DM=10` therefore got
no display-list walk and no DLI; their NMI-driven wait counters never advanced.

## Implemented graphics boundary

- **160A** — four 2-bit pixels per byte, doubled horizontally. Zero is
  transparent; values 1–3 select the entry's three palette colours.
- **320A** — eight 1-bit pixels per byte. Zero is transparent; one selects the
  first colour in the entry's palette.
- **Still missing** — 160B, the remaining 320B/C/D combinations, Kangaroo
  transparency, and distinct border-control behaviour.

MARIA also implements eight three-colour palettes, `BACKGRND`, colour kill,
WSYNC, vertical-blank status, Display List Interrupts, direct and indirect
fetches, holey DMA, and PAL/NTSC output palettes.

## Register surface

| Address | Register | Current behaviour |
|---|---|---|
| `$20` | BACKGRND | Line background and frame-start border colour. |
| `$21`–`$3F` | P0C1–P7C3 | Three colours for each of eight palettes, interleaved with control registers. |
| `$24` | WSYNC | Halt SALLY until the next scanline. |
| `$28` | MSTAT | Bit 7 reports vertical blank. |
| `$2C`, `$30` | DPPH, DPPL | Display List List pointer. |
| `$34` | CHBASE | Indirect-character graphics base. |
| `$38` | OFFSET | Reserved by Atari; writes are ignored. |
| `$3C` | CTRL | Output and graphics-mode control. |

## Timing boundary

The machine invokes MARIA once per 228-colour-clock scanline. MARIA walks the
lists and returns a DMA budget; the machine withholds CPU ticks for that many
slots at the start of the line. WSYNC extends the halt to the next line, and a
zone DLI drives SALLY's NMI.

This preserves the important relationship—more display work costs more CPU
time—but it is still scanline-batched. MARIA reads memory through a closure
rather than owning visible bus pins, so exact fetch placement and arbitration
remain accuracy work.

## Sources and precedent

- Atari, *7800 Software Guide* — hardware model, DMA relationship, structures,
  registers, and timing facts. Primary-library path given above.
- MAME `maria.cpp` — implementation precedent for DLL fields, indirect
  addressing, and `CW`.
- MiSTer Atari 7800 `DMA.sv` — implementation precedent used during the CTRL
  and display-entry correction.
