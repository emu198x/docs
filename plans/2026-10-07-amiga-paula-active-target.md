# Verify modulation into running Paula channels

Continue the approved Amiga accuracy campaign. The user selected a comparison
of simultaneous and adjacent modulation/reload transitions, including chains.
Previous attachment probes left target playback idle. Keep pending local
commits and defer pushing as already requested.

1. Add `test-data/commodore/amiga/paula-audio/active-target-probe/reference.py`.
   Reuse the pinned handover extraction. Advance every active channel using
   WinUAE's and vAmiga's inspected channel 0-to-3 event order. Cross source
   channels 0/1/2, manual/DMA playback, ordinary/volume/period/both attachment,
   single and chained attachment, source periods 2/8/124, target periods one
   clock before/equal/after, and modulation words 0/1/8. Observe all channels'
   period registers, time to next byte edge, state, buffer, raw sample, volume
   register, request and IRQ. Normalize WinUAE's manual early-IRQ event to the
   actual byte deadline; retain vAmiga sampler disagreements separately.
2. Add `crates/emu198x-commodore-paula-8364/tests/active_target.rs` against the
   checked-in WinUAE CSV. Require exact nonempty inventories and preserve the
   failing baseline before touching production. Keep extraction provenance and
   original upstream methods intact. Read HRM audio state-machine context and
   both reference schedulers; do not present emulator agreement as hardware
   capture evidence.
3. If the suspected ordering error is reproduced, correct only the existing
   `finish_audio_cck` transition order in
   `crates/emu198x-commodore-paula-8364/src/lib.rs`: apply each channel's
   request/IRQ/modulation effects before the next channel evaluates expiry.
   No extra ticks or saved fields are anticipated. Record the measured cause
   and bounded design before implementing; stop for agreement if evidence
   requires a new saved stage, public schema or architectural pattern.
4. Add a representative running-target board/restore regression in
   `crates/runtime-commodore-amiga/tests/paula_active_target.rs`, covering
   OCS/ECS/AGA and whole/half-CCK snapshots. Verify the audible target edge,
   not merely its period register. Run existing component, Paula board and
   runtime tests, strict affected-package Clippy, release build and ROM-backed
   waveform gate. Confirm the oracle checker rejects a corrupted observation.
5. Record evidence first in
   `reference/by-system/commodore-amiga/2026-paula-active-target-observations.md`
   using the isolated reference worktree; cite it from the existing Paula
   decision. Update this plan and commit the bounded work locally. Complete
   DMAL, physical register latency and analogue/PWM response stay out of scope.

## Baseline and correction design

The matrix executes 88,704 observations across 1,296 scenarios. Both references
agree on all compared outputs except their differently defined sampler
columns. Native mismatches in state/period/counter/buffer/sample/volume/request/
IRQ order are `[3876, 0, 4872, 424, 3866, 424, 0, 621]`, including 2,584
unmuted samples. Every ordinary-playback control matches. The component test
finishes its exact inventory and fails with those counts.

The cause is the deferred `output_events` array in `finish_audio_cck`:
receivers expire and reload before sources apply their new period. Replace
that deferred pass with applying the same effects directly after each existing
channel transition. Keep begin/finish clock phases, request and IRQ logic,
manual stop sampling, and snapshot version 60. This implements the bounded
ordering correction already described above, with no public API/schema change.

The old archive paths listed in RULES.md are absent. The frozen donor search
found only older Paula notes/tests; this work reuses the current pinned probe
chain and does not port chip code from the donors.


## Board fixture correction

The initial board fixture incorrectly expected one-CCK manual playback to
continue indefinitely while acknowledging IRQ before `begin_audio_cck`. The
trace shows it correctly samples the newly delivered IRQ at CCK 10, enters
Idle at 11 and retains the low sample. The corrected fixture asserts that stop
as well as the period-one reload and audible high/low transitions at CCKs
8–10; it keeps all later output checks and the full restore replay. Validate
this final fixture against the original production ordering as a fresh red
control, then restore the corrected source byte-for-byte and rerun the gates.
This is a test expectation correction, not a second production behavior fix.


## Verified correction

The production change removes the deferred output-event pass and applies the
existing request/IRQ/modulation effects immediately after each channel's
transition. All 88,704 observations now match WinUAE across all eight outputs;
both references continue to agree on their seven directly comparable outputs.
The sampler difference remains explicit because vAmiga scales samples and
suppresses repeated edges. The 2,584 baseline sample mismatches count channels
with attachment muting off, without weighting by volume.

The final board fixture rejects the original ordering at all 36 checkpoints
and passes with the corrected source restored byte-for-byte. The saved state,
IRQs, raw samples, audible stereo output and final snapshot bytes replay
identically on OCS/ECS/AGA. This includes the expected manual stop at CCK 11.
A separate regeneration matches every committed reference artifact exactly.
The enforced checker rejects both empty input and one corrupted deadline;
the latter completes all observations and reports exactly one counter mismatch.

Snapshot version 60, public APIs, dependencies and board clock phases remain
unchanged. The independent gain/volume-output latch, physical write latency,
full DMAL and analogue/PWM behavior remain outside this correction.


Final validation passes: 119 component tests, 44 Paula board tests, 298 runtime
tests (30 existing ignored diagnostics), including all 65 snapshot tests.
Strict affected-package Clippy, the Amiga release build, Rust formatting,
Ruff and the explicit three-case ROM-backed waveform gate pass. Waveform
routing, paired-volume levels and 3463.2276054374347 Hz cadence are unchanged.
Logs, baseline counts and hashes are retained in the new corpus's
`validation.json`. Code, evidence and this plan are committed locally;
pushing remains deferred at the user's request.
