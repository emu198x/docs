# MARIA interrupt scheduling choice

The emulator now follows the recovered original controller's sampled digital
stages. It does not follow the FPGA reference's replacement two-cycle pulse,
and does not choose a wall-time delay to fit the guest counter.

## Evidence and decision

The primary source record is
`198x/reference/by-system/atari-7800/gcc-maria-layout-evidence.md` and
`maria-dma-timing-evidence.md`. The pinned GCC layout supplies the controller's
input/output pass banks, feedback paths and NMI latch. Direct retained-device
replay has independently checked the staged model's transfers and capture order.
The reference FPGA remains the source for already-qualified DMA/bus/clock
captures, but its active NMI path bypasses this controller and holds the output
for two CPU periods. That replacement is weaker evidence for the original
interrupt logic than the original design itself.

The GCC specification explicitly gives a one-CPU-cycle pulse. The recovered
controller gives the same width. Its assertion sequence has an additional
sampled stage; the specification's phrase “one cycle after” does not define
both sampling boundaries or separately identify that cycle's clock domain.
We preserve the original controller's stages rather than deleting a stage to
force a literal elapsed-time reading of that sentence. The difference remains
visible in the primary evidence; this is a choice of digital model, not a
claim that the prose and circuit have become identical.

At the emulator's native observation granularity, a MARIA cycle is two
oscillator periods and an ordinary CPU cycle is four MARIA cycles. The
retained trace therefore has one observation per native period. Its absolute
origin is arbitrary: map the observed PCLK0 falling edge to the existing
CPU phase-1 strobe, and retain the physically traced input/output-bank order.
This is a relative digital mapping; no transistor propagation delay is inferred.

The export now proves a further useful invariance: replace the model's internal
edge term with the *observed PCLK0 falling edge*, and replace internal HALT
with the *observed HALT pad level*. The implemented controller still matches
all 32,832 cases, every observation, and all 16,416 pulses. This includes both
clock rates, both transition directions, both input orderings, both DMA request
sources, DLI clear/set, and all three assumed CPU-return delays. No empirical
HALT-to-NMI delay constant is needed. The compact corpus has 300 unique traces;
case multiplicities retain the complete matrix inventory.

## Implemented schedule

- In idle, a sampled CPU edge clears the output and arms the controller if
  HALT is active.
- While armed, HALT release without a DLI returns to idle. A DLI survives until
  the next sampled CPU edge, which advances to the assertion stage.
- The following sampled edge selects NMI assertion. The separate output bank
  and NMI latch preserve their actual capture order.
- The next sampled edge clears NMI through the same banks. Its width follows
  the live CPU clock, including a stretched transition, rather than a timer.

The descriptor flag feeds the request before shutdown; starting a new DMA
request clears the old flag so continuing zones cannot repeat it. Machine
wiring exposes the pin each native tick, independent of CPU execution or WSYNC.
All pending state belongs to the approved unreleased snapshot layouts.

## Qualification boundary

This adjudicates the production **digital scheduling model** using the original
circuit and the independently qualified native clock interface. It closes the
implementation choice that blocked replacing line-boundary delivery. The CPU,
vector, raster and continuation regressions additionally check its consequences.

It does not identify the archived layout's exact production revision, measure
analogue clock-generator non-overlap, or replace an oscilloscope capture from a
physical MARIA. These remain hardware-validation limits. The full chip cannot
be described as physically cycle-exact on this evidence. Issue #197 should keep
that narrower external-validation work visible after the functional correction;
#196 retains the separate external DMA timing-ROM qualification. Neither lack
of a supplied timing cartridge nor green synthetic guests is recorded as a
successful hardware timing test.

A revision-matched physical capture that contradicts the relative sampled
sequence would change this scheduling choice. The permanent trace corpus is
an implementation regression, not a claim that such a capture already exists.
