# VIA timer 2 start timing — issue 1677

Lane: engineering-frontier accuracy; shared VIA correction.

Issue 1677 reports the counter and flag starting one cycle early after a
T2C-H write. The current `mos-via-6522` loads immediately and decrements on
the tick closing the write cycle. VICE 3.10 `src/core/viacore.c`, `VIA_T2CH`,
delays interval counting by one cycle so the next cycle observes the written
value. Pulse counting has a distinct path. Verify the flag boundary separately
from the counter: do not assume timer 1's schedule establishes timer 2's.

1. Generate a synthetic VIC-20 KERNAL probe covering T1/T2 counter reads and
   interrupt flags around short timer expiries. Run identical bytes through
   native VICE xvic on PAL/NTSC and the existing VIC-20 machine test path.
   Record binary identities, bytes and disagreements before changing the VIA.
2. Determine the smallest existing-stage correction from those results.
   If a pending T2 load phase is needed, preserve it via serde. Audit every
   VIA consumer's snapshot envelope and obtain approval for that schema change
   before production edits. No new dependencies or CPU/bus abstraction.
3. Add failing chip and machine regressions, including restart, low-latch
   writes, pulse-counting controls and restore during the pending phase. Keep
   separate evidence for any discovered post-underflow or serial-shift fault;
   do not silently absorb those into a start-delay claim.
4. Validate every VIA user's suites with strict fixtures, the VIC-20 survey,
   full C64 runtime and catalogue including snapshot replay, then formatting,
   Clippy and CI. Classify any changed output before re-capture. Commit a
   self-contained correction and close 1677 only after its scope is proved.

Consumers: VIC-20, PET, Oric Atmos, BBC Micro, Atom, 1541/1571 and the shared
IEC-drive board. Runtime versions currently are VIC-20 7, PET 3, Atom 2,
and C64 18; confirm BBC/Oric and all snapshot paths before proposing changes.
The frozen Oldest VIA has an earlier direct timer implementation and is
reference-only. Primary sources are the MOS preliminary 6522 datasheet
(November 1977) and the family `reference/by-topic/via-6522/` reference.

Local disk space is about 5 GB free. Reuse existing build artifacts and inspect
actual build failures; do not disable tests or remove unrelated artifacts.

Status: approved fix committed and pushed; full C64 catalogue verification awaits the unavailable external media library.

## Confirmed baseline and concrete design

Native VICE xvic gives identical results on PAL/NTSC for all 68 reads.
Running the identical synthetic KERNAL in Emu198x finds four differences per
model: T2 at W+105 reads $FE95 instead of $FE96; N=3 at W+4, N=5 at W+6,
and N=7 at W+8 have IFR bit 5 set where VICE has it clear. All T1 controls
agree. The failing regression reports observations 2, 48, 57 and 66 on each
model. Source baseline: `ae399c87ecf649cf19d4753c9fd024945f22251c`.

Add `t2_load_pending: bool` to `crates/mos-via-6522/src/lib.rs`. A T2C-H
write in interval mode loads the counter and sets this phase; the tick closing
the write consumes it without decrementing. A pulse-mode load does not set
it, preserving the existing PB6 edge path as VICE's separate load handling
requires. The flag must be saved: dropping it during restore advances the
counter and interrupt one cycle early. Do not reload from T2L-L while
consuming it; a later low-latch write must not replace the loaded counter.

Version the existing envelopes and reject old versions before deserialising
the changed payload, following the already established C64 decoder pattern:

| Runtime | Old | New |
|---|---:|---:|
| C64 (including 1541/1571 drive state) | 18 | 19 |
| VIC-20 | 7 | 8 |
| PET | 3 | 4 |
| BBC Micro | 7 | 8 |
| Atom | 2 | 3 |
| Oric Atmos | 6 | 7 |

Files: the VIA chip, `crates/machine-commodore-vic-20/tests/via_timer_probe.rs`
and its two synthetic fixtures; the six runtime `src/snapshot.rs` files and
applicable snapshot/version tests. Preserve a mid-load snapshot in chip and
runtime regressions. No new clock, timing counter, dependency or architecture.
The user approved this schema change on 2026-10-10.

