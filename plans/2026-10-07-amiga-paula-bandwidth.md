# Reject aliases before producing Paula host samples

Continue the best-in-class Amiga accuracy campaign. Keep pushing deferred.
The completed v61 interval accumulator preserves signal area but has only a
box-filter frequency response. Investigate this separately from physical
Paula PWM phase, which remains unresolved.

1. Inspect the pinned WinUAE `sinc_prehandler_paula` and
   `samplexx_sinc_handler` in `audio.cpp`, including their table/time units.
   Search shared audio code and frozen archives for reusable DSP. The three
   archive paths named in RULES.md are absent; the frozen donor crates have
   no band-limited resampler. The shared shell converts host packets but does
   not provide a chip-signal antialiasing stage.
2. Add an explicit diagnostic in
   `crates/runtime-commodore-amiga/src/runtime.rs` that drives held output
   through the real sampler. Measure audible aliases from above-Nyquist
   tones, with in-band controls, PAL/NTSC and several phases. Preserve the
   failing inventory in `test-data/commodore/amiga/paula-audio/bandwidth-probe/`.
   This diagnoses resampling, not a new hardware waveform or PWM schedule.
3. Execute the unchanged WinUAE vanilla BLEP kernel and compare its rejection
   with the native inventory. Keep its board-filter tables distinct from
   generic resampling. Record source pins/hashes, elapsed time, nonempty
   inventories and negative controls. Do not import reference GPL code or
   coefficients into production.
4. Prototype an independently generated finite windowed-sinc step response.
   Measure passband error, alias rejection, delay, memory and dense-edge cost.
   Compare bounded edge accumulation with direct convolution before choosing
   the production design. No production stage or snapshot schema changes
   until evidence and concrete design are agreed.
5. Record observations in the primary reference library, then the codebase
   decision. Propose the narrow production extension and its snapshot state,
   including shared-layer placement under RULES.md rule 30. Obtain approval
   for the additional architecture/schema change before implementing it.
6. After approval, test signal conservation, silence/DC, bandwidth, stereo
   routing, arbitrary tick phases, dense edges, exact save/restore and reset,
   malformed state, and normal/instruction stepping agreement. Benchmark the
   hot path, run affected strict Clippy/build/tests and the ROM audio gate.
   Commit the verified correction as its own bounded change.

## Evidence and proposed design

The real sampler fails all 54 stopband rows in a 108-case inventory. On
A1200 PAL, 55 kHz folds to 7 kHz at 12.28% amplitude; the valid 20 kHz tone
loses 26.24%. OCS/ECS/AGA, both regions and three phases reproduce the gap.
The explicit diagnostic is ignored in ordinary suites because it records
an unresolved accuracy requirement; running it directly fails with all
108 rows printed. No existing test is disabled.

The independent 96-sample, 256-phase Blackman-windowed sinc step prototype
passes 66 tone cases from 1 kHz through 3 MHz and four pulse-area cases.
Bypassing it fails 48 tone cases. It preserves the tested passband within
0.015%, rejects the tested stopband below -60 dB, and delays output by 1 ms.
The shared table is 197,376 bytes; stereo history is roughly 1.5 KiB.
The final local C++ benchmark costs about 7 ms per emulated second at
period 124, 160 ms at period 1, and 313 ms with mixed changes every system
tick. These figures exclude the machine and must be remeasured in Rust.

The WinUAE extraction exposes an unresolved queue-time unit discrepancy;
normalised and pinned-caller units produce very different rejection. Its
algorithm is precedent, but neither extracted output is a hardware oracle.
The primary observation note records the pins, adaptation and limitation.

Recommend extending host resampling with this bounded step-response ring.
Alternatives are direct high-rate convolution (much larger per-host-sample
work), or a multistage decimator (more state and intermediate filters to
design and validate). Both remain possible if actual Rust performance
invalidates the candidate; do not quietly substitute either architecture.

Production files, pending agreement:

1. Add a generic helper under
   `crates/emu198x-shell/src/audio/band_limited.rs`, exposed by `audio.rs`.
   Keep clock ownership in the caller: consume fractional position from
   the runtime's existing integer phase. No new dependencies, chip ticks,
   hidden event queues or machine-specific logic in the shared helper.
   Generate immutable coefficients once; retain fixed-capacity stereo
   corrections, previous level and cursor. Test pulse area, constant/DC,
   stereo separation, fractional phases, dense edges and spectral limits.
2. Replace the box output in `runtime-commodore-amiga/src/runtime.rs` with
   this helper. Preserve the existing source observation and host cadence.
   Apply existing board filters to the resulting stream. Delay sampled LED
   control by the kernel's 48 host frames in a bounded 48-bit history so
   the extra signal delay does not misalign it. Keep the existing analogue
   response approximation explicit; rapid switching remains separate work.
3. Extend `snapshot.rs` to version 62, rejecting v61. Save ring, cursor,
   previous level, existing integer phase, delayed LED bits and existing
   filter histories. Retire the superseded box-area field. Rebuild shared
   coefficients; validate finite/bounded values, lengths, cursor and LED
   bit range atomically. Reset clears all signal history.
4. Promote `bandwidth_probe.rs` into a normal passing regression after the
   correction. Replace box-shape expectations in the earlier pulse test
   with area/independent convolution checks; do not pin the new code's own
   coefficients as its sole oracle. Extend snapshot and stepping replay to
   pending filter tails and delayed LED changes on all boards/regions.
5. Benchmark the real Rust path under ordinary, period-1 and denser mixed
   edges; run full runtime/snapshot tests, strict shared/runtime Clippy,
   release build, web compile where supported and the ROM waveform gate.
   The amplitude/cadence gate should tolerate the 1 ms startup delay by
   measuring settled samples, without weakening its amplitude assertions.

The prototype and diagnostic do not amend the production architecture.
Approval for this additional shared helper and v62 state is required by
AGENTS.md's rules on architectural patterns and breaking data schemas.

## Research verification

All 61 existing runtime library tests pass; the one new known-gap diagnostic
is excluded from that count and explicitly fails with 54 stopband failures
when invoked. Strict all-target runtime Clippy and workspace formatting pass.
The first Clippy run required `as_chunks` instead of `chunks_exact`; its
failure and the corrected run are retained. The final diagnostic source was
rerun after that correction. Ruff passes for the extraction runner, and its
three generated reference artifacts reproduce byte-for-byte. Normal and
bypassed candidate runs produce the required 66-case inventories, respectively
zero and 48 failures. Source hashes and compressed logs are in the corpus's
`validation.json`. Production and snapshot v61 remain unchanged.
