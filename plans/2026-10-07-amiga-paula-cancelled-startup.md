# Paula data delivery after startup cancellation

Continue the approved Amiga accuracy campaign by tracing a retained Agnus
audio transfer that reaches Paula after DMA startup has been cancelled.
The user approved this investigation and bounded correction. No new clock,
dependency or architectural pattern is proposed.

1. Reuse the pinned WinUAE/vAmiga extraction under
   `test-data/commodore/amiga/paula-audio/`. Execute cancellation in both
   startup waits, with IRQ clear/set, on all channels and several periods.
   Record real reference transitions and their limits in the primary Amiga
   reference library before deriving implementation expectations.
2. Reproduce through `service_audio_dma_word` and the existing board
   `paula_phase2_machine.rs` retained-descriptor instrumentation. Compare
   an already-cancelled channel receiving a retained word with its ordinary
   AUDxDAT input, then check samples, IRQs, address and length separately.
   Preserve a failing result before changing production code.
3. Correct only the reproduced DAT-delivery path in
   `crates/emu198x-commodore-paula-8364/src/lib.rs`, using existing state and
   interrupt stages if the evidence permits. Do not infer all DMAL request
   timing from a component adapter. A new saved stage or changed public
   contract requires a concrete design before extending this scope.
4. Add regression coverage at component, board and runtime snapshot levels:
   `crates/emu198x-commodore-paula-8364/tests/`,
   `crates/machine-commodore-amiga-ocs/tests/paula_phase2_machine.rs`, and
   `crates/runtime-commodore-amiga/tests/snapshot_roundtrip.rs`.
   Restore before and after delivery on OCS/ECS/AGA, including half CCKs.
5. Run affected tests, strict Clippy, formatting, release build and the
   existing ROM-backed waveform gate. Preserve reference and validation
   evidence; commit one bounded correction, run CI, then merge when green.

Hypothesis: cancelled startup enters Idle, but `accept_dma_word` only updates
DAT there. The ordinary DAT path can start manual playback when IRQ is clear.
This difference is not yet proof of incorrect board behaviour or timing.

## Reproduction and bounded design

Both pinned references agree on all 704 observations. The ordinary CPU DAT
control matches them; the admitted-word path disagrees in 544 rows. The real
board probe additionally fails `startup cancellation must precede delivery`:
DMACON has changed in Agnus, but Paula is notified only after retirement.

Use a public additive `sync_audio_dma_control(dmacon)` entry point to apply
existing channel mode transitions without advancing time. Call it at the
existing effective DMACON register write in the OCS/ECS/AGA wrappers; the
component combined tick continues to use it. This preserves the current
register-effect convention rather than inventing a physical write delay.
For a retained DMA-off delivery, advance the retained memory pointer, then
route DAT through `write_audio`: do not decrement/reload the length counter,
raise a DMA loop condition, or bypass the existing manual-start IRQ gate.
The existing saved stages represent this exactly, so version 60 remains valid.
No snapshot schema or existing public signature changes are needed.

## Validated result

Both native paths now match all 704 reference rows; the 544 retained-delivery
mismatches are closed. All 114 component tests and 44 board tests pass.
The runtime suite passes, including all 65 snapshot tests. The new regression
replays 192 snapshots across OCS/ECS/AGA, all four channels, both startup waits,
both IRQ states, and whole/half CCKs around retained-word delivery.

Strict Clippy, Rust formatting, Ruff, the release build and all three ROM-backed
waveform cases pass. Routing, measured sample cadence and full/half-volume RMS
are unchanged. Exact producer regeneration matches the committed reference
artifacts. Baseline and final logs with hashes are preserved in the corpus.
The implementation adds no dependency or saved field; snapshot version 60
remains compatible. Complete DMAL timing, physical register-write latency and
same-clock input priorities remain separate investigations.
