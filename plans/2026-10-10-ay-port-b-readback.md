# Read externally driven AY port B pins in output mode

Lane: engineering-frontier accuracy. Bounded correction within existing
AY port state; no new public API, dependencies, architecture or snapshot
schema. Separate from the unapproved upper-address decoder investigation.

## Result

All three new regressions fail before the correction. The Aquarius board
reads 255 instead of 187 for held up/fire contacts; Einstein reads 255
instead of 171 for grounded keyboard columns. The core test also detects
the disagreement between the two ports with identical wiring.

The correction applies the existing output-latch/external-pin combination
to port B. Its complete 131,072-case sweep covers all input masks and latch
values in both directions, checking that reads do not alter either latch.
All 93 affected-suite tests pass, plus four real-ROM checks: Aquarius boot
and audible startup beep, Einstein MOS boot and keyboard-entered HELLO.
The ordinary suites leave seven fixture tests ignored; four are exercised
explicitly above. Disk boot and two Aquarius cartridge tests are outside
this correction's validation scope.

Warnings-denied Clippy passes. The initial formatting check requested only
a line wrap in the Einstein assertion; formatting was applied and the
check passes. Retained logs and source/ROM identities are in the
[evidence folder](2026-10-10-ay-port-b-readback/). No firmware is included.

## Cause and sources

`Ay3_8910::read_data` combines port A's output latch with its external input
mask, but returns port B's output latch without consulting `port_b_input`.
External devices pulling a B pin low therefore disappear from readback when
R7 bit 7 selects output mode. Both ports should resolve the same way.

The manufacturer's I/O-port sections in
`reference/by-topic/psg-ay-3-8910/` describe both ports as equivalent I/O
blocks. [Kevin Thacker's hardware observations](https://cpctech.cpcwiki.de/docs/psgnotes.htm)
explicitly describe output-mode readback as the stored value ANDed with
external inputs for both ports. MAME `ay8910_read_ym` consults external port
callbacks even in output mode; this independently corroborates the missing
external influence, not an exact shared implementation.

## Plan

1. Add a failing core regression in
   `crates/emu198x-gi-ay-3-8910/src/lib.rs` that gives ports A and B identical
   external levels and latch data, covering all 256 input masks, all 256
   latch bytes and both directions. Assert equivalent resolved reads and
   preservation of the output latches.
2. Add consumer regressions in `crates/machine-mattel-aquarius/src/lib.rs`
   and `crates/machine-tatung-einstein/src/lib.rs`: held controller contacts
   and keyboard columns remain visible while port B is configured as output.
   Releasing contacts restores the latched data on reads.
3. Apply the existing port A resolution rule to B's existing fields; clarify
   method documentation. Do not change pin setters, storage or chip timing.
4. Run core, facade, both machines and runtimes; run available strict ROM
   checks, warnings-denied Clippy and formatting. Retain failing/passing
   logs, source identity and scope limits; commit and merge after CI.

## Commands

From the source repository:

```sh
cargo test --release -p emu198x-gi-ay-3-8910 -p gi-ay-3-8912 \
  -p machine-mattel-aquarius -p runtime-mattel-aquarius \
  -p machine-tatung-einstein -p runtime-tatung-einstein
EMU198X_STRICT_FIXTURES=1 cargo test --release -p machine-mattel-aquarius \
  --test bios_boot --test boot_beep -- --ignored --nocapture
EMU198X_STRICT_FIXTURES=1 cargo test --release -p machine-tatung-einstein \
  --test bios_boot --test keyboard_type -- --ignored --nocapture
cargo clippy -p emu198x-gi-ay-3-8910 -p gi-ay-3-8912 \
  -p machine-mattel-aquarius -p runtime-mattel-aquarius \
  -p machine-tatung-einstein -p runtime-tatung-einstein --all-targets -- -D warnings
cargo fmt --all -- --check
```

The strict checks require the identified ROMs at their conventional
`~/.emu198x/roms/{mattel-aquarius,tatung-einstein}/` paths, or their documented
environment overrides. Each selected fixture test fails if its BIOS is
missing; a zero-test or skipped result is not accepted as evidence.
