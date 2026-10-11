# Give PET profiles the hardware their firmware expects

Proposal; awaiting approval. Lane: engineering-frontier accuracy. This extends
the existing PET machine and runtime, without a new dependency or bus abstraction.

The current PET is a hybrid: both profiles have a CRTC, but their shared firmware
contract requires an 8 KB BASIC image. The installed test set is BASIC 2 with a
non-CRTC editor. Correcting the board's vertical-drive wiring exposes that
mismatch. We must validate coherent machines before shipping the signal fix.

## Evidence

The installed firmware hashes match these original Commodore parts, also
identified by the vendored MAME `src/mame/commodore/pet.cpp` ROM declarations:

| Input | Identification | SHA-1 |
|---|---|---|
| BASIC, first 4 KB | 901465-01, BASIC 2 at C000 | `3622111f486d0e137022523657394befa92bde44` |
| BASIC, second 4 KB | 901465-02, BASIC 2 at D000 | `1bc0ebf27c9bb62ad71bca40313e874234cab6ac` |
| KERNAL | 901465-03, BASIC 2 | `38742bdf449f629bcba6276ef24d3daeb7da6e84` |
| Editor | 901447-24, 40-column graphics keyboard, no CRTC | `5e5502ce32f5a7e387d65efe058916282041e54b` |
| Each 2 KB half of character input | 901447-08, BASIC 1 character set | `3e067cc621e4beafca2b90cb8f6dba975df2855b` |

