# Shared 6502 interrupt validation

Close source issue #126 by making its accepted NES delegation explicit and
reproducible. This is engineering-frontier validation work; no CPU behaviour,
public API, save-state layout or dependencies change.

## Evidence and scope

The existing `machine-nintendo-nes/tests/nes_sweep.rs` runs blargg's
`cpu_interrupts_v2` with the NES APU, PPU and DMA services it requires. The shared
`emu198x-mos-6502` crate supplies both `M6502::new()` and `new_2a03()`; their
interrupt and branch stages are the same. The constructor differences gate
decimal arithmetic and the unstable ANE/LXA constants, not interrupt stages.

Issue #126 explicitly accepts documenting this delegation instead of duplicating
a NES-dependent ROM runner inside the CPU crate. A fresh run is needed before
claiming the ROMs pass.

## Tasks and verification

1. Add `cpu_interrupts_v2` to the existing `nes_sweep.rs` test target. Reuse
   `run_one` for the five named singles and combined ROM, require a pass for
   every entry, and fail when an explicitly invoked gate lacks its fixtures.
   Keep the full sweep and its exact baseline unchanged.
2. Run the six ROMs in release mode. Temporarily disable the shared core's
   taken-branch IRQ-poll suppression, rerun the gate and require a ROM failure.
   Restore the original CPU source exactly and rerun the gate. Preserve logs,
   ROM SHA-256 hashes and source identity here without ROM payloads.
3. Audit constructors/dependencies in NES, Atom, BBC Micro, Electron, Atari
   2600/5200/7800/800XL, PET, VIC-20 and Oric. Update
   `knowledge/chips/mos-6502.md`, its index entry and append-only log with the
   delegated coverage and limits. Do not equate shared CPU validation with each
   board's interrupt-source timing, or close Dormann issue #124.
4. Run shared CPU unit tests, focused NES gate, formatting and focused Clippy;
   review the diff, commit and submit source/docs PRs. Merge after checks pass,
   then close #126 through the source PR.

## Results

All six ROMs pass on base `1387dd925ffbba6f0b6b87e5a418eced4dd4b38e` with the
focused harness added in source commit `fd431e8b0023d3d3725ea3923d36b5439d5424e0`. The production CPU source is unchanged. Fixture hashes,
compiler identity and dependency/constructor audit are retained alongside this
plan in `2026-10-10-6502-interrupt-delegation/`.

| ROM | Pass at NES master tick |
| --- | ---: |
| `1-cli_latency.nes` | 1,523,091 |
| `2-nmi_and_brk.nes` | 9,563,874 |
| `3-nmi_and_irq.nes` | 11,350,698 |
| `4-irq_and_dma.nes` | 6,168,849 |
| `5-branch_delays_irq.nes` | 33,954,057 |
| `cpu_interrupts.nes` | 65,123,712 |

The gate uses the existing sweep runner and requires a pass for each fixed
entry. A missing root panics; missing files or malformed ROMs return errors;
timeouts, visual-only and externally gated verdicts fail. There is no glob
that can silently enumerate zero cases and no accepted-failure baseline.

The negative control changed only the assignment
`self.branch_irq_suppress = true` to `false` in `tick_relative`. The branch
single and combined ROM each reported `Failed`, code 1; the gate exited 101.
The first four singles still passed. Restoring the saved original CPU file
byte-for-byte made all six pass again at the same ticks. `git diff --exit-code`
confirmed the mutation left no CPU changes.

Validation commands:

```sh
cargo test --release -p machine-nintendo-nes --test nes_sweep cpu_interrupts_v2 -- --exact --ignored --nocapture
cargo test -p emu198x-mos-6502 --lib
cargo clippy -p machine-nintendo-nes --test nes_sweep -p emu198x-mos-6502 --lib -- -D warnings
cargo fmt --all -- --check
python3 scripts/check-fixture-guards.py --self-test
python3 scripts/check-ignore-reasons.py --self-test
```

Results: six ROM passes within one focused gate, 39 shared CPU unit-test passes,
clean Clippy and formatting, and both hygiene checks pass with their own
negative self-tests. Full command output is retained; the mutation log is an
intentional failure, not an unresolved production defect.

## Shared-core delegation and limits

NES uses `M6502::new_2a03()`. Atom, BBC Micro, Electron, Atari 2600/5200/7800/800XL,
PET, VIC-20 and Oric use `M6502::new()` from the same workspace dependency.
`consumers.txt` identifies each declaration and constructor. Both constructors
initialise the same interrupt fields and use the same `tick.rs` implementation.
`decimal_disabled` gates ADC, SBC and undocumented ARR; ANE/LXA have different
variant constants. Neither gates the branch or interrupt stages.

The NES suite therefore exercises the shared CPU's delayed I-bit sampling,
NMI/BRK/IRQ vector interactions and taken-branch interrupt polling. It also
checks interrupt/DMA interactions on the NES. It does not establish another
board's IRQ/NMI routing or source timing, nor complete the separate Dormann
interrupt/decimal harnesses in issue #124. The suite readme warns that
`2-nmi_and_brk` can occasionally fail on hardware due to PPU/CPU synchronisation;
these results describe the emulator's startup alignment.

Issue #126's requested `knowledge/chips/mos-6502.md` note, knowledge index and
append-only log were updated locally. Those files are deliberately ignored by
the source repository under its docs-site decision. This tracked record and
the source harness preserve the reproducible evidence publicly without
publishing the private working knowledge base.
