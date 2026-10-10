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

Status: reproducing and auditing; no production changes approved or made.

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
This schema change is awaiting user approval.

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
