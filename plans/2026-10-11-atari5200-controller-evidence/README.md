# Atari 5200 controller evidence

The production correction is not implemented. The failing captures establish
why issue #421 requires a live scan stage, not just additional input aliases.

| Capture | Cases | Mismatches | Exit |
|---|---:|---:|---:|
| `baseline.csv` | 336 | 176 | 101 |
| `debounce-baseline.csv` | 84 | 46 | 101 |
| `reference.csv` | 2,048 | 0 | 0 |
| Reference with debounce comparison bypassed | 2,048 | 120 | 1 |

`probe.rs` builds an original 32 KiB cartridge and 2 KiB reset-vector BIOS in
memory. It boots through the CPU reset sequence, programs GTIA/POKEY/ANTIC and
copies chip reads into RAM. No CPU register, RAM or framebuffer is patched.
The guest requires `$0230=$A5` and more than 100 completed register-read loops.
Each case runs four actual NTSC frame budgets. A separate released-control
execution supplies the other pot values; this is a routing comparison, not
an analogue model qualification. `--debounce` adds SKCTL 1/3 cases at selector 0.
The default matrix covers selectors 0-3 and SKCTL 0/2, for physical ports
1-4, alias 0 and invalid ports 5/255, across idle/fire1/x/y/fire2/keypad-1.

From a source checkout at `10892b445182cc5d8106cff7cd142f9a64d4cf10`, build
`cargo build -p runtime-atari-5200`, then compile this standalone probe with
that target directory's `libruntime_atari_5200.rlib` and matching
`libemu198x_shell-*.rlib`, using `rustc --edition 2024 -L dependency=...`.
Run it once without arguments and once with `--debounce`. Both must currently
exit 101 after writing their complete CSV captures. The assertion is:
`controller observations differ from connector routing and scan-enable invariants`.

`reference-probe.py` extracts the **unchanged** keyboard scan event and Break
IRQ method from the vendored Altirra source. It compiles a scratch C++ harness
with `clang++` and supplies the selected controller's matrix and IRQ
acknowledgements. Source hashes are in `reference-provenance.json`. The
script writes `reference-probe.cpp`, binary and captures alongside itself;
use a scratch copy when rerunning. No third-party source is vendored here.

Its 2,048 rows cover four ports, four selectors, four SKCTL values, 15 keys
plus no key, and both upper-fire states. Each row runs 192 scan events.
Times count from a supplied divider-edge origin, **not from a CPU SKCTL
write**. Scheduling, CPU-write phase, analogue charging, matrix ghosting,
release and restore are outside this sweep. The reference and hardware
manual share an author; this is not an independent hardware capture.

The negative control replaces the four `!(mSKCTL & 1)` comparisons in the
extracted scratch C++ with `true`, recompiles, and fails 120 cases. Its
stderr is retained. `verify.py` checks complete case coverage, execution
counts in the capture, reference invariants and mismatch
accounting. This archive check passing does not mean the emulator passes.

## Simultaneous-key circuit check

`matrix-reference.py` executes unchanged Altirra `UpdateEffectiveKeyMatrix`
against a separate reachability calculation on the 4-row/4-column switch
network. It covers all 32,768 subsets of the 15 real keypad switches, with
upper fire both released and held: **65,536 cases, zero sampled-line
mismatches**. It compares all 64 KR1 scan positions and the three KR2 sampling
positions; unused modifier bits in the reference's internal matrix are not
external signals. `matrix-reference.csv.gz` is the complete capture, with
its decompressed hash in `matrix-provenance.json`.

62,522 cases include phantom keypad positions. Replacing the effective-matrix
method with a plain copy of the held keys makes the probe exit 1; its failure
count is recorded in `matrix-no-ghosts.stderr`. The calculation validates the
combinational connectivity model, not electrical propagation delays. This
check adds no production code or saved state.
