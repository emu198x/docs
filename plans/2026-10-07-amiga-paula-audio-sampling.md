# Preserve Paula output between host samples

Continue the approved Amiga accuracy campaign. The user requested correction
and continued investigation. Keep all work local; pushing remains deferred.

1. Recheck volume-path provenance. WinUAE commit
   `141f6bc7af878ac8f92b9d9550745ab5fc6de3a1` introduced PWM as "not working";
   `703671920406c7406c0f405073201ef17867bc27` removed its GUI checkbox.
   Record these limits in the primary volume note. Do not choose the chip's
   phase from the isolated experimental kernel.
2. Reproduce missed sub-host-sample pulses through the current
   `runtime.rs::sample_audio_after_tick`, across OCS/ECS/AGA and PAL/NTSC.
   Compute expected time-weighted output independently of the implementation,
   including a pulse crossing a fractional host boundary. Reproduce the
   separate discontinuity from `snapshot.rs` dropping live filter history.
3. Compare the bounded correction with pinned WinUAE `anti_prehandler` and
   `samplexx_anti_handler`: account for the entire held waveform, not just its
   endpoint. Extend the existing runtime accumulator with left/right f64
   weighted areas; split the one completed tick at the host boundary using
   integer phase. No extra emulated ticks, new dependency or chip phase guess.
   Interval averaging is a box filter, not complete band-limited PWM recovery.
4. Preserve those partial areas and existing filter history in snapshot v61,
   rejecting v60. Reconstruct coefficients from the model and validate finite
   histories/areas before mutating the live runtime. Prepare concrete failing
   evidence and obtain schema/design agreement before production changes.
5. Verify full/partial-window replay, restore into a warmed runtime, malformed
   audio-state rejection, instruction-step/run equivalence, pulse conservation
   and constant-level controls. Run runtime tests, strict affected Clippy,
   release build and the ROM-backed audio gate. Record primary evidence before
   the codebase decision; commit the verified correction as one bounded unit.
6. Continue physical PWM phase/reload and pre-decimation bandwidth work from
   the corrected sampling path. Do not describe interval averaging as closure
   of the still-unresolved physical volume counter.

## Reproduced baseline

`audio_sampling_preserves_pulses_between_and_across_host_boundaries` fails
all 36 cases: one-tick pulses at six host phases across PAL/NTSC OCS/ECS/AGA.
The independent expected values are the pulse's overlap with each host
interval, passed through a fresh copy of the existing filter. The current
point-sampler either misses the pulse or assigns a whole host interval to it.

`restore_retains_live_audio_filter_response` fails with restored output
`(0.01076639, -0.005383195)` versus uninterrupted
`(0.6979412, -0.46349975)`. Both failing logs are retained in
`test-data/commodore/amiga/paula-audio/sampling-probe/`.

The proposed schema stores only filter history, not editable coefficients:
rebuild the same coefficients from the model, validate the saved histories
and partial sums, and apply all restored state only after validation. Keep
the host drain buffer transient. The user has been asked for the specific
v61 schema agreement before production implementation and approved it.

## Implemented correction

The existing integer host phase now weights a left/right f64 signal area.
One completed tick is split exactly across a crossed host boundary. The
clock and source-observation phase stay unchanged. Snapshot v61 preserves
those partial areas and the existing filter histories; coefficients are
reconstructed from the model. Area bounds, finite/bounded filter state and
model topology are validated before committing a restore. Reset clears both.

The original 36 pulse cases now pass. All 48 restore checkpoints replay
audible output and final snapshot bytes exactly across A500/A1000/ECS/AGA
and both regions. Eight malformed-state cases fail atomically; precise AGA
instruction stepping agrees with ordinary system ticks. Strict release
Clippy and all 61 runtime unit tests pass. The full runtime gate passes 303
tests with 30 existing ignored diagnostics, including all 65 snapshot tests.
The Amiga release build and all three explicit ROM-backed waveform cases
pass. The first full run caught two stale assertions expecting snapshot v60;
both now expect the approved v61, and the full rerun passes. Logs and artifact
hashes are retained in the sampling corpus's `validation.json`.

The filter's unchanged R/C calculation also exposed an incorrect comment:
the LED stage is about 3091 Hz, Q=0.66. Only its prose was corrected. This
change does not enable the experimental PWM path, choose a physical volume
counter phase, or claim full rejection of above-Nyquist frequencies.
