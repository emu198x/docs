# Motorola 6845 and Hitachi HD6845S

The shared CRTC drives addresses and timing for the BBC Micro, Commodore PET and
Amstrad CPC. It does not generate pixels. Each machine turns its live memory
address, raster address and display-enable outputs into video.

## Manufacturer evidence

The primary library records Motorola's **MC6845 CRT Controller**, 1977, in
`reference/by-topic/crtc-6845/1977-motorola-mc6845-crtc.source.json`.
PDF page 11 contains the register table; pages 12–15 describe timing, interlace
and cursor control. The source PDF was reacquired with the recorded SHA-256
`84ae68617c23e3b3057dce86f4a04a5be5d890d108bce8e9bb928bfdd2759dcf`.

Hitachi's **8/16-Bit Peripheral LSI Data Book**, U70-A, August 1987, contains the
HD6845R/S chapter on printed pages 139–179 (PDF pages 150–190). Register details
are on printed 147–150; the R/S comparison is on 178–179. Its provenance is
`reference/by-topic/crtc-6845/1987-hitachi-peripheral-data-book.source.json`,
SHA-256 `6de0487818bba1aa1b39cd0bcadb8c118cb5f0d98b8ae49df85fb4ee2ae8ba92`.
These page numbers refer to the complete data book, not the separate 44-page
datasheet already catalogued in the library.

The curated library reference is
`reference/by-topic/crtc-6845/6845-registers-and-signals.md`.

## Registers and timing

| Registers | Function |
|---|---|
| R0–R2 | Horizontal total minus one, displayed characters, sync position |
| R3 | Horizontal pulse width; HD6845S also programs vertical width |
| R4–R7 | Vertical total minus one, extra scanlines, displayed rows, sync row |
| R8 | Interlace mode; HD6845S also provides display and cursor skew |
| R9 | Maximum raster address; interlace programming differs by part |
| R10–R11 | Cursor start/end raster and steady/hidden/16-field/32-field modes |
| R12–R13 | Display start address, 14 bits |
| R14–R15 | Cursor address, 14 bits |
| R16–R17 | Read-only light-pen address, 14 bits |

In ordinary non-interlace operation, a line has R0 + 1 character clocks and a
frame has `(R4 + 1) × (R9 + 1) + R5` scanlines. Successive rasters repeat a
character row's memory addresses while RA chooses the glyph or bitmap raster.

The original MC6845 reads back R14–R17; HD6845S also reads R12–R13. Both program
horizontal pulse widths of 1–15 character clocks. Motorola specifies no HSYNC
for zero; Hitachi excludes zero from valid horizontal-width programming.
Motorola's vertical pulse is fixed at 16 scanlines. HD6845S uses R3's high nibble
for 1–15 scanlines, with zero encoding 16.

Interlace sync requires a half-line displacement between fields. Sync-and-video
mode also changes RA parity. Hitachi explicitly distinguishes R/S vertical
register units, row-height programming and cursor field behaviour in this mode;
one shared interlace formula cannot establish complete variant accuracy.

## Implementation boundary

At source commit
[`10892b4`](https://github.com/emu198x/emu198x/blob/10892b445182cc5d8106cff7cd142f9a64d4cf10/crates/motorola-6845/src/lib.rs),
the core ticks once per character clock. BBC and CPC select `Hd6845s`; PET uses
the default `Mc6845` personality. All three consume live CRTC addresses. BBC
applies separate bitmap/teletext decoding and bitmap wrapping in its machine
crate. The personality selection does not establish a complete MOS 6545 model
or coverage of every CPC CRTC type.

The core implements variant readback, R0 = 255 wrapping, RA field parity and
cursor blinking. It still lacks half-line sync displacement, chip-level skew,
light-pen capture and hardware write protection for R16–R17. R7 = 0 does not
trigger vertical sync. Register write masks and interlaced vertical programming
also need further work. [Issue #166](https://github.com/emu198x/emu198x/issues/166)
tracks the interlace/skew boundary.

A [public-output probe](../plans/2026-10-11-6845-sync-evidence/README.md) finds
62 failures across 64 sync-width cases: nonzero horizontal and all vertical
pulses are one interval short, and width one disappears. Both zero-horizontal
controls pass. The existing 23 chip tests pass despite this fault. The source
starts a pulse and advances its width counter at the same boundary, consuming
an interval before it has elapsed. The probe uses fixed registers and ordinary
non-interlaced lines; it does not validate live width changes or pulses crossing
vertical adjustment.

The reference documentation closes the evidence gap in
[issue #168](https://github.com/emu198x/emu198x/issues/168). It does not certify
the remaining timing or variant behaviour.
