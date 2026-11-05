# First CPC CPU-clock divergence on current main

Current main `79b5fc12e` reproduces the frozen v5 saves with CPU 0.8.
Changing only the two CPC CPU requirements and lockfile edges to 0.9 fails:

```text
amstrad-cpc464: full v5 state
```

The requested diagnosis already existed in [PR #2296](https://github.com/emu198x/emu198x/pull/2296).
This recapture verifies that result on the post-release tree; it introduces
no second machine-timing implementation.

## Observation

The project-written synthetic ROM runs for exactly 100 CPU half-cycle edges
on each of CPC464, CPC664 and CPC6128 under each CPU: 600 observed edges.
The observer samples immediately after the existing CPU tick and before the
existing bus handler. `hc` is the zero-based CPU-edge index. 

All three models produce the same comparison:

| Observation | CPU 0.8 | CPU 0.9 |
|---|---|---|
| State after edge 2 | M1 T2 rising repeats | M1 advances to T2 falling |
| First CRTC index write to BC00 ends | Edge 81 | Edge 87 |
| WAIT at the later I/O sample | Already asserted again | Already asserted again |

The first physical/architectural difference is after edge 81: 0.8 deasserts
IORQ/WR and retires the instruction; 0.9 retains both strobes and has not
retired it. WAIT, IRQ, CRTC phase and machine T-state counters match at every
observed edge. The CPU versions receive the same machine waveform.

CPU 0.8 samples I/O WAIT at its T2 falling state. CPU 0.9 samples after the
automatic TW, then repeats complete rising/falling TW pairs. The machine's
free phase has passed before that corrected sample; the CPU must wait for
the next free phase. Both cores keep the same machine cadence.

## Source checks and limits

- Zilog's held *Z80 CPU User Manual*, UM008011-0816, printed pp. 7 and 10,
  specifies falling-edge memory WAIT sampling and I/O sampling during the
  automatically inserted wait state (Figure 7). The plain-text source and
  provenance are `reference/by-topic/cpu-z80/zilog-z80-cpu-user-manual.*`
  in the umbrella. This is the held late Zilog printing, not period silicon
  measurement.
- The held CPC464 firmware guide, printed p. 1.2, describes memory-cycle
  synchronization and stretching to the microsecond grid. It does not
  establish a different phase for the CPC's physical WAIT waveform.
- Vendored MAME's `amstrad_m.cpp:2183` pads memory-cycle totals with
  `adjust_icount`; Arnold's `Z80_ExecuteInterrupt` returns 5/7 microseconds;
  Caprice32's interrupt handler uses 20/28 T-states. These are independent
  implementation checks, but none supplies a WAIT-pin capture that would
  justify retuning phase 2. Their identities are in
  `emulators/amstrad-cpc/INDEX.md`.
- The earlier [qualification](../2026-11-04-cpc-wait-evidence/README.md)
  retains the physical-reference review and remaining JP/NOP 11/5 and IM1
  19-T-state discrepancy. This recapture does not resolve that limitation.

## Reproduce and validate

`identity.json` records the base/integration revisions, CPU registry checksums
and the synthetic firmware/observer hashes. Apply `observer.patch` to the base
revision in an isolated checkout. Run:

```sh
CPC_WAIT_OBSERVE=1 cargo test --locked -p common-amstrad-cpc --lib \
  wait_observer -- --nocapture
```

Run once with original CPU 0.8 and once changing only the two direct CPC
requirements/lockfile edges to published 0.9. The observer adds no clocks or
signal writes. It was removed before testing integration. `trace.json` retains
the complete bounded records; `comparison.json` retains both sides of each
first difference.

```sh
python3 verify.py
```

The verifier requires both versions, all three models, exactly 100 consecutive
edges per case, consistent machine clocks and the retained divergence edges.
Missing an edge, substituting identical CPU traces, and altering WAIT each
fail independently; `controls.json` records their nonzero exits.

## Integration verification

PR #2296 applies cleanly to current main as local integration `06be84c7f`.
Its separately approved v6 policy rejects v4/v5 before payload decoding or
mutation and preserves every original file; it is not a relabelled v5 golden.
The existing public verifier matches all eighteen old/new specimen hashes and
requires a nonempty CPU graph containing only 0.9 on the CPC path.

Fresh verification: 104 common/runtime/board tests and 14 headless-runner tests
pass, along with Clippy (warnings denied), formatting and diff checks. The
16 fixture-gated tests remain explicitly ignored in this ordinary run; their
earlier explicit firmware/disc/tape/SHAKER results are retained in yesterday's
qualification and are not counted as newly rerun tests.

PR #2296 merged as `9d9f756a681c9a04a64f44fbd18ad05f52e82895`. Its tree
exactly matches the tested integration tree; the public verifier also passes
on the merged source. Issue #2284 is closed.
