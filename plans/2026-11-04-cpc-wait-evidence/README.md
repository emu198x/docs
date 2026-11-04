# CPC WAIT and save qualification

CPC464, CPC664 and CPC6128 adopt published Z80 0.9 with version-6 saves.
Qualified source: `322c672fbd7765aa91c4b4271849795a803ae3bc`.
The original v4/v5 specimens remain unchanged and are rejected before payload
decoding. This qualifies the CPU correction; it does not settle the existing
mixed-stream instruction-cost discrepancy discussed in #971.

## Reproduce

From a checkout containing the source change, run:

```sh
python3 verify.py /path/to/emu198x
cargo test --locked -p common-amstrad-cpc -p runtime-amstrad-cpc \
  -p machine-amstrad-cpc464 -p machine-amstrad-cpc664 -p machine-amstrad-cpc6128
cargo test --locked -p emu198x-amstrad-cpc --no-default-features
cargo clippy --locked -p common-amstrad-cpc -p runtime-amstrad-cpc \
  -p machine-amstrad-cpc464 -p machine-amstrad-cpc664 \
  -p machine-amstrad-cpc6128 --all-targets -- -D warnings
```

`verify.py` checks all 18 original/new specimen files against `fixtures.json`
and checks the resolved CPC CPU graph. It requires both a nonempty CPU graph
and version 0.9.0 throughout that graph. It does not run the Rust tests itself.
The Rust commands run from the emulator checkout; `verify.py` is beside this
README in the docs checkout.

With the original local firmware and SHAKER images staged, also run:

```sh
cargo test --locked -p common-amstrad-cpc --test firmware_boot \
  --test firmware_keyboard --test interrupt_timing --test microsecond_grid \
  --test shaker -- --ignored --nocapture
EMU198X_CPC_AMSDOS_ROM=/path/to/cpcados.rom cargo test --locked \
  -p common-amstrad-cpc --test firmware_disc -- --ignored
cargo test --locked -p common-amstrad-cpc --test firmware_tape -- --ignored --nocapture
```

## What changed

The original baseline is source `e8b693731`, using CPU 0.8. Its three complete
v5 states and continuation records reproduced byte-for-byte. An otherwise
unchanged private candidate selected published CPU 0.9 through both direct CPC
requirements; the lockfile changed only those two dependency edges.

The first internal sequencer difference is at half-cycle 2, as memory WAIT
moves from a repeated rising half-cycle to complete TW pairs. The first
physical bus/architectural difference is the synthetic firmware's CRTC index
write at BC00. IORQ/WR releases at half-cycle 81 with CPU 0.8 and 87 with 0.9.
The corrected sampling edge arrives after WAIT has asserted again. This
happens identically on all three models; no machine clock or WAIT phase changed.

At the frozen specimen's time of 330033 T-states, both candidates retain the
same monitor scan (`last_retrace=329896`, `relocking=false`). CPU 0.8 has PC
00AB, an internal cycle with eight half-cycles remaining, R=31 and 27521
retired instructions. CPU 0.9 has PC 00A9, M1 T1 rising, R=21 and 27512 retired
instructions. These are decimal register R values.

All three subsequent native fields match in complete frame records and audio
sample bits, with elapsed times 82337, 82474 and 82474 T-states. The complete
final saved CPU state differs. A matching picture cannot establish equivalent
saved execution.

The user approved v6 and early rejection of v4/v5. The new v6 specimens come
from fresh corrected execution with the unchanged project-written synthetic
firmware, not from relabelling old save bytes. No copyrighted ROM is published.

## References and limits

- The original CPC464 Firmware guide, printed p. 1.2, describes synchronized
  memory accesses and M-cycle stretching. Its extract and source provenance
  are held in the umbrella `reference/by-system/amstrad-cpc/`.
- Longshot's [CRTC Compendium 1.11](https://shaker.logonsystem.eu/ACCC1.11-EN.pdf),
  printed pp. 31, 282, 286 and 290, provides I/O diagrams and instruction/WAIT
  discussion. The former 1.10 download URL now returns HTML; it was not treated
  as the old PDF. Page 31 was rendered and inspected.
- Vendored MAME `amstrad_m.cpp:2183` pads memory cycles with `adjust_icount`;
  it supplies no independent WAIT-pin waveform. Arnold's `Z80_ExecuteInterrupt`
  returns 5/7 microseconds; Caprice32 records 20/28 T-states. Those totals do
  not qualify internal sample placement or a replacement machine phase.
- The release phase remains 2. The existing JP/NOP 11/5 T-state pair and
  19-T-state IM1 entry remain recorded. CPU 0.9 is not claimed to fix them.
- An additional five-cycle paused-WAIT snapshot probe was set aside after its
  coverage guard could not establish a held memory write. Its failed attempts
  remain in private recovery evidence. No five-cycle coverage is claimed;
  the shipped gate is the exact three-field continuation on all three boards.

## Controls

Using CPU 0.8 with the new v6 oracle fails at
`amstrad-cpc464: full v6 state`. Returning the injection regression to the old
`instruction_complete` guard fails with PC 8001 instead of 0038. The corrected
`at_execution_boundary` guard makes all five SHAKER tests pass; the old guard
failed to launch three 464 tests after the CPU timing correction.

Complete v4/v5 specimens and version-only prefixes are rejected for blank and
live runtimes on all three models. Their original file identities are pinned
in `fixtures.json`. Fresh v6 snapshots and the first three restored fields,
audio sample bits and final state are compared exactly against separate v6
files, rather than replacing historical expectations.

## Verification results

- 104 common/runtime/board tests and 14 headless-runner tests pass.
- 16 fixture-gated tests pass when run explicitly: two 464 boot checks, two
  disc catalogue/program tests, five SHAKER tests, one keyboard test, two
  interrupt measurements, three grid measurements and the real tape load.
- The tape consumes 220049 of 220179 spans and the program takes over the
  display. The test ran within its explicit 300-second process deadline.
- Clippy passes with warnings denied; formatting and diff checks pass.
- The dependency graph contains only CPU 0.9 on the CPC path; only its two
  direct lockfile edges changed. No other family was upgraded.
- Two further negative controls fail: accepting old versions past the header
  breaks the version-only rejection test, and a modified specimen breaks the
  public SHA-256 verifier. All positive implementations were restored.
