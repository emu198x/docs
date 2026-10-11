# Sord M5 I/O alias evidence

The original CPU guests demonstrate dropped upper CTC, VDP and PSG port
aliases. The bounded decoder correction restores them without changing
snapshots, clocks or chip stages. Keyboard and unmapped-read controls remain
unchanged. This supports issue #251's source and documentation correction.

- `sources.json`: manufacturer scan attachment URLs, hashes and provenance
  limits. The one-page BASIC-G appendix is printed page 279; the second scan
  is Sord's M5C-01 schematic. No copyrighted scan is reproduced here.
- `red.log`: baseline guest failures at main `0ec2b192848da4765d4da71822e1db440fb7f7a3`.
  The test code was added before the decoder changed; compilation failure is
  not counted as the red result.
- `tests.log`: corrected machine/runtime suite, 38 passed and six ignored.
- `firmware.log`: all six gated firmware tests explicitly executed, all pass.
- `fixture-hashes.json`: identities of the local BIOS and cartridges used;
  copyrighted media are not included.
- `clippy.log`: affected all-target checks with warnings denied.

The regression is `crates/machine-sord-m5/tests/io_aliases.rs` in the source
PR. It constructs its own ROM-slot programs; it calls no private I/O handlers.
For red reproduction, apply that test file to the baseline revision and run:

```sh
cargo test -p machine-sord-m5 --test io_aliases
```

Run the same command on the corrected source, then the two affected packages:

```sh
cargo test -p machine-sord-m5 -p runtime-sord-m5
cargo clippy -p machine-sord-m5 -p runtime-sord-m5 --all-targets -- -D warnings
cargo fmt --all -- --check
```

The fixture tests additionally require installed original media, including
European BIOS SHA-1 `ac042c4ae8272ad6abe09ae83492ef9a0026d0b2`. Set
`EMU198X_SORD_M5_BIOS` and `EMU198X_SORD_M5_CART` to the monitor and Dig Dug;
BASIC-I/Dig Dug also reside in the existing `~/.emu198x/media/sord-m5/` paths.
Use `cargo test -p machine-sord-m5 -- --ignored --nocapture`.

MAME `src/mame/sord/m5.cpp::m5_io` at revision
`9391e1eff80eb04abd58d48218a1d3b9643c1ea8` supplies implementation precedent.
This pass did not execute MAME's full stock M5 because its required FD-5 ROM
was unavailable. Manufacturer wiring and implementation source support the
aliases; Emu198x guests prove the defect and correction. Neither is claimed
as a physical hardware capture or a PSG waveform accuracy comparison.
