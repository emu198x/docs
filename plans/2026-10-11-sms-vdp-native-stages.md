# SMS VDP counter and interrupt stages

Proposed engineering-frontier correction for source issue #212. Approval is
required for the clock-stage extension and SMS/GG snapshot 8→9. No production
timing code has changed yet.

[Evidence directory](2026-10-11-sms-vdp-native-stages/) includes both runners,
four completed-page captures, raw RAM and all 64 result comparisons. Metadata
pins the external cartridge hash and download; its ROM/source are not bundled.

## Confirmed trigger and cause

The earlier [phase investigation](2026-10-11-sms-raster-phase.md) found late
line interrupts and stale V counts. FluBBa's published SMS VDP Test 1.31 now
reproduces six failures on the same unmodified cartridge in both PAL and NTSC:
V-counter change timing, frame IRQ V/H count, line IRQ V/H count and VINT flag
H count. Genesis Plus GX passes all sixteen tests on this page in both regions.
The ten passing Emu198x controls include the full H-counter sequence, its TH
latch behaviour, counter/port mirrors and retained VINT flag.

The cartridge's boot display lasts 128 frames. The runners press button 1
on frames 200–204 to select the SMS tests and 400–404 to advance to the timing
page; capture is at frame 1000. Both pages and the final test rows were inspected.
RAM at $C914–$C923 supplies the sixteen results; test 21 identifies PAL/NTSC
with 1/2, zero means pass for the others, and $FF means failure. The completed
screen is a positive execution check, rather than interpreting untouched zero
RAM as passed tests.

The archive's source tag says 1.30 despite the distribution being labelled
1.31. The unmodified distributed binary is the test input; it was not rebuilt
from the source. The frame-V-count and first frame-H-count comparison byte
sequences were checked in the binary at $0ABC and $0B12 respectively. Source
inspection is supporting evidence, not a claim of a reproducible binary build.

Source `205bfd85db9cf91bd7489e1d4dec7d7a32b8ef40` combines line-counter work,
V-count update, frame status and interrupt delivery in `advance_line()`.
`update_interrupt()` derives the frame IRQ directly from the status flag.
The machine services the VDP only after CPU edges, accumulating whole pixels.
Those paths cannot independently represent the measured event edges.

The original NTSC hardware report distinguishes frame and line IRQ edges by
one oscillator period, with two periods per pixel. This rules out treating
all such events as a single whole-dot update. Exact event positions must also
pass the published guest tests: references use different coordinate origins
and CPU I/O callback positions. We will not shift the H-counter formula to
cancel an IRQ scheduling error.

## Approaches

1. Move the existing combined update to an earlier dot. Small, but still
   combines events that hardware distinguishes and does not preserve an
   underflow waiting to become a CPU-visible interrupt.
2. **Extend the existing cadence and VDP stages (recommended).** Use the
   SMS oscillator as the local scheduler quantum and retain the missing
   event state in the existing chip. Keep the current CPU pin interface,
   framebuffer geometry and dot-based renderer.
3. Replace the SMS driver/VDP with a new event scheduler. Wider than needed;
   the existing native-clock cadence can carry this correction.

## Bounded design

- In `crates/common-z80-machine/src/lib.rs`, add a default no-op chip hook
  called on every scheduler quantum before the CPU samples its inputs. The
  existing dispatcher and other machines retain their current cadence.
- In `crates/machine-sega-master-system/src/lib.rs`, select three oscillator
  periods per Z80 T state, with CPU edges at phases zero and one. This matches
  the documented one-period high/two-period low SMS clock. Drive the VDP at
  each oscillator period through the new hook. PSG stepping and public runtime
  tick units remain CPU T states. Test that no oscillator period is omitted.
- In `crates/sega-vdp/src/lib.rs`, add a native oscillator tick entry point.
  Retain `dot` for rendering and add its half-dot phase. Separate line-counter
  evaluation, V-count update, line-IRQ assertion, frame-IRQ assertion and
  frame-status visibility. Preserve a scheduled line IRQ separately from the
  existing visible pending latch, and a frame-IRQ latch separately from the
  status bit. Status reads clear the visible interrupt state without erasing
  an event whose delivery time has not arrived. Register enables gate delivery
  without losing the underlying event.
- Keep `tick()` as one pixel's two oscillator periods, and make the scanline
  convenience route traverse the same stages. Preserve pending VRAM accesses,
  sprite evaluation and line rendering; do not introduce a second timeline.
- At the machine boundary, validate the V/H counter data seen while the CPU
  holds an I/O read. If the existing early callback freezes a changing V value,
  drive these side-effect-free counter outputs from the active pins until the
  CPU samples them. Destructive status/data reads must remain single strobe
  transactions; do not poll them repeatedly to obtain the desired result.
- Save the new phase and pending stages in both serde and manual VDP state.
  Advance `crates/runtime-sega-master-system-class/src/snapshot.rs` from 8
  to 9, rejecting version 8 before decoding the payload. SMS and Game Gear
  share this envelope. Coordinate with the separately pending PSG designs:
  share version 9 only if the changes are combined before it ships.

The selected event positions will be documented per chip variant and validated
against hardware windows and the live cartridge. The design does not authorise
changing CPU instruction timing to force a VDP test result, changing the
H-counter origin, or including horizontal-scroll latching without its own
reproduction. A discrepancy on those paths must be explained separately.

## Work and verification

1. Retain the external cartridge's URL and SHA-256, the input scripts, RAM
   results and completed-page captures. Do not bundle the unlicensed ROM or
   its source. Source and expected results come from the downloaded archive,
   not the newer GitHub source tree. Re-run the existing ZEXDOC gate as the
   test author's CPU prerequisite; it is currently running, not yet passed.
2. Extend and test the cadence hook at divisors 2, 3 and existing slower-clock
   cases. Verify both CPU edges, every chip quantum and identical cadence for
   existing users. Keep this as one small validated commit.
3. Extend the SMS/VDP stages and snapshot together. Add phase regressions under
   `crates/sega-vdp/tests/` and guest tests under
   `crates/machine-sega-master-system/tests/`. Include all R10 values at line
   boundaries, both sides of timed status reads/register writes, PAL/NTSC and
   SMS1/SMS2/Game Gear controls. Use the existing dot/H-count control suite.
4. Restore before/between/after the new events and compare subsequent IRQs,
   CPU execution, V/H reads, framebuffer and audio to uninterrupted execution.
   Verify both state encodings and explicit rejection of version 8.
5. Re-run the sixteen hardware-test rows and the 40-case original guest sweep,
   preserving baseline failures. Exact agreement with an instruction-batched
   reference is not a substitute for the hardware test's expected values.
6. Run focused common-Z80, VDP, machine, shared-runtime, SMS and GG tests,
   Clippy and formatting. Run Alex Kidd as a smoke control. Only then publish
   a source PR and apply exact-head checks before merging.
7. Keep #212 open until the requested Sonic/Out Run reference captures are
   obtained and compared. No cartridge image for those games is assumed.

The local colour correction's PR #1726 remains closed and unmerged. Before a
new source PR, use current main as its base and keep colour changes separate
unless the user explicitly authorises reopening that PR.
