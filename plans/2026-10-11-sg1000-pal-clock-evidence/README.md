# PAL audio-rate baseline

The original cartridge in `probe.rs` programs PSG tone channel 0 and counts
executed loops in RAM. The unmodified machine advances by the T-state rate
read from `runtime_sega_sg_1000::profile_for` for each of three consecutive
seconds. Every interval must contain audible output; the probe also prints
its guest marker. No CPU registers, RAM or I/O are patched by the host.

At source `6aeae61fce121dff9a7fa1f22eb699436c67f85b`, all three NTSC
intervals contain 48,000 samples. PAL has 48,441, 48,443 and 48,442. The
probe intentionally exits 101 because three of six intervals violate the
runtime/audio duration invariant. These are measured values, not a hardware
clock oracle. The exit and assertion are retained in `baseline.stderr`.

To reproduce, build `machine-sega-sg-1000` and `runtime-sega-sg-1000` with
the source workspace's pinned toolchain. Compile the probe with `rustc
--edition=2024`, `-L dependency=<target>/debug/deps` and `--extern` paths for
`common_z80_machine`, `machine_sega_sg_1000`, and `runtime_sega_sg_1000`.
Run it and retain stdout, stderr and the nonzero exit. Run from the source
checkout so the toolchain matches the linked rlibs.

`SHA256SUMS` covers the probe, observations and provenance. No corrected
capture or PAL console hardware timing claim is made yet.
