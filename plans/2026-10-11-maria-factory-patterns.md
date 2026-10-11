# Qualify MARIA factory test patterns

Engineering-frontier research for the remaining #197 NMI phase gate. The
staged correction is approved; its physical assertion timing still needs
evidence. This work changes no production schema or pipeline design.

The [GCC MARIA archive](https://7800.8bitdev.org/images/0/06/GCC_MARIA_Chip_Layout_and_Netlist_Artifacts.zip)
SHA-256 is `849e215c71d13c17ec813f97a23b2078469c4b1e14a36dcd5a9ccf72b5360a48`.
Despite the archive's layout/netlist title, several `.2SC` files are readable
Sentry factory tests. The primary acquisition record retains member hashes
and distinguishes these files from binary test data and layout material.

1. Inspect the standalone-chip pin map and tester setup in
   `MARIAS/MARIAC/REV0/Z5349.2SC.1`, and the readable `MARIAS/MARIAB/ZMAR00`
   through `ZMAR03.2SC.1` patterns. Establish which revisions actually share
   those patterns. Names alone cannot establish equivalence with later
   compiled `.2MD` files.
2. Qualify a bounded source decoder in this plan's adjacent evidence directory.
   Use the [1977 FACTOR manual](https://bitsavers.org/pdf/fairchild/sentry/factor/67095738_FACTOR_Programming_Language_Reference_Manual_197703.pdf),
   sections 6.4.2–6.4.3, and the
   [1983 Fairchild handbook](https://www.bitsavers.org/pdf/fairchild/sentry/quick_reference/Fairchild_Digital_Test_Systems_Quick_Reference_Handbook_1983.pdf),
   printed pages 3-10, 3-11 and 3-15, for directions, masks, local register
   writes, calls, loops and repeats. Unknown syntax must fail. Keep source
   order, executed order and elapsed time distinct. Include synthetic
   direction/mask, repeat and call/return checks and malformed-input negatives.
3. Determine whether executed patterns compare NMI through a DMA shutdown.
   Retain nonzero observation counts and original source locations. Reject
   a deliberately masked or disconnected NMI observation. Resolve timing-set
   strobes, crystal pulses, and mask-write pipeline delays before converting
   pattern positions to native ticks. A 140 ns tester period contains two
   crystal-input pulses in the inspected setup; one row is not one tick.
4. If these sources establish an NMI constraint, reproduce the corresponding
   stimulus in the qualified reference harness and compare the outputs.
   Record what the factory program requires separately from observations of
   FPGA execution. Only then adjudicate the production pulse schedule. If
   no checked interrupt transition survives, record that bounded negative
   result and leave the physical timing gate open.

Do not redistribute the third-party archive or manuals in the public docs
repo. Retain our decoder, synthetic checks, compact derived observations,
source identifiers, hashes and exact reproduction instructions.

## First bounded decoder gate

Before implementing the tester's clock engine, scan the full stored main
prefix and every called subroutine body for a checked NMI-low pattern with
MEN enabled. This is a conservative superset of execution: the source's
main prefix includes padding after the host-selected end address. Normal
repeat counts are recorded, and MATCH loops have unknown iteration counts;
no elapsed-time inference is allowed. Reject mutation of direction/mask
registers inside a MATCH loop until its runtime semantics are modelled.

Files: `2026-10-11-maria-factory-patterns/decode_patterns.py` and
`test_decode_patterns.py`. Parse every statement in the four pinned full-width
source files; fail on unknown syntax, missing calls, malformed widths, missing
registers or unterminated routines. Preserve compile-time D/M/timing-set
selection separately from runtime LSET values. Synthetic checks must cover
mask/input exclusion, call-site register state, normal repeats, MATCH
uncertainty, return to the caller, and an injected checked NMI assertion.

This gate can disqualify these source patterns as an enabled-NMI timing oracle
without guessing strobe timing. It cannot establish a pulse schedule or prove
identity with the compiled patterns for other revisions.

## First-gate result

The four source files contain no candidate checked NMI-low pattern with MEN
driven high under the decoded mask and call semantics. There are 9,932 visits
to enabled, checked NMI-high patterns. The checked lows occur with MEN low;
the raw lows with MEN high have comparison disabled. The injection controls
find a changed NMI bit in every file, so the empty candidate result is not
an always-empty detector.

| Source | Enabled NMI checks, all high | Checked lows with MEN low | Enabled low candidates |
| --- | ---: | ---: | ---: |
| ZMAR00.2SC.1 | 2,622 | 91 | 0 |
| ZMAR01.2SC.1 | 2,622 | 91 | 0 |
| ZMAR02.2SC.1 | 2,420 | 174 | 0 |
| ZMAR03.2SC.1 | 2,268 | 174 | 0 |

These counts are **coverage visits**, not physical clock ticks or a completed
factory test execution. The decoder visits the entire stored main prefix,
which includes padding beyond a host-selected end address. NORMAL loops
repeat their bodies; MATCH loops have unknown execution counts and are
covered once per call. A MATCH loop may stop within its body, so this is an
over-approximation for candidate discovery. The decoder fails if such a loop
changes direction or mask state. The host's initial direction masks come
from `MARIAB/ZMARIA.2SC.3`; their exact values and source hash are retained.

All source statements are parsed, including uncalled routines and padding.
Eleven synthetic tests pass for mask, direction, MEN, repeat, call-site state,
return, MATCH uncertainty, precise source locations and rejected input.
Injecting one assertion into a previously checked high finds exactly one
candidate in each real source, at lines 2515, 2513, 1076 and 1944 respectively.
Suppressing the NMI mask in each source fails with `missing enabled-NMI
observations`. Ruff lint, formatting and diff checks pass.

This does not establish a physical pulse width or assertion delay. Compiled
pattern identity, host execution limits, inversion and tester strobe/pipeline
semantics remain unqualified. These four source files cannot presently serve
as the positive NMI timing oracle required by #197. Do not turn their masked
zeros into an asserted pulse or select a production timing schedule from them.

## Reproduction

From the docs repo, with the hash-pinned archive held locally:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-maria-factory-patterns -v
python3 plans/2026-10-11-maria-factory-patterns/decode_patterns.py \
  /path/to/layout-artifacts.zip /path/to/coverage.json
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-maria-factory-patterns/qualify_patterns.py \
  /path/to/layout-artifacts.zip /path/to/coverage.json /path/to/controls.json
```

The archive and manuals stay outside the public repo. The adjacent directory
retains our decoder, controls, tests and compact derived observations.
