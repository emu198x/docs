# Exercise MARIA interrupt delivery through the native machine

Continue the approved staged correction in the engineering-frontier lane.
The original DLI probe uses APIs removed by the native DMA integration. Restore
an executable acceptance gate without selecting an unqualified pulse delay.

1. Add a diagnostic Rust module in the adjacent `maria-native-dli-probe/`
   directory. Run a synthetic 6502 cartridge through the existing native
   machine in both regions, at zone heights 1/2/3/16, with absent/all/alternating/
   single-entry flags and fast/slow/WSYNC guest loops. Use a 16-bit handler
   counter so PAL's longer active region cannot wrap an eight-bit observation.
2. Count actual descriptor flag reads, NMI pin edges, both vector-byte reads,
   and completed handlers independently. Check a complete nonempty case
   inventory, descriptor progression and inactive controls. Preserve timestamps
   for the first requested and delivered interrupt, without claiming that
   today's line-boundary delivery is correct hardware timing.
3. Compile the temporary module in the existing source checkout, preserving
   and restoring its pre-existing work byte for byte. Retain the module and
   bounded output here; do not commit a failing diagnostic as a production test.
4. Deliberately suppress the guest handler to prove that pin/vector observations
   alone cannot pass. Document the remaining failing cases and run format/lint
   checks. Keep source PR 1704 draft and issue 197 open until pulse phase and
   raster-output acceptance gates are satisfied.

This slice changes no production API, schema or timing. The approved design
is `2026-10-10-maria-timed-dma-design.md`; the current physical timing limit is
recorded in `2026-10-11-maria-dynamic-raster-clock.md`.

## Result

The probe executes all 192 combinations: two regions, four zone heights, four
flag patterns, three guest loops and DMA enabled/disabled. Descriptor reads
must advance consecutively; active rows require actual DMA and CPU execution.
The RIOT and WSYNC loops must exercise their respective slow reads and waits.
The handler counter starts at 254, exercising its carry on every row with two
or more delivered interrupts. Counts report increments relative to that seed.

Six rows fail, covering consecutive flagged one-line zones with each guest
loop in both regions:

| Region | Flagged descriptor reads | NMI edges | Each vector-byte read | Handler increments |
| --- | ---: | ---: | ---: | ---: |
| NTSC | 243 | 1 | 1 | 1 |
| PAL | 293 | 1 | 1 | 1 |

The other 186 rows agree on all four observations. This is delivery-count
evidence, not an assertion that their interrupt phase is correct. For example,
the initial flagged descriptor is read at native tick 14,558 on raster 16,
while the current CPU pin first rises at tick 15,436 on raster 17. The machine
still consumes pending requests only at the line boundary; consecutive true
values never generate another edge.

The actual failure is:

```text
assertion `left == right` failed: every native DLI request must reach its handler
  left: 6
 right: 0
```

Replacing the guest counter handler with an immediate RTI makes 72 rows fail.
In 66 of these, pin edges and both vector reads still agree with the requested
count. Only the executed outcome reveals the fault. Eight capture-guard tests
also pass, rejecting missing/duplicate cases, absent DMA, compiler failure,
false success status, a missing test result and a falsified summary.

The source was `edc96b5a` plus the pre-existing POKEY clock/sample wiring work.
The exact machine-source hash and probe hash are in `summary.json`. The runner
restored the source byte for byte after each capture. No production behaviour
was changed. Ruff checks/formatting, Rust formatting and diff hygiene pass.

The existing reference captures establish separate pulses and upcoming-zone
ownership. Their physical phase qualification remains limited as described
in the dynamic-raster plan. The primary Atari software guide describes DLI
after the preceding zone's DMA; the source is linked in the
[original investigation](2026-10-10-maria-dli-pulses.md). This diagnostic does
not settle the specification/layout disagreement or replace the required
raster-output cartridge. PR 1704 remains draft and issue 197 remains open.

## Reproduction

Run with exclusive access to the machine source file; pre-existing edits are
preserved. The runner installs a temporary test module, captures baseline and
handler-suppression runs, checks the complete observations, and restores the
original file. It exits **1** while the baseline acceptance check is red;
the underlying Rust tests exit **101**. Capturing an expected failure does
not turn it into a passing acceptance test.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-maria-native-dli-probe/run_probe.py \
  ../emu198x /path/to/local-output
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-maria-native-dli-probe -v
```

The adjacent logs retain all observations. The compact summary hashes the
complete ordered rows using UTF-8 JSON with sorted keys and separators
`(',', ':')`; it also retains every baseline failing row. Full regenerated
rows are in the runner's local `summary.json` output.
