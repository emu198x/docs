# NES 2.0 ROM extent evidence

The size decoder and mapper-boundary regressions are recorded against source
PR #1730, head `f3604fa2e752dabe1e6a4274d6fd41e3b4bbdf95`.

- `before.log`: two exponent payload failures before the decoder correction.
- `partial-bank-before.log`: the out-of-bounds NROM read after decoding, before the mapper guard.
- `affected-tests.log`: 186 passed, zero failed, 135 ignored across parser, machine and runtime crates.
- `clippy.log`: affected all-target Clippy with warnings denied.
- `comparison.json`: exhaustive size-helper result counts and reference source hash.
- `compare_sizes.py`: our host; it extracts the unchanged reference and production functions locally.

Logs replace local source/target paths and omit the host's mise tracking warning.
No ROMs, reference implementation source, generated reference binaries or full
third-party emulator checkouts are included.

## Reproduction

Use a 64-bit host with Python 3.13+, a C++20 compiler named `clang++`, and the
source checkout's Rust toolchain. Obtain Mesen2 revision
`fabc9a62174f8734a113df6d244f5539ef6b8fcf` separately. The compared file is
`Core/NES/NesHeader.cpp`; its expected SHA-256 is in `comparison.json`.

```sh
python3 compare_sizes.py /path/to/Mesen2 /path/to/emu198x /tmp/nes2-size-comparison
```

The host chooses NES 2.0 and discards reference logging, then compiles the
unchanged size methods. It requires exactly 4,096 rows from each binary and
checks every result. Mesen2 returns 32-bit sizes; results beyond that range
are checked against exact integer arithmetic, not treated as reference matches.
The production host must be 64-bit for the recorded overflow counts.

From the source checkout:

```sh
cargo test -p format-nintendo-nes-ines -p machine-nintendo-nes -p runtime-nintendo-nes
cargo clippy -p format-nintendo-nes-ines -p machine-nintendo-nes -p runtime-nintendo-nes --all-targets -- -D warnings
cargo fmt --all --check
```

This evidence establishes decoder boundaries and the covered mapper read
windows. It does not establish board wiring, unimplemented metadata, or
execution of the explicitly ignored test corpus.
