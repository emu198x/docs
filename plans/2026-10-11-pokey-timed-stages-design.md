# Proposed timed POKEY counter and output stages

**Status: proposed; additional architecture and snapshot approval required.**

Repair the confirmed linked-timer ordering and silent-filter faults by extending
the existing POKEY core with retained clocked stages. Preserve pulse duration
through the host sampler and save/restore. This proposal also includes the
partial audio/filter persistence correction awaiting approval in docs PR 55.

## Existing failure modes and evidence

- All 32 synchronized active-filter cases in the public audio probe become
  identically zero; 64 unfiltered/volume-only controls pass. The unchanged
  reference renderer preserves half-cycle pulses across 648 cases.
- All 16 focused linked-timer cases emit the last low and high event together.
  The connected reference counter/borrow/output trace separates them by three
  clocks. Correct total period alone does not establish either event's phase.
- The public AUDF-write probe fails 24 of 96 cases: a changed divider written
  one clock before a pending IRQ affects the next reload too early. All 480
  reference write/counter/borrow/output cases pass, including earlier writes
  and unchanged-value controls.
- The public STIMER probe fails all 72 reset cases; all 24 no-reset controls
  pass. Immediate counter reset drops an IRQ that should survive and restarts
  four clocks early. All 1,440 reference cases pass, including one-clock-away
  borrow cancellation and repeated STIMER writes that postpone both stages.
  The linked extension passes 6,912 reference cases through digital output;
  all 288 public linked-reset cases fail while 96 no-reset controls pass.
- STIMER also omits the waveform preset entirely: 16 of 64 public channel-output
  cases fail, including hidden state under volume-only mode. The original reset
  queue passes 960 supplied-event cases; the connected 1,440-case STIMER path
  now reaches 7,808 verified output transitions with unchanged timer/IRQ traces.
- The current whole-cycle output observation cannot preserve a half-cycle
  pulse. A rounded-clock mutation of the reference loses the same pulse area.
- The existing save path omits partial audio sums and filter history. The
  earlier 80-case continuation probe fails; pending timing stages would create
  further restore differences unless saved as well.
- The 7800's chip-clock/host-sample separation remains local work on the MARIA
  branch. Both functions currently advance through one whole chip period;
  they cannot supply the newly observed half-clock output boundaries.

Reproductions: `2026-10-11-pokey-filter-timing.md`,
`2026-10-11-pokey-borrow-output.md`, and the clock/sampling proposal in docs
PR 55. The unlinked fast-period correction is merged independently in source
PR 1709; preserve its complete divider inventory.

