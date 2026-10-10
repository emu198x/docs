# MARIA native clock contract and full-clock reference

The first approved implementation slice is committed as `7ffb356b` on
`emu198x/emu198x:fix/maria-timed-dma`. It is intentionally unmerged. Issue #197
remains open: the old bulk renderer still loses consecutive interrupts and
uses the wrong descriptor boundary. Version 6 must not ship until the staged
DMA correction is complete.

## Clock-contract correction

The machine now counts native oscillator periods. Existing TIA clocks occur
every four periods; existing CPU, RIOT and POKEY slots every eight. Runtime
metadata names the same unit and supplies the regional rate, including PAL.
Machine and host share the frame budget. The old host budget was one scanline
short in each region. Step-instruction results use native units and retain the
previous wall-time safety cap. Runtime saves reject version 5 before decoding
or mutating the live machine.

This slice preserves the old 912-native-tick scanline and bulk DMA behaviour.
The reference uses 908; change the raster length with the fetch/output stages,
not as an incidental consequence of changing the counter units. Framebuffer
geometry is unchanged. Audio-rate approximation and slow CPU accesses are not
claimed corrected here.

Red controls are in `2026-10-10-maria-native-clock/clock-*-red.log`: instruction
ticks were 6 instead of 24, runtime frame advancement was 59,964 instead of its
59,736 budget, profile metadata reported the colour clock, and v5 was accepted.
The new checks pass after the correction. CPU bus activity, RIOT timer and TIA
samples resume identically at all eight native phases in both regions. A
standalone TIA comparison includes register writes between sound clocks.

Validation: 50 tests across machine, runtime and frontend; Clippy with warnings
as errors; formatting and diff checks; Asteroids 200-frame boot/render test.
The synthetic runtime cartridge now asserts that it actually ran 60 frames.
Logs are in the adjacent evidence directory. The POKEY finding below is excluded
from the restoration claim.

## Full-clock reference sweep

Reference: `Atari7800_MiSTer`, revision
`29aaacbbed127c670972c8a0a950ca82dc87e5df`. The own testbench drives the reference's
actual clock generator and video-sync module, unlike the earlier DMA-only
harness. Run:

```sh
python3 plans/2026-10-10-maria-native-clock/run_raster.py \
  ../../emulators/atari/Atari7800_MiSTer/rtl/Maria \
  /private/tmp/maria-raster-reproduction
```

Icarus 13 requires the previously qualified constant-wildcard workaround.
Two additional syntax adapters expand unpacked constant arrays into individual
assignments; their parsed values and array lengths are checked. A declaration
moves before its first use. Generated reference copies stay in scratch and
are not committed. `hashes.log` records source and generated hashes. The
vendored reference is verified unchanged after the run.

The testbench uses `ce=1` at each native clock, matching the top-level clock
wiring. It initialises six omitted reference reset values explicitly; those
assumptions are visible in the harness. Control and pointer setup use bus writes.
Only empty display lists are covered so far.

All 48 combinations pass: PAL/NTSC, fast ROM/slow RIOT accesses, zone heights
1/2/3/16, and no/all/second-descriptor DLI flags. Each row checks 24 DMA starts
and releases, the exact expected pulse count, complete pulse release, 38 full
908-tick line intervals, and no unknown bus control after setup. The single
flagged upcoming descriptor fires at raster 16 plus the preceding zone height.
Suppressing the NMI output fails with `expected=1 pulses=0 lines=38`.

The reference pulse lasts 16 native ticks on fast accesses and 24 on slow
accesses. Its assertion delay varies with CPU phase. The isolated harness's
17-tick delay is therefore not a production constant. The primary acceptance
specification describes a one-CPU-cycle pulse, while this reference uses two.
The primary evidence and revision limits are recorded first in
`198x/reference/by-system/atari-7800/maria-dma-timing-evidence.md`.

Next gates: populated headers/graphics, actual bus-fetch timestamps, DMA cutoff,
line-buffer playback mapping, and adjudication of the standalone production
chip's external NMI phase. No empty-list sweep establishes those behaviours.

## Separate POKEY restore finding

The native-phase probe exposed an existing shared-chip bug. POKEY's serde
layout skips the audio accumulator, sample count/phase and filter history along
with its delivered output buffers. Restoring therefore changes the timing and
value of future audio. A minimal reproduction needs no MARIA or machine clocks:

```sh
cp ../docs/plans/2026-10-10-maria-native-clock/pokey_restore_probe.rs \
  crates/machine-atari-7800/tests/pokey_restore_probe.rs
cargo test -p machine-atari-7800 --test pokey_restore_probe
```

It fails at resumed cycle 21 with `left: [0.24523441], right: []`, after the
pre-save output has been drained. The own temporary integration probe was
removed after recording its source and failure log; no committed test was
ignored or disabled. Fixing the shared chip requires considering its other
machine consumers and snapshot versions. It is not part of this clock-only
commit or evidence for completing MARIA #197.
