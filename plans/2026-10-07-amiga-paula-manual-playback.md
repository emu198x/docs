# Paula CPU-fed playback investigation

Lane: best-in-class Amiga accuracy campaign. Start at the merged version-58
DMA interrupt correction. Production changes await a resolved timing design.

1. Trace the manual start, data holding and stop paths in the original HRM,
   vAmiga and WinUAE. Inspect the origin of WinUAE's early IRQ sample and the
   existing vAmigaTS timing guests. Record what each can actually establish.
2. Execute the reference transition methods under identical explicit register
   and acknowledgement schedules. Sweep periods including 1, 2, 8 and zero,
   acknowledgement before/after the word edge, and writes while playing.
   Keep producer source, exact revisions, hashes and CSV in
   `test-data/commodore/amiga/paula-audio/manual-probe/`.
3. Compare the current native manual probe. Separate agreed failures from
   reference disagreements. Define the smallest existing-stage correction;
   request approval only if the evidence requires a new saved latch/schema or
   a change to the previously approved pipeline design.
4. Once the design is settled, promote the agreed probe to regressions and
   verify component DMA remains unchanged, live-board register delivery,
   OCS/ECS/AGA restore, waveform gate, build and strict Clippy.

Initial constraints: the 20-scenario manual probe has 396 mismatches in 480
observations. vAmiga and WinUAE both gate idle startup on pending INTREQ and
start on the high byte with a delayed IRQ. WinUAE samples the manual stop
condition one CCK before the low-to-high edge; vAmiga consults it at the edge.
A source majority is not physical-hardware proof.

## Executed results and provenance

WinUAE's early sample is a deliberate correction, introduced in commit
`d53bc2521ef155f4b34fae4f7692980cb22b521b` (2021-09-19). Its 4.9.0 beta 34
change log explicitly says the state-3 INTREQ check occurs at counter 1, and
credits ross's test set. Commit `2e5d87a906f79e7d534f44af7203f9290effac75`
then distinguishes a sampled clear bit from an unsampled condition. Commit
`2448841a540d40389ad18146626f64983ea013ad` handles period 1 by sampling on
low-byte entry. This is maintainer-reported test evidence, not a newly acquired
physical capture. The underlying ross test package has not been recovered.

The new producer executes unmodified WinUAE register-event and transition
methods at `c32694e338fa5f34977f522eb4898adb069d2e73` and unmodified vAmiga
methods at `60fd1e6b69dcd77c9f44d1291bd37ec715362ab0`. It runs 440 scenarios:
four channels, periods 1/2/8/124/65,536, eleven input schedules and input applied
before/after the period event. Each producer emits 4,312 observations. State
and IRQ differ in 420 rows across 108 scenarios. vAmiga's sampler suppression
prevents treating its repeated DAC samples as a reliable comparator; the
cross-reference count deliberately excludes those samples.

Example: period 8, clear INTREQ immediately before clock-16 output. WinUAE
stops, retaining the low byte, because its decision was sampled at clock 15;
vAmiga continues. Conversely, a bit set at clock 16 cannot overturn WinUAE's
sampled continue decision. WinUAE requests the normal word IRQ at that boundary
even if the channel stops, making a late clear distinguishable one CCK later.

The native research probe fails with functional mismatch counts
`[216, 312, 304, 284, 304, 216, 308, 260, 304, 376, 296]`: 3,180 of 4,312
output/IRQ observations. Its 3,072 state-name differences are recorded separately;
our current public diagnostic deliberately labels CPU-fed playback Idle, so
that count is not independent proof of an output fault. Existing component
regressions remain intact. Production code is unchanged.

Minimig's source uses a boundary-time check and supplies no early decision
latch; it does not resolve the conflict. The inspected vAmigaTS audtim1/audtim7
sources trigger CPU interrupt handlers and vary periods/lengths, but do not
control acknowledgements immediately around the disputed edge. Their hardware
photos have not been used as proof of this particular timing.

## Recommended design — requires snapshot approval

Follow the documented WinUAE correction at the disputed edge. Extend the
existing AudioChannel with `manual_stop_pending: Option<bool>`: None means
unsampled, Some(false) means continue, Some(true) means stop. Retaining false
is necessary: sampling clear and then setting INTREQ must still continue.
Expose the same field in channel diagnostics and query leaves. Save it in
Amiga snapshot version 59, rejecting 58.

Reuse Idle/Playing, current_word, dat, next_byte_is_hi, period_counter and the
version-58 delayed IRQ stage. A CPU DAT write always updates dat. While Idle,
start only if the visible INTREQ bit is clear: load the output buffer, present
the high byte, reload period, enter Playing and request delayed startup IRQ.
While Playing, DAT changes only the holding latch. Manual playback does not
request DMA and must not drain its output buffer after the first low byte.

At low-byte entry clear the previous decision; for period 1 sample immediately.
For longer low-byte periods capture visible INTREQ when one CCK remains. At
expiry consume that decision, request the normal delayed word IRQ, and either
hold the low sample in Idle or load dat and present the next high byte. Period
attachment retains its existing edge selection; add directed manual-attachment
probes before claiming that combination is closed.

Alternative: consult live INTREQ at expiry, like vAmiga/Minimig. This avoids
saved state but contradicts WinUAE's explicitly documented test correction and
loses the demonstrated early sample. Alternative: fix startup/active writes
alone and defer stop behaviour. That leaves the reproduced playback loop wrong.
The saved decision is the bounded recommendation.

Implementation files: Paula `src/lib.rs`, manual component regressions,
shared-board manual register tests, runtime query leaf catalogue,
`snapshot.rs` and `snapshot_roundtrip.rs`. Verify both sampled values across
OCS/ECS/AGA restore, period-1 and zero periods, late clear/set, active DAT
writes, and existing DMA reference closure. Retain the three-case waveform
gate and run release build, formatting and strict Clippy.

The root AGENTS.md requires agreement for “Breaking changes to APIs or data
schemas”. The previous approval covers version 58's DMA stages, not this
additional manual decision. No production or snapshot change is made here.

Exact implementation targets in `Emu198x/emu198x/`:

- `crates/emu198x-commodore-paula-8364/src/lib.rs`
- `crates/emu198x-commodore-paula-8364/tests/manual_playback.rs` (new regression)
- `crates/emu198x-commodore-paula-8364/examples/manual_boundary_probe.rs`
- `crates/machine-commodore-amiga-ocs/tests/paula_phase2_machine.rs`
- `crates/runtime-commodore-amiga/src/variants.rs`
- `crates/runtime-commodore-amiga/src/snapshot.rs`
- `crates/runtime-commodore-amiga/tests/snapshot_roundtrip.rs`

No new clock, dependency or broader DMA-to-manual transition rewrite is proposed.
The new research example builds under strict Clippy; all 109 existing Paula
component tests still pass. Ruff and formatting pass. The reference generator
checks both row counts and the full 440-scenario inventory, then checks that
producer input/clock keys agree before counting disagreements.
