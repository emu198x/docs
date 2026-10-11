# 6845 sync-width baseline

An original standalone Rust program writes the public register ports and samples
the public HSYNC/VSYNC outputs after each character clock. It imports the
production crate; it does not reproduce its counter implementation.

Source: `10892b445182cc5d8106cff7cd142f9a64d4cf10`.
All 64 rows are retained in `sync-baseline.csv`, including both passing controls.
The process exits 101, with:

```text
62 mismatches across 64 pin-level sync cases
CRTC sync outputs must remain high for the programmed interval
```

For each of two variants, the probe varies all 16 horizontal encodings and all
16 vertical encodings. Each nonzero expected width must produce at least two
complete pulses, and every complete pulse must have the specified length. The
two zero-H controls require no high samples, including any trailing partial
pulse. Hitachi excludes zero-H programming, so its row is an implementation
control rather than a specified hardware waveform.

R0 is 63, hence 64 clocks per line; R7 is 25 and R9 is zero. The raster is long
enough for complete vertical pulses. These are normal, fixed-register,
non-interlaced cases, not coverage of frame-wrap or mid-pulse writes.

Expected widths come from Motorola 1977, PDF page 12, and Hitachi 1987 U70-A,
printed page 148 / PDF page 159. See the [chip reference](../../chips/motorola-6845.md).
`manifest.json` binds the original program and captures to their hashes. The
unchanged crate's existing tests separately report 23 passes and no failures.

## Reproduce

With a checkout of the source commit and its Rust toolchain:

```sh
cargo build -p motorola-6845 --message-format=json
```

Use the `compiler-artifact` entry for `motorola_6845` to identify its `.rlib`.
Compile this directory's `sync-probe.rs` with that library and its containing
dependency directory, then run the resulting binary:

```sh
rustc --edition 2024 sync-probe.rs \
  -L dependency=/absolute/target/debug/deps \
  --extern motorola_6845=/absolute/target/debug/deps/libmotorola_6845-HASH.rlib \
  -o /tmp/6845-sync-probe
/tmp/6845-sync-probe
```

The baseline must fail with 62 mismatches. A corrected implementation should
make the same program pass without changing its width expectations.