The reference and datasheet also say T2 continues counting after its one
interrupt; the current implementation stops it. That is a separate observed
code discrepancy, not claimed fixed by the start-delay correction, and needs
its own probe before implementation. Serial-shift coupling is also outside
this correction.

Three additional chip regressions fail on the same baseline: T2's first read
is $FEFD where T1 reads $FEFE, N=0 flags in cycle 1 instead of after the load,
and a restart reads 4 where 5 was loaded. The existing PB6 pulse-count test
passes. `chip-red.log.gz` and `failing-regressions.patch.gz` preserve this
reproduction while schema approval is pending. The archived patch changes
tests only; the synthetic machine fixtures regenerate from `probe.py`.


## Implemented correction and verification

Source commit `0a3c6c5dc5433f303fc967f15d8347427b1ed949` retains the
interval-mode load phase and leaves PB6 pulse-mode loads immediate. All six
snapshot envelopes have the approved versions. The five decoders that used
to parse the entire payload first now reject a leading incompatible version
before reading chip data. Tests cover the version-only old envelope and
unchanged runtime state after rejection.

The synthetic guest now agrees with all 136 native VICE observations (eight
mismatches before). Chip checks cover zero through 65535, restarts, low-latch
writes before and after consuming the phase, and immediate PB6 edges. The
runtime test saves both VIC-20 VIAs before the load tick and during counting
on PAL/NTSC, then checks the counter against elapsed machine cycles and the
entire state against uninterrupted execution. A deliberate `serde(skip)` on
the new field makes it fail: `left: 65277`, `right: 65278`. The field was
restored before the passing checks and commit.

Validation records alongside this plan:

- `suites.log.gz`: 542 ordinary tests pass across the shared VIA, IEC drive
  board, seven machine consumers and six runtimes; 110 fixture/diagnostic
  tests ignored by default. The subsequent doctest invocation encountered
  `error[E0463]: can't find crate for machine_commodore_1541` while other
  invocations rebuilt the shared artifacts. The separate all-consumer
  doctest rerun in `doctests.log.gz` completes successfully (no runnable
  doctest examples).
- `focused-green.log.gz`: 35 chip/runtime tests pass after adding the
  first-PB6-edge control and strengthening the low-latch regression.
- `fixtures.log.gz`: 32 explicitly enabled fixture tests pass under strict
  fixture mode across the six machines with fixture suites. This includes
  BBC MOS timing, keyboard, display and tape checks, Atom tape round trips,
  PET/VIC-20 boot and keyboard checks, 1571 ROM boot and Oric boot/display.
- `survey.log.gz`: the VIC-20 reference survey and its wrong-frame negative
  control both pass; the expected pixel counts are unchanged.
- `drive-roundtrip.log.gz`: the real-ROM 1571 SAVE/LOAD/RUN and both 1541
  save/read/load/run checks pass in release mode.
- `clippy.log.gz`: all affected packages and targets pass with warnings
  denied. Workspace formatting and the doc-link/fixture-guard/ignore-reason
  checker self-tests pass.
- `source-identity.json`: the committed files and their SHA-256 identities.
  The committed synthetic ROM matches `reference.json`, and its 68-byte
  golden result matches both native model records exactly.

The complete C64 catalogue is **not validated yet**. `catalogue.log.gz`
records the firmware-only boot and snapshot replay passing, then the run
stopping because `/Volumes/Data/Library/ROMs/TOSEC/commodore/c64/Games/Arcade/[D64]/Bruce Lee (1984)(Datasoft).zip`
is missing. `/Volumes/Data` is not mounted. The user has been asked to reconnect
it or provide the current library path. No reference hashes were changed;
keep the source PR draft and issue 1677 open until this gate passes.

Run the remaining gate from the source repository, overriding
`EMU198X_CATALOGUE_MEDIA_ROOT` if the library has moved:

```sh
EMU198X_CATALOGUE_SYSTEMS=c64 EMU198X_STRICT_FIXTURES=1 cargo test -p emu198x-catalogue --release --test run -- --ignored --nocapture
```