The original [Commodore ROM images](https://www.zimmers.net/anonftp/pub/cbm/firmware/computers/pet/index.html)
are available for comparison. The downloaded BASIC 4 parts 901465-23/-20/-21,
KERNAL 901465-22, 40-column editor 901498-01 and character ROM 901447-10 all
match the corresponding MAME declarations. There are multiple archived
901474-04 editor dumps; the `_alt` image matches MAME's
`66887061b6c4ebef7d6efb90af9afd5e2c3b08ba`. Do not identify an editor by its
filename alone. The download manifest records each distinct image.

`PetRuntime::set_roms` accepts exactly 8 KB of BASIC and 4 KB of characters.
`Pet::mem_read` leaves B000–BFFF unmapped. Thus the advertised CRTC profiles
cannot load the conventional three-bank BASIC 4 set through the runtime.
Both profiles use the graphics-keyboard mapping; VICE's 8032 model selects
the business keyboard. These are independent of the pending retrace patch.

The baseline passes all five firmware keyboard tests. With the pending
vertical-drive correction, two pass and three fail. The diagnostic trace
shows the editor still printing its banner at frame 120; it eventually
produces the expected `AB C` text by frame 260. This establishes delayed output
under the mismatched setup, not correct timing for a real non-CRTC PET.
The failing assertions and unmodified tests must remain part of the evidence.

VICE `pet.c::pet_crtc_set_screen` uses discrete retrace for non-CRTC models
and CRTC retrace for later models. For 80 columns it sets
`CRTC_HW_DOUBLE_CHARS`; `crtc.c` doubles characters per CRTC address, rather
than doubling the CRTC tick rate. Our 80-column path ticks the CRTC twice and
fetches one character each time. Resolve that discrepancy against the board
schematics and original editor execution before implementation.

## Recommended scope

Represent three concrete configurations through the existing runtime-owned
catalogue and machine-local hardware configuration:

1. A 32 KB PET 2001N/3032-class machine: discrete video, BASIC 2 and graphics
   keyboard. It provides an explicit home for the existing BASIC/editor set,
   with the correct 2 KB character ROM. It is not the original BASIC 1/chiclet
   PET 2001.
2. A CRTC 4032-class 40-column, 50 Hz configuration: BASIC 4, graphics keyboard,
   editor 901498-01 and its actual board timing.
3. A CRTC 8032-class 80-column, 50 Hz configuration: BASIC 4, business keyboard,
   a precisely identified 901474-04 editor and paired video fetches.

Keep the existing `commodore-pet-40col` and `commodore-pet-80col` IDs assigned
to their advertised CRTC classes, with explicit display names. Add
`commodore-pet-2001n-32k` for the non-CRTC configuration. ROM hashes identify
test provenance; they must not secretly select machine hardware at runtime.
Use model-specific firmware sources so selecting 80 columns cannot silently
reuse the non-CRTC graphics editor. Preserve input files unchanged.

Extend the existing machine state with the selected board and its native video
counter/fetch state. The discrete board must advance its actual counters and
signals on the machine clock; do not emulate it by hiding a programmable CRTC.
The CRTC configurations retain the existing chip stages. Derive video RAM and
character addressing from board wiring, including inverse video, character-set
selection and raster rows beyond an eight-row glyph. Keep CPU, VIA and PIA on
their pin-driven native cadence.

Match framebuffer geometry to each board's displayed raster. The current fixed
200-line active height cannot represent 25 ten-line character rows. Verify the
last displayed row and every glyph raster row, including blank rows, instead
of cropping output to preserve the current dimensions.

Advance PET snapshots from version 4 to version 5 and reject version 4 before
decoding its payload. Preserve board identity and every in-flight video phase;
reset, replacement and restore must agree on firmware and board selection.
This changes the public machine configuration/constructor and extends the
runtime model enum and firmware contract. Update all callers atomically.

## Alternatives

- **Recommended: extend the existing PET stages for these three configurations.**
  It corrects the current claims and preserves the existing BASIC 2 use case.
- Correct only the CRTC profiles and retire BASIC 2 compatibility. This is
  smaller but discards a working use case instead of representing its hardware.
- Keep the hybrid and lengthen firmware test delays. Reject: a passing test
  would still describe a hardware/firmware combination we do not claim to model.

## Implementation and gates

Deliver this as small tested commits on one branch; merge only when all three
configurations meet their gates. Do not publish an intermediate snapshot v5
before its final state layout is settled.

1. Preserve the pending patch, before/after polling traces, failing firmware
   output, fixture identities and reference sources. Finish schematic checks
   for the discrete board, CRTC clocks and character wiring. Write executable
   reference comparisons for counters, sync and paired fetches; establish
   failing controls before modifying those paths.
2. In `crates/machine-commodore-pet/src/lib.rs`, introduce the explicit hardware
   selection and extend its native video stages (a local `video.rs` module if
   needed). Map BASIC at C000 for BASIC 2 and B000 for BASIC 4; implement the
   model's video RAM decode and character addressing. Apply the existing
   vertical-drive patch only to the corresponding CRTC wiring. Add meaningful
   machine tests in `tests/board_video.rs`, with CPU-executed I/O guests.
3. Extend `crates/machine-commodore-pet/src/input.rs` and the existing keyboard
   state path for the business matrix. Update runtime `input.rs` so characters
   requiring modifiers produce real key combinations. Test the matrix against
   reference wiring and type through each original editor.
4. Update `crates/runtime-commodore-pet/src/profiles.rs` and `runtime.rs` for
   the three configurations, model-specific ROM lengths and sources, and
   evidence-backed clock/frame metadata. Update existing catalogue/program
   tests. Existing IDs must resolve consistently through CLI, UI and runtime.
5. Update `crates/runtime-commodore-pet/src/snapshot.rs` and
   `tests/snapshot_roundtrip.rs`: round-trip each video phase, interrupt edge,
   selected keyboard and ROM bank; compare subsequent bus, pixel and audio
   results with uninterrupted execution. Reject v4 without changing the live
   machine. Check reset and replacement after restore.
6. Run the existing `keyboard_type.rs`, `rom_boot.rs` and
   `synthetic_firmware_boot.rs` tests against explicit matching firmware sets,
   then extend them to all three configurations. Boot must reach READY within
   a reference-measured time bound; typing must finish with the expected
   screen result. Do not substitute a fixed longer delay for that evidence.
   Check pixel output as well as screen RAM so a wrong character ROM cannot
   pass by printing the right character codes.
7. Run affected chip/machine/runtime checks, Clippy, formatting and required
   CI. Update current PET status and issue #355 from measured results. Keep
   the separate CRTC status-port investigation open until its own checks pass.

No new dependencies, CPU protocol changes or general emulator architecture
are proposed. BASIC 1/chiclet models, other RAM sizes, 60 Hz CRTC variants,
IEEE-488/second PIA completion and full 6545/interlace accuracy remain separate.
This is progress on #355, not grounds to close its wider family scope.
