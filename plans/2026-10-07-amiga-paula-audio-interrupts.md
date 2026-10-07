# Paula audio interrupts and CPU-fed playback

Lane: best-in-class Amiga accuracy campaign. The preceding modulation fix is
merged. This change closes DMA interrupt timing; manual playback remains separate.

1. Execute vAmiga register, transition, event and audio-IRQ methods with an
   explicit scheduler adapter. Observe INTREQ visibility independently of the
   internal request call. Compare original HRM pages 164–166 and UAE source.
2. Add public-interface native regressions in
   `crates/emu198x-commodore-paula-8364/tests/audio_interrupt_timing.rs`.
   Exercise DMA wrap at several byte phases and attachment modes; manual DAT
   startup with clear/set IRQ; acknowledgement before/after word boundaries;
   and DAT writes during playback. Retain exact CSV, producer code and source
   hashes in `test-data/commodore/amiga/paula-audio/interrupt-probe/`.
3. Localise mismatches before changing production code. Describe the concrete
   existing-stage extension and saved fields if the current state cannot
   express pending conditions. Obtain approval for any additional snapshot
   schema or pipeline-design change before implementing it.
4. Validate both DMA entry paths, all Paula tests, relevant board tests and
   live runtime snapshot replay, plus the independent waveform gate, release
   build, formatting and strict Clippy. Preserve evidence boundaries: a
   component scheduler adapter is not a hardware or complete-machine trace.

Initial source finding: native DMA word acceptance raises loop interrupts
immediately, whereas vAmiga latches intreq2 until the selected byte transition
and AUDxIR schedules INTREQ one CCK later. Native CPU DAT writes restart the
counter without entering the reference's manual-playing state or consulting
pending INTREQ. These are source discrepancies pending executable proof.

## Executed reproduction

The native tests fail against the compiled reference: 1,744 of 4,896 DMA
observations and 396 of 480 manual observations disagree (116 scenarios,
5,376 observations). DMA interrupt visibility is up to 32 CCKs early. Ordinary
manual DAT startup leaves the DAC unchanged until the first period expires,
rather than presenting the high byte at the write; its startup interrupt is
missing. Pending INTREQ does not inhibit startup, and active DAT writes restart
the counter instead of updating only the holding latch.

The test windows distinguish reference limits. The reference's experimental
sampler suppresses some repeated sample edges, so manual capture stops at
clock 23. UAE also samples manual pending IRQ one CCK before the final word
boundary while vAmiga reads it at that boundary. Exact-boundary acknowledgement
is deliberately not asserted and needs an additional reference/hardware probe.

## Approved bounded design

First correct the DMA interrupt path. Add a per-channel pending loop-interrupt
latch (the reference's intreq2) to the existing audio stages. A wrapped data
word sets it; the next eligible byte transition consumes it according to the
attachment mode. Carry the resulting audio IRQ through a saved one-CCK request
stage before exposing it in INTREQ. Include startup audio IRQs in that same
request stage so their visibility is not immediate either.

Advance the IRQ stage at the existing shared CCK boundary before retained DMA
service, then run the existing audio output stage at its normal position. The
combined component tick must wrap these same beginning/end phases. This avoids
an IRQ requested by DMA retirement becoming visible in the same CCK and adds
no second clock. The implementation and board tests must verify both paths.

Expose the pending condition/request in diagnostics and retain them in Amiga
snapshot version 58, rejecting version 57. The programmed registers and
sample-buffer fields remain in their existing stages. Test live restore before
and after the selected byte edge and before INTREQ delivery, across OCS/ECS/AGA.

Alternative: infer or pack pending interrupts into the existing period/request
counters. Do not choose it: a DMA wrap can occur at several phases with the same
counter value, and pending delivery must survive save/restore independently.
Explicit saved state makes those independent conditions inspectable.

Manual playback uses the same missing IRQ delivery stage, but should remain a
separate correction after DMA closure. Reuse the existing Idle/Playing states
for CPU-fed playback, gate startup on pending INTREQ, load the first high byte
on DAT startup, and preserve the running interval on active DAT writes. Resolve
the one-clock acknowledgement disagreement before implementing the stop edge.

AGENTS.md requires agreement for “Breaking changes to APIs or data schemas”
and significant pipeline-design changes. Earlier approvals covered snapshot
57's period counter, not these additional retained interrupt stages.

## Independent test-program lead

The upstream vAmigaTS repository at revision
`bdbc379862f5a1de6f5e9c8c298597c0079a4942` contains
`Paula/Audio/timing/audtim1` through `audtim7` and `dmatim1` through `dmatim8`.
Its README describes Copper-triggered AUD0DAT writes and colour bars showing
interrupt-handler timing; the DMA variants exercise DMA-fed audio. These are
candidate independent guest probes, not yet executed or admitted as hardware
evidence in this investigation. Inspect their source and provenance before
using them to resolve the acknowledgement-boundary disagreement.

The preceding modulation PR #1658 and its companion documentation/reference
PRs merged after all configured CI checks passed. The user approved the version-58 DMA interrupt stages on 2026-10-07.
Implementation and local validation are complete. The manual reproduction remains
a separately runnable research probe until its acknowledgement boundary is resolved.


## DMA result

The approved extension closes all 1,744 DMA mismatches: all 4,896 reference
observations now agree. The combined and retained component paths agree across
72,000 ticks. All four live-board startup channels show no INTREQ at retirement
or halfway through that CCK, followed by delivery at the next boundary.

The component suite passes 109 tests. The board suite passes 40; runtime checks
pass 56 library, 45 query and 62 snapshot tests. Restore covers 48 checkpoints
across four attachment modes and OCS/ECS/AGA, including startup request, held
loop condition, pre-edge and delayed loop request. Every replay must deliver a
new INTREQ and reproduce the complete saved machine state. The independent
three-case waveform gate retains its routing, cadence and volume results.

The reference producer regenerates the exact retained CSV. Strict Clippy and
Ruff pass, and the release Amiga build succeeds. The manual research probe still exits nonzero with differences
`[64, 64, 96, 92, 80]`, preserving all 396 unresolved observations. Its command
is documented in the corpus README; no shipped regression is ignored or removed.
