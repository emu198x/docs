# VIA Timer 2 continues after its one-shot interrupt

Lane: engineering-frontier accuracy. This is separate from issue 1677's
approved load-delay correction and will stack on that branch.

The MOS November 1977 datasheet's Timer 2 interval and pulse-count sections
explicitly say counting continues after timeout; only further interrupt
generation is disabled until T2C-H is rewritten. VICE's `viacore_t2_zero_alarm`
clears `t2_irq_allowed` separately from its counter calculation. Our shared
VIA stops its counter at zero by clearing `t2_running`.

1. Extend the existing synthetic VIC-20 timer probe method with short and
   long post-underflow reads, low-read/IFR acknowledgement, a second full
   wrap and a restart. Compare identical guest bytes with native xvic on
   both regions. Add failing chip tests for interval and PB6 modes.
2. In `crates/mos-via-6522/src/lib.rs`, use the existing `t2_running` latch
   solely to arm the one-shot interrupt; allow the counter to decrement and
   wrap on its selected clock even when unarmed. Preserve the approved load
   delay and keep serial shifting separate. No new field, dependency or
   snapshot layout is proposed. Test IRQ rearming only through a high write.
3. Add uninterrupted-versus-restored continuation across underflow using
   the existing runtime snapshot test machinery. Run all shared VIA consumer
   suites, the native probe, VIC-I survey and available drive regressions,
   formatting and Clippy. The full C64 catalogue remains a merge gate and
   is unavailable until the external media library returns.
4. Commit one bounded fix, retain native/failing/passing evidence and create
   a separate PR stacked on the approved Timer 2 start fix. Do not claim
   serial T2-low coupling or unmeasured reset values have been corrected.

## Evidence and result

The shared reference source is
`reference/by-topic/via-6522/mos-6522-preliminary-nov-1977/mos-6522-preliminary-nov-1977.md`,
sections **Timer 2 Interval Timer Mode** and **Timer 2 Pulse Counting Mode**.
Both describe continued decrementing after the first timeout and require a
T2C-H write to allow another interrupt. The implementation precedent is
VICE 3.10's `src/core/viacore.c`, particularly `viacore_t2_zero_alarm`,
`viacore_t2_underflow_alarm` and the elapsed-time `viacore_t2` calculation.

The synthetic guest uses initial counts 0, 1, 7, 255, 256 and 65535. Each
case reads shortly after loading, after each of two full counter wraps,
and after a high-byte restart. The observations include the interrupt flag,
both counter bytes and the flag after a low-byte read acknowledges it.
Between long waits, low-latch and IFR writes check that neither rearms IRQ.
All 96 bytes agree between native PAL and NTSC xvic.

Before the correction, 84 of the combined 192 observations differed from
VICE. The new interval and PB6 regressions also failed at the first timeout:
`left: 0`, `right: 65535`. After the correction, all 192 observations agree.
The chip regressions exercise another 65,537 clocks or PB6 edges after
acknowledgement, checking continued wrapping and no repeat interrupt. The
PB6 test also checks that held-low and rising input levels do not count.

The existing private `t2_running` field now gates only the one-shot
interrupt. The selected clock continues decrementing the counter with
16-bit wrap. The approved pending-load phase is unchanged. This adds no
field and changes no snapshot layout or public API. The snapshot versions
remain those approved in the parent Timer 2 start correction.

The runtime regression saves at 24 positions across PAL/NTSC, initial counts
0, 1, 3 and $FEFE, and three instruction offsets. It checks both VIAs against
elapsed machine clocks and compares the complete restored state with
uninterrupted execution after each of four further instructions.

The generator, native logs, reference manifest and failing/passing test logs
are retained in [the evidence directory](2026-10-10-via-timer2-underflow/).
Regenerating the guest and native captures produces byte-identical fixtures.

The full C64 catalogue remains a merge gate: the external media volume is
absent. No catalogue hash is changed. Keep this fix stacked on PR 1689 and
draft until the parent and catalogue gate pass. This work does not resolve
the separate serial-shifter/T2-low coupling or establish physical reset
counter values.

## Validation

Source commit: `145dc6cf` (stacked on `0a3c6c5d`).

- 546 ordinary tests pass across the shared VIA, IEC board, machine
  consumers and runtimes. All doctest invocations complete successfully.
- 32 explicitly enabled firmware tests pass with strict fixture handling.
- The VIC-I reference survey and its deliberately wrong-frame control pass;
  the expected pixel counts are unchanged.
- All three real-ROM 1541/1571 SAVE/LOAD/RUN checks pass.
- All affected targets pass Clippy with warnings denied. Workspace
  formatting, diff whitespace, and the doc-link, fixture-guard and
  ignore-reason checker self-tests pass.

`validation.json` records the counts; `source-identity.json` pins the source
commit and modified files. The native manifest pins the guest, generator
and xvic executable. Logs ending in `-red` retain the pre-fix failures;
the other test logs record the corrected source.

The remaining catalogue command, from the source repository, is:

```sh
EMU198X_CATALOGUE_SYSTEMS=c64 EMU198X_STRICT_FIXTURES=1 cargo test -p emu198x-catalogue --release --test run -- --ignored --nocapture
```

Set `EMU198X_CATALOGUE_MEDIA_ROOT` if the library has moved. The parent's
missing-media failure is retained in
`2026-10-10-via-timer2-start/catalogue.log.gz`; it is not a passing result
for either branch.
