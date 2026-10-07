# Paula DMA/manual handover

Lane: best-in-class Amiga accuracy campaign. Start from the merged version-59
manual-playback correction. The user asked to investigate the remaining
handover between DMA and CPU-fed output.

1. Trace DMACON changes during idle, startup waits, high and low byte output
   in the HRM, pinned WinUAE and vAmiga. Establish whether a DMA edge changes
   output phase, pending requests, holding data or interrupt delivery.
2. Add an executable reference adapter under
   `test-data/commodore/amiga/paula-audio/handover-probe/`, reusing the existing
   extracted methods. Sweep edges around sample boundaries on all channels,
   with explicit input/IRQ/output order. Preserve reference disagreements.
3. Add a native research reproduction in
   `crates/emu198x-commodore-paula-8364/examples/dma_handover_probe.rs`.
   Record nonempty scenario counts and a failing output/IRQ trace before
   proposing the smallest correction to `src/lib.rs`.
4. If the measured fix fits the existing approved stages and saved fields,
   implement it with a regression in `tests/dma_handover.rs`. Any new saved
   stage, schema break or binding-decision conflict needs a concrete design
   and agreement first. Do not extend attachment switching or analogue scope.
5. Validate component reference closure, shared-board handover timing and
   OCS/ECS/AGA restore as applicable. Run the existing DMA/manual reference
   suites, ROM-backed waveform gate, release build, formatting and Clippy.
   Record primary observations before codebase-tied conclusions.

Initial hypothesis: `AudioChannel::sync_dma_enable` calls `start_dma` or
`stop_dma` for every edge; both discard the current output phase. WinUAE keeps
states 2/3 when DMA changes, unless an explicitly disabled compatibility hack
forces a restart. This is source evidence, not yet a reproduced native result.

## Reproduced result

The compiled references produce 12,608 observations in 1,408 scenarios each.
Native compares all 6,304 pre-output observations (704 scenarios), reproducing
2,552 sample/IRQ differences, 236 held-loop differences and 3,420 state
differences. The counts overlap. Sample/IRQ failures by schedule are
`[240,264,268,228,408,408,328,408]`; the probe exits 101. Existing production
code is unchanged, all 112 component tests pass and the research example is
strict-Clippy clean. Ruff and formatting pass.

The HRM p.166 state diagram was rendered and inspected. It confirms that
DMA-off exits startup waits immediately but does not unconditionally exit
playing states. WinUAE agrees with this; vAmiga stops those states immediately.
Minimig retains playback states but has a separate silence workaround, so its
raw output is not a DAC reference for this purpose.

Period 8 gives a decisive saved-state case. A low byte entered with DMA on,
disabled at 9, continues when IRQ clears at 16. A low byte entered manually,
with DMA enabled at 9 and disabled at 10, stops despite the same clear at 16.
The latter scheduled an early sample at 15; the former did not. Both have the
same current DMA setting and byte/countdown by then. Version 59's saved
`manual_stop_pending` cannot distinguish these two unsampled histories.

## Proposed bounded correction — awaiting approval

1. Preserve the existing Playing state, output buffer, holding word and
   period countdown on DMA mode changes. Use the existing startup path only
   when enabling from Idle; disabling a startup wait still returns to Idle.
2. Extend the existing low-byte stage with `manual_stop_sample_pending: bool`.
   Arm it only on manual low-byte entry (period 1 samples on entry). Retain
   its scheduled event through mode changes. At its one-CCK-remaining event,
   capture `!dma_active && visible_irq` into `manual_stop_pending`, including
   false, and clear the pending sample flag. At a manual final boundary,
   consume the saved decision or use visible IRQ if no sample was scheduled.
   Clear/recreate the phase fields only on real low-byte entry or idle startup.
3. Preserve a held loop condition across a DMA-off pulse, and deliver it at
   its eligible DMA output edge. Keep issued IRQ delivery independent. Trace
   existing retained DMA retirement before changing request handling; do not
   infer Agnus request timing from this component adapter.
4. Add the sampling-phase field to diagnostics, all four query leaf paths and
   Amiga snapshot version 60; reject version 59 before decoding. Validate both
   histories and saved sampled values across OCS/ECS/AGA half-CCK restore.
5. Promote handover regressions for the corrected scope, update the existing
   stop/loop regression to assert the measured invariant, and preserve the
   startup-wait and DMA/manual reference suites. Verify board mode writes and
   admitted fetches separately, then waveform, release build and strict Clippy.

Files: Paula `src/lib.rs`, `tests/dma_handover.rs`, existing
`tests/audio_interrupt_timing.rs`, the research example/corpus;
`machine-commodore-amiga-ocs/tests/paula_phase2_machine.rs`;
`runtime-commodore-amiga/src/variants.rs`, `src/snapshot.rs`,
`tests/snapshot_roundtrip.rs`; and the binding
`knowledge/decisions/amiga-paula-audio-interrupts.md`.

The binding decision currently says: “Stopping DMA discards an unissued loop
condition”. Amend it to distinguish a DMA-off edge from a real playback stop:
“DMA mode changes preserve the active byte pipeline and its scheduled sampling
phase. A DMA-off edge does not discard a held loop condition or an issued IRQ;
consume the held condition at its eligible DMA transition.” This is a proposed
record update, not an adopted rule. Primary evidence is recorded first in
`reference/by-system/commodore-amiga/2026-paula-dma-handover-observations.md`.

Alternative: fix only enabling during manual playback using existing fields,
and defer DMA-off continuation. That can close the agreed enable-only cases
without a schema change, but leaves the measured handover failures. Alternative:
resample all low bytes after every mode change. This cannot preserve the
reference's two distinct histories and is rejected by the paired trace.

Recommendation: extend the existing stage and version saves. The root AGENTS.md
requires agreement for “Breaking changes to APIs or data schemas”; the binding
decision's loop-discard statement also needs explicit amendment. Approval is
needed before production changes. No new dependency or independent clock is
proposed. Live attachment switching and analogue/PWM work remain separate.
