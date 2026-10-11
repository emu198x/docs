# Route PET retrace inputs from the board's vertical-drive signal

Lane: engineering-frontier accuracy. This is a bounded correction to existing
machine wiring, with no new state, snapshot format, dependency or public API.
It is one step of the [CRTC port investigation](2026-10-11-pet-crtc-ports.md);
the separate CRTC status/data-port fault remains to be corrected afterward.

**Prototype gate:** wiring checks pass, but three of five real-ROM keyboard
tests fail. The inputs are a non-CRTC BASIC 2 firmware set. Preserve the patch
and exact results in the [evidence directory](2026-10-11-pet-vertical-drive-evidence/).
Do not merge until the [board/firmware correction](2026-10-11-pet-board-firmware-design.md)
has been agreed and matching configurations pass their checks.

## Root cause

The PET feeds keyboard PIA CB1 from `crtc.in_vertical_retrace()`, a live R6
comparison. VIA PB5 receives its inverse. This gives the two consumers
opposite polarity and uses the visible-area boundary for a sync-derived wire.

Commodore schematics 8032029 revision F and 8032081 revision E establish the
connection: sheet 3 connects VIA PB5 and PIA CB1 to the same VERT DRIVE net;
sheet 10 XORs VSYNC with PULLUP 1, which sheet 8 pulls to +5 V through R2.
With the shown pull-up selection, the wire is inverted VSYNC. Jumper 2's
alternative ground selection is not an emulated board option.

VICE confirms the two connections: `pet.c::pet_crtc_signal` signals CB1 falling
when retrace begins and rising when it ends; `petvia.c::read_prb` clears PB5
during that same interval. The CRTC-backed model explicitly selects
`CRTC_RETRACE_TYPE_CRTC`, which derives retrace from VSYNC. This resolves the
external-wire question; it does not settle VICE's separate status-port use of
the same field.

The original 6502 polling guest captures four traces (40/80 columns × falling/
rising PIA edge), each spanning 80,000 CPU clocks. The 40-column VIA low span
is about 7,245 sampled clocks and the 80-column span about 3,700: the blanking
intervals. The current programmed VSYNC spans are 1,024 and 800 CPU clocks.
Polling quantises the observed transition times; preserve raw clocks and data.

## Change and verification

1. Add a regression to `crates/machine-commodore-pet/src/lib.rs` that samples
   both external inputs over full frames in both display profiles and both
   PIA edge modes. Check VIA readback and PIA interrupt flags against the same
   inverted VSYNC wire, clear flags between samples, and require both levels
   and both transitions. Demonstrate failure before production changes.
2. Feed `!self.crtc.vsync` to PIA CB1. Clear VIA PB5 while `self.crtc.vsync` is
   asserted. Drive the existing `via.pb_in` pins before its tick and use normal
   `via.read` for the port. The new output-mode control exposed a second fault:
   `read_port_b_with_value` returns its argument without applying DDR/output
   selection. Driving the pins restores that existing chip logic and input
   latching; no VIA core or snapshot field is added. Correct the nearby
   comments describing CA1/CB1 and blanking.
3. Rerun the unchanged public polling guest. Check its VIA samples against the
   programmed sync intervals and its PIA reads against the selected edge and
   guest read/clear windows. Compile the unchanged VICE routing stages to
   verify polarity for both signal levels and port-direction settings.
4. Run chip/PET tests, PET runtime snapshots, the real-ROM boot and keyboard
   checks with their fixtures explicitly enabled, Clippy and formatting.
   Publish exact baseline/after evidence and merge only after CI completes.

This corrects the source and polarity of the existing wire. It does not prove
the 80-column character-clock model, add MOS-specific pulse-width programming,
implement CRTC status or light-pen capture, or resolve interlace. Those remain
separate evidence-backed stages of the accuracy work.
