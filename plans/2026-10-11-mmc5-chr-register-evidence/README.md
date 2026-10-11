# MMC5 CHR register probes

These observations use Emu198x source head
`f3604fa2e752dabe1e6a4274d6fd41e3b4bbdf95`. No mapper correction has been made.
The synthetic CHR payload identifies 1 KiB pages by page number modulo 251.

- `probe.rs` / `baseline.csv`: reads all 8,192 pattern bytes for 64 static mode/bank pairs. 34 rows disagree with bank indices in the selected window size.
- `mode_probe.rs` / `mode-baseline.csv`: writes four aligned banks in 1 KiB mode, then changes the mode without another write. Twelve widening cases disagree with retained physical bases; four unchanged-mode controls pass.
- `compare_reference.py` / `reference_host.cpp.in`: compile Mesen2's unchanged `UpdateChrBanks` locally and compare all 64 expected first-page bytes.
- `reference.csv` / `comparison.json`: compiled reference output and checked counts.
- `hardware/`: original observation cartridge, full-machine hosts, 32-row measurements and negative controls for the unresolved write bits. See its README for building and hardware capture.
- `finding.json`: original bounded observation and the remaining validation requirement.

The reference host fixes 8x8 sprites and records selected pages. It does not
simulate a complete PPU or prove mode-change correctness. The reference uses
raw bank indices and is unsuitable as the mode-transition oracle.

## Reproduction

Build `format-nintendo-nes-ines` in the named source checkout. Set `INES_RLIB`
to its freshly built `.rlib` and `NES_DEPS` to that build's `debug/deps`
directory. From this evidence directory, with the same Rust toolchain:

```sh
rustc --edition=2024 probe.rs --extern "format_nintendo_nes_ines=$INES_RLIB" -L "dependency=$NES_DEPS" -o /tmp/mmc5-static-probe
/tmp/mmc5-static-probe
rustc --edition=2024 mode_probe.rs --extern "format_nintendo_nes_ines=$INES_RLIB" -L "dependency=$NES_DEPS" -o /tmp/mmc5-mode-probe
/tmp/mmc5-mode-probe
python3 compare_reference.py /path/to/Mesen2 /tmp/mmc5-reference-check
```

Use Mesen2 revision `fabc9a62174f8734a113df6d244f5539ef6b8fcf`. The host
requires Python 3.13+ and clang++ with C++20 support. It verifies nonzero row
counts and every expected first-page result; a mismatch raises an error.
Ruff passes, and rerunning the host reproduced 64 reference agreements and
34 baseline mismatches. Full-byte counts come from the public mapper probe,
not from the first-page reference comparison.

The retained-register expectations come from the primary schematic and use
only unambiguous bits. See the parent design for the uncertain low-bit
write paths. No ROM bytes or third-party source bodies are included.
