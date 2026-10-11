# MTX VDP/CTC/IM2 timing audit

Engineering-frontier work on source issue #267. The PSG tone corrections are
merged; the requested MTX known-program comparison and CTC interrupt path remain
unverified. The pending PSG and MC6809 schema designs are outside this task.

## Bounded steps

1. Obtain the community MEMU source as a read-only reference under
   `emulators/memotech-mtx/MEMU/`, record its revision/licence and update the
   existing per-system INDEX. MAME remains the existing second reference.
2. Inspect actual MEMU `ctc.c`, VDP/frame scheduling and `LoopZ80`, and the MAME
   MTX driver. Establish each oracle's observation granularity before claiming
   cycle accuracy; an instruction/frame-level model cannot prove sub-instruction
   latency. Consult shared primary CTC/MTX references for timing requirements.
3. Write a finite synthetic guest and a runtime probe for VDP `/INT` polarity,
   selected CTC edge, channel countdown, interrupt acknowledge/IM2 vector and
   RETI release. Observe actual CPU/bus/CTC flow through existing APIs or test
   hooks; avoid replacing a reference's interrupt scheduler with our own model.
4. Reproduce any discrepancy and explain its cause before changing production
   code. Write a bounded correction design first if needed; request agreement
   for genuinely new serialized stages/API/schema changes, not routine tests.
5. Retain generator/probe source, nonempty traces, exact reference revisions,
   failures and corrected checks. Update #267's requirements individually and
   close it only if its actual runtime verification is complete.

## Confirmed polarity correction

The guest programs CTC channel 0 in falling-edge counter mode with time constant
1, enables the VDP interrupt, selects IM2 and waits in HALT. On baseline main
`07d77cbac67fc3339997b1a65c273e5ba900207c`, it sees one VDP assertion but never
reaches its ISR: `model=Mtx500 vector=00 assertions=1 services=0`. The rising-edge
control incorrectly services and clears the asserted interrupt. Both regressions
fail (0 passed, 2 failed).

`Tms9918::interrupt` is an asserted flag, while `Ctc::set_trg` accepts an electrical
level. The MTX glue passes the asserted flag directly, reversing both edges.
MAME `mtx.cpp` uses `.invert()` on the corresponding VDP-to-TRG0 callback.
MEMU's CTC is triggered by a video pending transition; it does not model pin
polarity and is not an edge-timing oracle.

The bounded fix is to invert the flag in the existing MTX `before_tstate` wiring.
No fields, data types, snapshot versions or scheduling stages change. Verify the
complete ROM/I/O/IM2/RETI route for both MTX models and four vector bases, plus a
rising-edge negative control. Keep physical CTC latency and the known-program PSG
comparison open in #267; this fix cannot establish either one.

## Verification

- Both new integration tests fail on the original polarity and pass after the
  correction. The positive test covers both models and four vector bases (eight
  guest runs), each with two VDP assertions and two ISR visits.
- A separate negative control omits only the CPU's CTC RETI notification. The
  lower-priority-request assertion then fails, proving the RETI check is live.
  Corrected production source was restored byte-for-byte after each control.
- The full, unmodified MEMU `ctc.c` compiled with its actual headers and
  `-DLSB_FIRST`. Eight trigger/vector/RETI observations pass. This is a component
  probe with diagnostic and IRQ sinks, not a whole-MEMU runtime comparison.
  Initial compiler attempts lacked the Z80 include directory and endian define;
  the retained reproduction includes both required upstream build settings.
- 50 routine machine/runtime/CTC tests pass. Two copyright-ROM tests are ignored
  by the normal suite; both were separately run and pass with the installed
  24,576-byte OS+BASIC+ASSEM ROM, SHA-256
  `e93edd8490f320c1828f879460a857f393ce15213fa8d8cc853beb700bc71b0f`.
- Clippy with warnings denied, package formatting and diff whitespace checks pass.
- The manufacturer's CTC summary was checked as an image: Appendix 6ii, printed
  page 232/PDF page 235, including edge selection and vector bit placement.
  A separate attempt to retrieve the TI VDP PDF from Bitsavers returned HTTP 403;
  no new TI page-image verification is claimed.

Evidence and the reproduction script are in
[`2026-10-11-mtx-ctc-timing/`](2026-10-11-mtx-ctc-timing/).
Issue #267 remains open for physical edge-to-IRQ timing and known-program PSG
cadence. The approval-pending PSG phase/stereo stages are separate work.

## Integrated source

Source commit `2f6d5d91f19eecc767283e01fb0a51213d1aa862` is rebased onto main
`99c1862effd379e72df627e89e6ee8a1f2ce8254`, including the merged TI noise-slaving
correction (#1723). The 50 routine tests and warnings-denied Clippy pass again
on that integrated tree. The source PR must pass its own checks before merging.
The upstream source and snapshot designs requiring approval remain separate.
