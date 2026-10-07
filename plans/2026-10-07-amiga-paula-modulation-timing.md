# Paula modulation transition timing

Lane: best-in-class Amiga accuracy campaign. Continue after the approved
period-counter correction; this investigation starts from that change.

1. Execute unmodified vAmiga startup and steady-state transition methods,
   including their buffer-load and attachment methods, with a scheduler and
   DMA-request recorder. Compare UAE and the original HRM state diagrams.
   Keep all external scheduling assumptions explicit.
2. Add a native public-interface regression in
   `crates/emu198x-commodore-paula-8364/tests/audio_modulation.rs`, covering
   ordinary, period-only, volume-only and combined attachment for all four
   source channels. Observe startup, both transition directions, target
   register values and DMA requests with changing input words.
3. Localise any failure before editing
   `crates/emu198x-commodore-paula-8364/src/lib.rs`. Prefer the existing
   register, byte-phase and DMA stages. Agree any additional saved state,
   API/schema change or pipeline redesign before implementation.
4. Retain producer revision, source hashes, generated adapter, input/output
   rows and native before/after logs in
   `test-data/commodore/amiga/paula-audio/modulation-probe/`. Record new
   observations in the primary reference library, citing them from the
   emulator decision. Do not claim hardware calibration from component probes.
5. Validate all Paula tests, the board-level audio tests and independent
   waveform gate. Add live restore checks if saved stage behaviour changes;
   run the relevant runtime tests, release build, formatting and strict Clippy.

Initial source comparison suggests period/volume events and steady DMA
requests use reversed byte phases. Startup always requests a word and does
not deliver attached volume. Native modulation reads an output-event word;
the reference reads the current AUDxDAT holding latch. These remain hypotheses
until the executable probe reproduces them.

## Reproduction and bounded correction

The compiled reference produces 720 observations across 48 scenarios: all four
source channels, all four attachment modes and periods 1, 8 and 124. The native
regression fails before production edits with mismatch counts 120 ordinary,
144 period-only, 165 volume-only and 135 combined (564 total).

The correction reuses the existing byte-phase, AUDxDAT and request state:
request on high-byte entry for ordinary/volume modes and low-byte entry for
period attachment; suppress the startup request for period-only mode; deliver
startup volume; source attached words from AUDxDAT. No field or schema change
is needed. Both DMA entry points must use identical startup behaviour.

## Delayed delivery and buffer boundary

The initial correction matches all 720 immediate-grant observations. Extending
the adapter to five-CCK grants produces 96 scenarios / 1,440 observations and
exposes 36 additional differences: request accumulation and loss of byte phase
when the buffer empties. Coalescing AUDxDR and retaining the output word closes
those differences. A separate late-arrival test fails at clock 16 (observed
sample 17, expected 51), proving that the holding/output transfer must happen
on high-byte entry, not on the preceding low byte. Arrival clocks 9, 12 and 15
are checked, followed by continued buffer repetition.

All changes still reuse existing saved fields and stages. Manual playback
startup/IRQ handling and live attachment-bit switching remain outside the
claim. The earlier period-counter PR #1657, docs #8 and reference #52 merged
after all configured checks passed.

## Final validation

All 1,440 reference observations agree. All 107 Paula component tests, 39
board-level tests, 56 runtime library tests, 45 query tests and 61 snapshot
tests pass. The new live restore test covers 18 byte-transition checkpoints
across OCS, ECS and AGA and requires real target changes and DMA activity.
The two component DMA entry paths agree over 72,000 ticks. The independent
three-case waveform gate retains its previous routing, cadence and volume
measurements. Strict targeted release Clippy, release Amiga build, Rust
formatting and Python checks pass. Regeneration reproduces the reference CSV
and C++ byte-for-byte.

The initial component suite also exposed an old diagnostic test expecting the
CPU's previous AUDxDAT write after DMA had replaced it. Its assertion now uses
the actual DMA word; both the failure and passing rerun are retained. The
runtime test uses existing diagnostic fields, without adding a chip dependency.
All artifacts and hashes are in the modulation-probe corpus. Snapshot version
57 remains unchanged.
