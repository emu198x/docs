# MARIA reference comparator diagnosis

Continue issue #197 after the CPU defect and reference limits recorded in
`2026-10-10-maria-dli-pulses.md`. This is engineering-frontier validation work.
This evidence precedes the separately approved correction in
[`2026-10-10-maria-timed-dma-design.md`](2026-10-10-maria-timed-dma-design.md).

## Root cause and plan

The two-line trace first fails when OFFSET changes from zero to one. At that
point cond2 is the fully known value $2887: its procedural wildcard comparison
returns true, but the identical continuous comparison produces X. A standalone
split-driver reproducer demonstrates this in Icarus Verilog 13.0 without any
MARIA code. A single-driver control passes.

1. Retain both reduced simulator reproducers and the decisive transition trace.
2. Generate a temporary reference copy replacing only continuous comparisons
   against constant wildcard patterns with equivalent masked comparisons.
   Never edit the vendored RTL. Preserve all clocks, registers and DMA logic.
3. Check the replacement against the original procedural comparisons for every
   known 5-bit/14-bit input and a deterministic four-state input sample. Include
   a negative control that changes a significant mask bit.
4. Re-run the original full-DMA 48-row sweep without adjusting its clock or
   stimulus. Require all DMA completion and NMI invariants; keep the suppression
   negative control. Record reference hashes and source identity.
5. Only use the resulting traces to choose the next timing design after the
   oracle checks pass. Preserve any remaining disagreement with the primary
   guide's shutdown-to-DLI statement; do not close #197 on reference success.

## Results

The simulator adaptation passes 1,011,936 comparisons against the procedural
wildcard operator: all known inputs plus 4,096 deterministic four-state inputs
per width. The significant-mask-bit negative control fails. The original
48-row DMA testbench now passes all 48 rows, with 40 DMA starts and completions
per row. The 12 previously passing one-line logs are byte-for-byte unchanged.
Suppressing NMI in a 16-line zone still fails with zero edges instead of one.

The split-driver reproducer fails with `continuous wildcard differs from mask
on split-driven vector`; the single-driver control passes. This localises the
original 36 failing rows to Icarus's continuous wildcard comparison, rather
than to a MARIA reset, memory, or clock change.

The preparer replaces exactly 55 continuous constant-pattern comparisons
(seven selector terms and 48 DMA terms). Its inventory guard rejects partial
matches. It leaves procedural comparisons, state, clocks and DMA logic intact.
Generated reference RTL and generated comparison tables remain temporary local
artefacts; this repository retains our preparer, minimal reproducers and logs.

For a flag only in the second descriptor, all four heights (1, 2, 3, 16) fire
at the preceding zone's shutdown. Across start phases 0, 2, 4, 6, the NMI falling
edge is at dots 66, 64, 70, 68 respectively. HALT release precedes it by 17
supplied ticks; pulse width is 16 ticks. These are observations of the FPGA
implementation, not proof of physical MARIA timing. The original Atari guide
states a one-MARIA-cycle delay; that discrepancy remains an implementation
gate. This sweep's 912-tick line interval is controlled stimulus, not a raster
length assertion: the reference `video_sync.sv` uses 908 native ticks.

## Provenance and reproduction

Reference: Atari7800_MiSTer revision
`29aaacbbed127c670972c8a0a950ca82dc87e5df`, `rtl/Maria/DMA.sv`.
Original SHA-256:
`d86608b30af23821ef252cdff61c93f8effdd0e25fab18f06111fa831df1c8fc`.
Simulation-only generated SHA-256:
`b055738d86d2d936044b158fb280789df04961a284687c1ff7908b01ad620704`.
The vendored original remains unchanged. Simulator: Icarus Verilog 13.0 stable.

Run `prepare_rtl.py ORIGINAL_DMA_PATH OUTPUT_DIRECTORY`, compile its generated
`comparator_tb.sv` with `iverilog -g2012`, and run with `vvp`. Repeat preparation
with `--negative-control` for the failing comparison check. The sweep runner and
unaltered `dma_tb.sv` are retained beside the preceding DLI plan; pass the
prepared `DMA.masked.sv` as its reference argument. All commands must check
process status and nonzero case inventory.

[Evidence directory](2026-10-10-maria-dli-oracle/) includes the comparator
results, both minimal reproducers, original failing transition, sweep summary,
16 descriptor-boundary traces and the NMI-suppression negative.

The vendored `F15_Atari7800.pdf` is a 2015 CMU student project report, not an
Atari service manual. Its stated VGA conversion changes DMA timing; it is not
used to adjudicate the physical assertion delay.
