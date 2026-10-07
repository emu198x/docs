# Paula period and modulation evidence

Lane: best-in-class Amiga campaign. The user approved investigating Paula
after the merged graphics sweep. Keep unrelated graphics evidence integration
separate; merge those PRs when checks pass.

1. Compare `emu198x-commodore-paula-8364/src/lib.rs` with the registered
   vAmiga and UAE audio state machines and the original hardware manual.
   Reproduce period 0, short periods and mid-period writes using runnable
   reference code and the existing public Paula component interface.
2. Preserve exact source hashes, probe inputs and observed event times under
   `test-data/commodore/amiga/paula-audio/`. Distinguish source inspection,
   component execution, full-machine evidence and analogue measurements.
3. Add a failing regression for each confirmed defect before a bounded
   correction. Reuse existing counter/stage state where it represents the
   hardware; new state, architectural changes or snapshot schema changes
   require a concrete design and approval. Do not change filters to hide
   digital timing differences.
4. Validate normal-period controls, period-zero rollover and writes at several
   counter phases. Run all Paula component tests, the independent full-machine
   audio gate, relevant board and snapshot tests, formatting and strict Clippy.
5. Investigate attach-period/volume transition phases separately after the
   period correction is understood. Retain unresolved differences explicitly,
   record verified observations in the shared primary-reference layer, and
   commit each bounded correction with its evidence.

Initial source finding: `effective_period()` clamps the raw period to 124;
both reference implementations reload shorter values directly and use 65,536
for zero. Existing native tests assert the clamp, so those tests cannot
establish its accuracy. This was established before changing production code.

## Reproduction and proposed bounded correction

The compiled unmodified vAmiga `pokeAUDxPER` and `percntrld` bodies produce
eleven reload observations and twelve mid-period write observations. The
adapter replaces only the scheduler with an elapsed-clock recorder; this is
component-source execution, not a full-machine or hardware trace. UAE's
cycle-exact register handler independently corroborates the reload values.

The new native `tests/audio_period.rs` measures actual DAC sample transitions
through public Paula methods, with an explicitly staged initial DMA buffer.
Seven of eleven period rows fail: 0, 1, 2, 3, 60, 113 and 123 all last 124 CCKs.
Periods 124, 125, 512 and 65,535 agree. At four write phases, writes to 0 and 1
produce the wrong next interval; writes to 512 agree, and every current
interval still ends at the correct time. Both regressions fail before any
production edit (15 differing rows out of 23).

Approved design (2026-10-07):

- Keep the programmed period register at 16 bits; widen the existing remaining
  counter and derived diagnostic period fields to `u32` so 65,536 has an
  explicit representation. Reload 0 as 65,536 and every other value unchanged.
- Remove the artificial 124-CCK playback floor. Retain the public constant as
  the documented recommended DMA period, with accurate documentation.
- Preserve the existing clock, current-interval write behaviour and DMA stages.
  Correct only period reloads in this commit; modulation scheduling remains a
  separately measured follow-up.
- Update Paula diagnostics and their shared runtime serialization consumers;
  advance Amiga snapshots from 56 to 57 and explicitly reject older saves.
  Add restore checks during both long-zero and short periods, plus the existing
  23 reference-backed cases, all Paula tests, board regressions, the independent
  audio gate and the full snapshot suite.

The alternative is retaining a 16-bit counter with zero encoding 65,536. That
avoids wider stored state but makes zero ambiguous in the current counter and
diagnostic contracts. Explicit width is recommended for inspectable state.
The user approved this public diagnostic/schema change before implementation.

## Completed correction and validation

The existing counter and public derived period fields now use `u32`; reloads
use the written value, with zero interpreted as 65,536. Amiga snapshots use
version 57 and reject version 56 before decoding its payload.

All 23 reference-backed timing observations agree after correction. Validation
passed: 104 Paula component tests, 56 runtime library tests, 60 snapshot tests,
45 query tests, 39 board-level Paula tests, and the independent three-case
full-machine audio gate. Its routing, cadence and volume observations are
identical before and after the correction. Live restore covers 27 checkpoints
across OCS, ECS and AGA, including the full zero-period countdown and sample
transitions. Grouped and leaf diagnostics both retain 65,536.

The release Amiga build, strict targeted Clippy with all targets, Rust formatting
and Python probe checks pass. Rebuilding the reference probe reproduces its CSV
byte-for-byte. Evidence, hashes and logs are retained under
`test-data/commodore/amiga/paula-audio/period-probe/` in the emulator repo.
The first broad snapshot run found two stale version-56 assertions; both were
updated to 57 and the complete snapshot suite passed on rerun. The initial
failure log remains available alongside the final results.

The previous graphics evidence and documentation PRs (#1655 and docs #7) are
merged. Modulation transition phases remain the next investigation. Source
inspection suggests a phase difference, but no executable modulation mismatch
has yet been established. DMA starvation, manual startup and interrupt timing
also remain outside this period-reload claim.
