# MSX family

The family runtime has nine named MSX1/MSX2 board owners. Generic MSX presets
are retired; choose a physical board and its matching firmware. The
[source profile catalogue](https://github.com/emu198x/emu198x/blob/main/crates/runtime-msx/src/profiles.rs)
provides the current IDs, fitted memory layouts and firmware requirements.

## Sony HB-10P PU-37

The identified original 32 KiB Sony ROM reaches `MSX BASIC version 1.0`,
`28815 Bytes free` and `Ok`. Keyboard-entered `PRINT 3+4` returns `7`.
The regression verifies the entire ROM identity before execution, checks
native framebuffer glyphs for the banners and result, and compares exact
continued output after restore. C-BIOS checks alone do not establish this
manufacturer-specific result.

The board has 64 KiB of physical RAM in slot 3. Slot-0 C000–FFFF selects the
same RAM, rather than adding another 16 KiB. Its S3527 has no A2 address input:
PPI and PSG ports have their documented A2 aliases, and VDP strobes cover
98–9F. Guest regressions exercise both directions of the RAM mirror, port
aliases and neighbouring non-alias controls. Restore and reset reattach the
immutable board decoder; other owners keep their own decoding.

Sony service documentation identifies a Toshiba T6950 video part and Yamaha
S3527 integrated SSG. The current implementation uses common TMS9918-family
video and AY/PPI components. The decoding and BASIC evidence do not qualify
all T6950 timing, integrated-SSG differences or analogue colours. Printer
peripherals and cassette media handling also remain incomplete.

Primary source and wiring audit:
[PU-37 manufacturer evidence](https://github.com/stevehill1981/198x/blob/main/reference/by-system/msx/sony-hb10p-pu37-decoding.md).
Original-ROM tests are `runtime-msx/tests/sony_hb10p_boot.rs`; captures and
verification logs are retained with the
[qualification evidence](../../plans/2026-11-03-board-qualification-evidence/).

## Native saves

HB-10P writes and requires v11. Its v10 saves are rejected before decoding or
mutation under the approved corrected-execution contract. The other eight
named boards retain v10, including their frozen state bytes and native
video/audio/clock continuations. The original HB-10P v10 specimens remain
immutable historical evidence. Foreign board topology is rejected before
changing the receiver.

## Shared hardware and remaining work

The runtime covers primary/expanded slots, cartridge mappers, keyboard and
joystick input, native saves and shared debugging. MSX2 owners add V9938 video,
SUB-ROM, RAM-mapper and RTC wiring. Sound cartridge regressions cover SCC,
FM-PAC and Sound Cartridge paths; this is separate from manufacturer-specific
SSG qualification. External disk hardware and the CX5M SFG-01 remain distinct
board work.

Exact HB-10P T6950 timing, integrated sound and port-direction qualification
remain tracked in [#2270](https://github.com/emu198x/emu198x/issues/2270).