Further input evidence:
[AUDF delivery](https://github.com/emu198x/docs/blob/main/plans/2026-10-11-pokey-audf-delivery.md)
and [STIMER delivery](https://github.com/emu198x/docs/blob/main/plans/2026-10-11-pokey-stimer-delivery.md),
followed by [connected reset output](https://github.com/emu198x/docs/blob/main/plans/2026-10-11-pokey-reset-output.md)
and [linked resets](https://github.com/emu198x/docs/blob/main/plans/2026-10-11-pokey-linked-reset.md).
These qualify the stated unlinked and linked paths. Linked AUDF changes,
combined STIMER/AUDF writes, other control writes and physical CPU-write
phase still require validation. The reference's counter-assignment timestamp
is not itself a physical reload phase; preserve the distinction recorded in
the STIMER evidence when designing native stages.

## Recommended representation

1. Extend `Channel` and the existing POKEY clock path with separate retained
   countdown, borrow/reload and waveform-output state. Linked channels retain
   their individual counter/borrow phases. Their last low event and high event
   must occur at the separately observed boundaries; the combined interval
   remains a validation result rather than the sole state representation.
2. Give waveform delivery and paired-filter capture finite pending stages at
   half-clock resolution. Sample noise when the qualified clock reaches its
   output latch, retaining the existing sampled-noise and disabled-filter
   corrections. Preserve volume-only's visible override and hidden state.
3. Retain timed register copies where writes can affect an in-flight reload or
   output event. Qualify AUDF, AUDC, AUDCTL, STIMER and SKCTL delivery through
   the original reference paths before fixing their stage delays. The current
   captures begin from loaded counters; they are not CPU-write timing evidence.
   Trace reset/borrow collisions and linked reloads before coding those rules.
4. Keep these stages in the existing POKEY core, driven by its supplied clock
   edges. The reference scheduler stays in the validation harness. No runtime
   event scheduler, CPU bus callback, new dependency or parallel audio engine.

The public direct-chip state codec will receive a `POKEY` version-1 tag and
complete retained-state encoding. Reject the previous unversioned bytes before
mutating the chip. Keep deterministic tables and already-emitted host buffers
out of the saved payload; preserve every partial timer/output/sample/filter
state needed for identical continuation. Use the existing manual codec style
and serde support, with no new serialization dependency.

## Clock and sampling contract

- Preserve `Pokey::tick()` as one whole chip clock for existing fixed-rate
  library callers. Internally it visits both native half-clock boundaries and
  integrates both intervals, so it cannot erase an intervening pulse.
- Add an explicit phase/clock-edge entry point and keep host sampling separate.
  Repeated levels hold state; only real supplied edges advance clocked stages.
  The machine's master oscillator remains authoritative.
- The 5200 and 800XL already tick at one colour clock per CPU half-clock. Route
  the two POKEY edges through those existing master slots. Their public machine
  time units and runtime clock metadata stay unchanged.
- The current mainline 7800 routes its fixed-rate POKEY phases through existing
  colour-clock slots. On the MARIA branch, route actual phase-1/phase-2 edges
  from the native variable CPU clock and accumulate audio on every oscillator
  tick, including DMA ownership and stretched peripheral clocks.
- Extend the current accumulator to weight held levels by elapsed master time.
  A fixed whole-clock convenience call contributes two half-duration intervals;
  a machine sample tick contributes its actual native duration. Keep the
  48-kHz output deadline tied to elapsed master time, not CPU execution count.
  Save partial sums, phase, duration count and DC-filter history.

The concrete phase API and constructor naming must make the supplied sample
clock unambiguous. Existing `new(cpu_frequency)` plus `tick()` callers retain
their rate. Native callers explicitly select their master sampling rate.
No catch-up ticks or time advancement in register accessors.

## Snapshot versions and branch coordination

Develop the shared correction independently of MARIA's unresolved physical NMI
gate, so the 5200/800XL correction can merge once verified.

| Runtime | Current main | Timed POKEY correction |
| --- | ---: | ---: |
| Atari 5200 | 18 | 19 |
| Atari 800XL | 18 | 19 |
| Atari 7800 | 5 | 6 |

Reject the preceding runtime version before machine decoding. The separate
unreleased MARIA branch currently also uses version 6 for a different payload;
move that pending native-MARIA envelope to **version 7** when integrating the
shared correction. This prevents two different layouts from claiming the same
published version. Its former version-6 development saves will be rejected.
No version-6 MARIA payload has been merged into main.

Approval covers this explicit renumbering as well as the new POKEY fields and
direct-chip format. The earlier v18-to-v19 audio persistence proposal is
included here, not a second independent format change to ship afterward.

## Implementation and validation gates

1. Qualify reference register-delivery/reset collisions and record their
   counter/borrow/output consequences. Add failing regressions for the new
   state boundaries before replacing the corresponding production behaviour.
2. Extend `crates/atari-pokey/src/lib.rs` with focused stage/state modules as
   needed. Keep the existing register API, serial/pot/IRQ responsibilities and
   polynomial generators. Run the full period, sampled-noise, polarity and
   latch inventories alongside timed pure/noise/filter/control-transition
   traces. Both supported filter pairs and linked channel pairs are required.
3. Update `crates/machine-atari-{5200,800xl,7800}/src/lib.rs` at their existing
   oscillator edges. Validate actual CPU register writes, DMA holds, WSYNC and
   fast/slow accesses, including public audio and IRQ outcomes. Integrate the
   preserved MARIA/POKEY work without discarding its local edits.
4. Update the three runtime `snapshot.rs` envelopes. Save at every distinct
   countdown/borrow/reload/output/filter phase and at partial host samples;
   compare resumed bus/IRQ/audio traces against uninterrupted execution with
   intervening register writes. Test old-version rejection before mutation.
5. Run chip, machine/runtime, affected frontend, boot/synthetic-cartridge,
   Clippy, formatting and hygiene checks. Require complete nonempty inventories
   and fault-injection controls. Commit bounded passing slices. Merge the
   shared correction after CI; keep the separate MARIA PR draft until its own
   interrupt/raster gates pass.

## Alternatives

- **Recommended:** the retained stages above. They cover both confirmed faults
  and preserve their partial execution through saves without changing machine
  oscillator units.
- **Continue evidence first:** keep production unchanged while extending the
  register/reset trace. This postpones architecture and schema approval; the
  current faults remain open.

This is not a claim that the manual and Altirra provide independent hardware
measurements. The source and observation limits remain explicit. Further
disagreements must be investigated before choosing production expectations.
