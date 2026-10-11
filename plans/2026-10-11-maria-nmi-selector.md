# Qualify the bypassed MARIA NMI selector path

Engineering-frontier research for the remaining #197 assertion/width gate.
POKEY schema approval is pending separately. This experiment changes no
production emulator or vendored RTL.

1. Extend our qualified populated-memory `fetch_tb.sv` harness with a separate
   observational latch following the reference's commented selector path:
   at MARIA phase 0, selector 6 asserts NMI and selector 0 releases it.
   Retain the reference's active NMI output and all existing fetch, ownership,
   raster and pulse inventory assertions. The candidate must not drive back
   into the reference.
2. Compare candidate and actual edges against HALT and CPU phases over fast/
   slow accesses, both regions, zone heights 1/2/3/16, unflagged/all-flagged/
   second-only flags, and empty/populated direct/indirect lists. Reject unknown
   selector state. Report missing, extra and misplaced candidate pulses;
   do not hide them by accepting only successful configurations.
3. Verify a suppression negative fails a nonzero event assertion. Record
   reference identity, adapters, build status and case inventory. Preserve our
   harness/generator and concise observations in this docs repo.
4. Use the result to determine whether that bypassed network is a useful
   additional timing witness. It is not automatically the production chip:
   the source gate diagram is a combined TIA/MARIA design and the FPGA
   includes other startup/shutdown overrides. Do not choose a production NMI
   phase unless the evidence supports the claimed hardware relationship.

Primary sources: [GCC1702B acceptance specification](https://7800.8bitdev.org/images/5/58/Gcc1702b_maria_specs.pdf)
PDF page 14 (one CPU-cycle pulse, one cycle after HALT release),
[Atari 7800 software guide](https://7800.8bitdev.org/index.php/7800_Software_Guide)
Appendix 3 (one 7.16 MHz cycle after DMA shutdown), and the
[1984 TIA/MARIA gate-level logic](https://7800.8bitdev.org/images/4/44/TIA-Maria_Gate-Level_Logic_Diagrams.pdf)
PDF pages 17 and 46 (selector network and combined HALT/NMI pad).
The differing shutdown boundaries and chip revisions remain explicit;
these statements are not interchangeable.

## Result

All 816 cases retain the baseline fetch, graphics, clock, ownership and active
NMI checks. The separate observer produces 3,400 complete pulses, with no
missing/extra pulses, wrong-zone assertions, assertions during HALT, or pulses
left active. Suppressing the observer fails the same event gate:

```text
selector inventory: expected 24 complete pulses, got {'assertions': 0, 'releases': 0, 'final': 1}
```

| Observed output | Fast assertion delay | Slow assertion delay | Pulse width |
| --- | --- | --- | --- |
| Bypassed selector latch | 3, 4, 5, 6 native ticks | 3, 4, 5, 6 native ticks | 2 or 6 native ticks |
| Active reference output | 15, 17, 18 native ticks | 17, 19, 20 native ticks | 16 fast, 24 slow |

Delays are measured from the reference HALT pad's release. The selector's
pulse inventory and upcoming-zone ownership agree with the active output,
but its width is not the specification's one CPU cycle. Restoring this
commented network alone therefore does not resolve the physical timing gate.
The reference also changed its selector inputs and HALT timing in commit
`6540304b548da6d37c3f97452f71aea09592f2a2`; this observer is not a reconstruction
of the standalone production chip.

## Reproduction

Use MiSTer Atari7800 revision `29aaacbbed127c670972c8a0a950ca82dc87e5df`
and the qualified temporary RTL from the
[clock handoff probe](2026-10-10-maria-clock-handoff.md). This retains the
populated-memory bus handoff and the explicit reset of `noslow`. Run:

```sh
python3 plans/2026-10-11-maria-nmi-selector/capture_selector.py \
  /path/to/Atari7800_MiSTer/rtl/Maria \
  /path/to/qualified \
  /path/to/output
```

The runner verifies its reference/adaptation hashes before compiling, checks
compiler and simulation status, rejects incomplete result inventories, and
checks all 816 distinct configurations. It records the bench hash alongside
its inputs. The retained matrix, summaries, example traces, build log and
suppression failure are in the adjacent evidence directory. The complete raw
logs can be regenerated; third-party RTL is not copied into this repository.
Ruff formatting and lint pass. No production NMI change follows from this
experiment.

## Next evidence source

The [GCC MARIA archive](https://7800.8bitdev.org/images/0/06/GCC_MARIA_Chip_Layout_and_Netlist_Artifacts.zip)
contains readable standalone-chip factory test programs and pattern sources.
`MARIAS/MARIAC/REV0/Z5349.2SC.1` identifies the C025349 MARIA-C final test,
dated 6 June 1984, with distinct HALT and NMI pads. This provides another
primary source to investigate. It is not a physical capture or an already
qualified timing oracle. Follow the [bounded qualification plan](2026-10-11-maria-factory-patterns.md)
before using those patterns to settle the NMI schedule.
