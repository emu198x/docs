# SMS raster phase: confirmed failure and calibration work

Engineering-frontier investigation for [source issue #212](https://github.com/emu198x/emu198x/issues/212).
The interrupt and V-counter events are attached to the wrong active-picture
boundary. No production timing change is included or approved by this record.

## Evidence

[Evidence directory](2026-10-11-sms-raster-phase/) contains original guest
generators, 40 IRQ-case observations, eight interrupt-disabled polling controls,
per-T-state Emu198x traces, reference I/O traces and a failing chip probe.
`metadata.json` pins both source revisions and the validation scope;
`SHA256SUMS` covers every retained evidence file.

The primary observation record is
`198x/reference/by-topic/vdp-sms/2026-raster-phase-observations.md`.
It distinguishes original hardware measurements from MAME source inspection
and live Genesis Plus GX results. In particular, MAME's SMS HINT position is
one pixel later than the published original-NTSC-SMS measurement. Choosing
an exact edge still requires calibration; matching Genesis Plus GX's
instruction-level timestamps alone would not settle it.

The live comparison finds an H-latch displacement of 16 counter positions
(32 dots modulo a line) in all 40 IRQ cases. R10 reloads 7/31/63/191 and
inserted NOP counts 0/1/4/16/32 cover both PAL and NTSC. The wrap calculation
must remove the unused H-counter codes $94–$E8 before subtraction.

More decisively, Emu198x raises R10=31 IRQs at active-picture lines
32,64,96,128,160,192, dot zero, while V still reports the preceding line.
At active line 31, V reports 30. MAME schedules the first IRQ before active
line 31. The earlier matching guest V-count rings concealed this error.

`chip_phase_probe.rs` checks all 342 H-counter positions for each SMS1/SMS2
and PAL/NTSC combination. All 1,368 H controls pass, while eight independent
V/IRQ phase checks fail. Baseline exit is 101, with the literal failure:

```text
1368 horizontal controls passed; 8 phase failures
assertion `left == right` failed: VDP phase disagrees with reference
  left: 8
 right: 0
```

The reference trace host forwards the original core's I/O callbacks and logs
their timestamps. Traced/untraced 61-frame runs have identical RAM and PPM
bytes in both regions. TH-high occurs 75 Z80 T states after the reference
line-scheduler origin. Emu198x's trace records it 71 T states after its IRQ
event; these are different CPU observation conventions, not proof of a
four-cycle Z80 defect.

## Reproduce

Use the unmodified core build and runners described in
[the initial investigation](2026-10-11-sms-raster-timing.md). Place the added
files beside those runners in `/private/tmp/198x-sms-raster-evidence`.

1. Run `python3 sweep_counters.py` and `python3 sweep_poll.py`. Each subprocess
   must succeed and return 8 KiB RAM with nonempty observations. The scripts
   retain ROMs, RAM, logs and frames locally, and write JSON/CSV summaries.
2. For H-distance comparison map codes at or above $E9 to `code - 85`, leave
   the others unchanged, then subtract modulo 171. Every IRQ row gives 16.
   V-ring order is not an absolute frame-phase comparison: the two frontends
   stop at different boundaries. Long polling delays can skip transitions.
3. Build `machine-sega-master-system` with Cargo JSON output; use the reported
   matching `machine_sega_master_system`, `emu198x_zilog_z80` and `sega_vdp`
   rlibs when compiling the Rust runners. The recorded build used Rust 1.99.0
   and edition 2024. Run `emu_timing_trace counter31.sms ntsc-u` (or `pal`):
   it warms up for 60 frames, then traces one frame through public APIs.
4. Compile `reference_timing_trace.c` with `-DLSB_FIRST`, the reference's
   `core/z80` and libretro include directories, and the existing dylib. Run
   from its dylib directory with ROM, region, output prefix and `61`. Compare
   its RAM and PPM byte-for-byte to an untraced `reference_host` run of 61
   frames. Both comparisons passed for both regions.
5. Compile/run `chip_phase_probe.rs` against the matching `sega_vdp` rlib.
   On the recorded source it must exit nonzero with eight phase failures and
   1,368 successful controls. Its IRQ expectation is explicitly MAME's dot
   schedule, not a claim of subpixel hardware accuracy.

## Next bounded work

1. Calibrate CPU I/O sampling and IRQ observation against the published
   hardware windows, MAME and Genesis Plus GX. Keep the unit conversions
   explicit; resolve the small edge differences before selecting constants.
2. Design the correction in existing `SegaVdp` dot/counter stages, retaining
   active-coordinate rendering and the existing H-counter formula. Separate
   line-counter evaluation, V-count update, frame flag and IRQ delivery.
   Check status reads and R10 writes either side of each event.
3. If a future-IRQ latch or native-clock phase is required, request agreement
   for its concrete design and snapshot change before implementation. Inspect
   both serde and manual chip-state encoding. Coordinate SMS/GG version 8→9
   with the separately pending PSG designs; never reuse a shipped version.
4. Add permanent before/after regressions, live guest checks and timed save
   continuation tests; run the focused SMS/GG suite, Clippy and formatting.
5. Obtain and compare Sonic/Out Run captures before closing #212. Alex Kidd's
   existing boot smoke and these synthetic tests do not replace that gate.

The tested source includes the colour correction from
[PR #1726](https://github.com/emu198x/emu198x/pull/1726), which is currently
closed without merging. Its branch is preserved; no reopening is assumed.
