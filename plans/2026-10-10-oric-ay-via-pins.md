# Drive the Oric AY bus from the VIA outputs

Lane: engineering-frontier accuracy. Bounded correction to the existing board
wiring; no new chip stages, dependencies, public fields or snapshot schema.

## Result

The public-pin probe improves from eight failures in nine combinations to
zero. Four new board regressions fail before the correction and pass after
it; the existing fixed-control test remains green. Six new tests cover those
board cases, a CPU-executed guest and save/restore at 320 guest-clock positions.
The snapshot test compares the next 32 clocks, AY state, buffered audio and
complete serialized state against an uninterrupted machine.

All 104 tests in the machine, runtime, VIA and both AY crates pass. Both
strict real-ROM boot/display tests pass. Warnings-denied Clippy and workspace
formatting pass. Logs, probes, exit codes and artifact identities are retained
in the [adjacent evidence folder](2026-10-10-oric-ay-via-pins/).

A real Atmos ROM boots and executes keyboard-entered `PING` on the baseline
and corrected library. The 785 watched AY writes, final framebuffer and
returned 1,024 audio samples are byte-identical. The probe requires non-silent
audio and an envelope-register write, so an inert workload cannot pass. The
audio API returns a bounded buffer: this comparison is of that final window,
not every sample generated during the workload. No ROM or generated media is
included in the evidence.

The implementation preserves the existing undriven-low convention and
CPU-period observation granularity. It does not establish floating voltages
or sub-cycle AY timing, and it does not implement cassette recording (#342).

## Reproduction and cause

On source `831a02b0`, the public-pin probe arms CA2 and CB2 in all nine
combinations of handshake-high, pulse-idle-high and fixed-high. Every row has
both pins driven high, so each must select AY register 7. Eight rows fail:
the subsequent fixed-mode data transfer writes register 0 instead, and two
rows also emit a premature data write. Fixed-high/fixed-high is the control.

`process_ay_bus` infers each level from PCR's fixed-high encoding. The chip
already exposes its real output level and drive state. The board also misses
changes caused by port reads, port B writes, VIA ticks and tape CB1 edges.

The original Oric schematic connects CA2 to BC1 and CB2 to BDIR. General
Instrument's AY-3-8910/8912 data-manual bus table establishes the four phases
with BC2 high. MAME `update_psg` consumes the control levels; Oricutron's
`via_main_ca2pulsed`, `via_main_cb2pulsed`, handshake callbacks and
`ay_modeset` propagate those changes beyond PCR writes.

## Implementation and verification

1. Add failing regressions in `crates/machine-oric-atmos/src/lib.rs` for the
   nine idle-high combinations, read-triggered CA2 transfer, CB2 port-B
   handshaking and pulse release through the machine clock.
2. Resolve driven CA2/CB2 from existing VIA output fields. Retain the existing
   undriven-level convention; this fix does not establish floating voltages.
   Notify the existing AY bus handler when control levels change across each
   board mutation. Keep ordinary PCR/port-A write delivery and avoid repeated
   writes on unchanged clocks, which would restart the AY envelope.
3. Exercise a CPU-driven guest and snapshot replay across the relevant phases
   in the existing machine/runtime tests. Compare future AY/audio behaviour.
   Stop for design review if saved state beyond the existing VIA/AY state is
   needed. Do not change the chip's own strobe phase or CPU/VIA tick order.
4. Run machine/runtime/AY/VIA tests, strict real-ROM Oric checks, warnings-denied
   Clippy and formatting. Re-run the public probe; retain its red/green rows
   and exact identities. Confirm a fixed-control ROM workload keeps its
   behaviour and audio. Merge after CI passes.

## Sources and reproduction

The [original Oric schematic](https://homepages.uni-regensburg.de/~hep09515/oric1/oric1-1p.gif)
wires VIA CA2/CB2 to AY BC1/BDIR. The [General Instrument data manual](https://map.grauw.nl/resources/sound/generalinstrument_ay-3-8910.pdf),
PDF page 2 (printed 5-19), gives the bus-control table. Primary wiring
provenance is recorded in the umbrella's `reference/by-system/oric/`.
Reference implementation paths are
`emulators/multi-system/mame/src/mame/tangerine/oric.cpp` and
`emulators/oric/oricutron/{via.c,8912.c}`; these are corroboration, not new
hardware authority.

From the source repository:

```sh
cargo test --release -p machine-oric-atmos --lib ay_bus_
cargo test --release -p machine-oric-atmos -p runtime-oric-atmos \
  -p mos-via-6522 -p gi-ay-3-8912 -p emu198x-gi-ay-3-8910
EMU198X_ORIC_ATMOS_ROM=/Users/stevehill/.emu198x/roms/oric/oric.rom \
  EMU198X_STRICT_FIXTURES=1 \
  cargo test --release -p machine-oric-atmos --test bios_boot -- --ignored --nocapture
cargo clippy -p machine-oric-atmos -p runtime-oric-atmos --all-targets -- -D warnings
cargo fmt --all -- --check
cargo build --release -p machine-oric-atmos
rustc --edition=2024 -C opt-level=3 -C lto=thin \
  ../docs/plans/2026-10-10-oric-ay-via-pins/ay-handshake-probe.rs \
  -L dependency=target/release/deps \
  --extern machine_oric_atmos=target/release/libmachine_oric_atmos.rlib \
  -o /private/tmp/oric-ay-pin-probe
/private/tmp/oric-ay-pin-probe
```

Compile `rom-audio-probe.rs` with the same flags and run it with a fresh
output prefix for each library version. Compare all three nonempty files
(`.audio`, `.frame`, `.writes`) byte for byte. Their sizes and SHA-256 hashes
are in `rom-comparison.json`. The baseline public probe must return 1;
the corrected probe must return 0. The red regression run predates the two
CPU/snapshot tests. An initial snapshot-test scaffold used a nonexistent
`clone` method and failed to compile; the retained full-suite result uses
an independently constructed uninterrupted machine instead.
