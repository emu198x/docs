# Sord M5 PAL boot and clock verification

Engineering-frontier work on source issue #252. The installed 8 KB Monitor ROM
matches MAME's European BIOS SHA-1 `ac042c4ae8272ad6abe09ae83492ef9a0026d0b2`.
The issue's missing-fixture assumption can now be tested. Pending schema designs
remain separate and are not authorized by this investigation.

1. Pin MAME's PAL/Japan machine clocks and ROM definitions. Inspect its European
   ROM patches; do not silently compare patched reference firmware with an
   unpatched Emu198x run. Consult the shared Sord/TMS primary/reference material.
2. Run the unmodified European BIOS with BASIC-I and Dig Dug in PAL mode. Check
   real prompt/tile output, CTC channel-3 interrupt delivery, frame duration and
   progression after keyboard input; retain hashes and finite runtime traces.
3. Measure PSG host-sample production over runtime-declared one-second intervals.
   The current PAL PSG constructor uses 3,546,893 Hz while the runtime advertises
   3,579,545 Hz for both models; prove any mismatch at the output before fixing.
4. Reproduce root causes and propose bounded changes. Retain save-state compatibility
   requirements explicitly: the PSG currently serializes its internal clock rate.
   Do not claim old PAL save states are corrected merely because a constructor is.
5. Add finite regression assertions after validation, run machine/runtime checks,
   and update/close #252 only when its full boot/timing requirement is met. Keep
   limitations visible if an external oracle or compatibility change is needed.

## Results and bounded correction

The unmodified installed European BIOS boots BASIC-I to `Ready` and Dig Dug to
its player-selection screen in PAL mode. The name tables and captured frames
were inspected. Both deliver exactly 100 channel-3 acknowledgements over the
measured 100 PAL frames; each frame advances 71,364 CPU T-states and ends at
VDP scanline 0.

The runtime-clock probe fails: 3,579,545 CPU T-states produce 48,000 audio samples
on NTSC and 48,441 on PAL. MAME's source uses 10.738635 MHz / 3 for the PSG in
both regions; the installed MAME 0.289 `-listxml m5p` independently reports CPU
and PSG clocks of 3,579,545 Hz and 313 video lines. This is reference configuration
inspection, not a complete MAME boot comparison (the required FD5 ROM is absent).

Correct the PAL PSG constructor constant to 3,579,545 Hz, matching the machine's
existing runtime clock and the reference. This is a bounded configuration fix;
no new fields, API or serialized layout. Add normal-cadence and PAL boot regression
coverage and test newly created PAL save-state continuation.

**Legacy-state limit:** old PAL snapshots serialize the erroneous internal PSG
clock. A constructor change cannot repair those saved values. The pending shared
PSG phase/stereo designs already propose Sord M5 snapshot v5→v6. Do not advance
that version without approval and do not silently synthesize missing old audio
history. Keep #252 open with the legacy-state limitation and remaining oracle
qualification until the correction's continuation requirements are satisfied.


## Regression results

- European BASIC-I and Dig Dug boots: both verify their name-table prompt,
  framebuffer output, 71,364 T-states/frame and 100 frame interrupts across
  100 measured frames. BIOS fingerprint guards against accidentally using the
  Japanese monitor or MAME's patched bytes.
- Dig Dug starts with keyboard row 1 bit 0. A 2,500-frame diagnostic places
  the transition to moving sprites between the sampled frames 300 and 400.
  The initial 200-frame wait plus 100-frame measurement was too short. The
  final gate spans 1,000 frames after the wait and observes 310 distinct
  sprite tables and exactly 1,000 channel-3 acknowledgements. This checks
  progression, not hardware-verified introduction duration.
- Both regions produce 48,000 samples for 3,579,545 CPU T-states. Restoring
  the old PAL constant makes the final regression fail with
  `left: 48441`, `right: 48000` (exit 101).
- An audible guest-programmed PAL tone produces identical samples after
  a save/restore at T-state 12,347. Both continuations produce 48,000 samples
  over the following runtime second.
- An old-clock synthetic PAL machine was serialized by an old-constant
  build and restored by the corrected build. It still produces 48,441 samples.
  The legacy limitation is reproduced, not merely inferred from serde fields.

Primary observation record:
`198x/reference/by-system/sord-m5/2026-pal-clock-observations.md`.
Reference revision: MAME `9391e1eff80eb04abd58d48218a1d3b9643c1ea8`.
The test BIOS SHA-1 is `ac042c4ae8272ad6abe09ae83492ef9a0026d0b2`;
BASIC-I is `d11f7623919ee593e275e9f00f8a4acf7aed3cf5`, Dig Dug
`971f7bc1b6247d17a488f6e07eabc07580219ed9`.

## Reproduction

In the source checkout, with European firmware at
`~/.emu198x/roms/sord-m5/sord-m5.rom` (or `EMU198X_SORD_M5_PAL_BIOS`)
and the named cartridges in `~/.emu198x/media/sord-m5/`:

```sh
cargo test -p machine-sord-m5 --test pal_validation -- --include-ignored --nocapture
cargo test -p machine-sord-m5 -p runtime-sord-m5 -p ti-sn76489 -p ti-tms9918 -p zilog-z80-ctc
cargo clippy -p machine-sord-m5 -p runtime-sord-m5 --all-targets -- -D warnings
cargo fmt --package machine-sord-m5 --check
```

The two ROM tests are explicitly ignored in routine CI; their executed local
results are retained separately. The host-sample and real-tone continuation
checks use synthetic guests and run without fixtures.

Evidence is in [the adjacent folder](2026-10-11-sord-m5-pal-validation/).
`SHA256SUMS` covers every retained file. `gameplay-trace.rs` is the diagnostic
source used to obtain the longer trace; select `trace_pal_gameplay_start` when
running it. Its earlier short gameplay assertion is deliberately retained as
historical evidence, not proposed as a passing regression.

For the legacy experiment, temporarily install `legacy_clock_probe.rs` in
`crates/machine-sord-m5/tests/`. Build with the old PAL constant and
`GENERATE_LEGACY_CLOCK=1 LEGACY_CLOCK_SNAPSHOT=/tmp/legacy-pal.postcard` to
serialize the synthetic machine. Restore the corrected constant and rerun
without `GENERATE_LEGACY_CLOCK`, keeping the same snapshot path. The probe
asserts the known **incorrect** legacy rate; it is a limitation reproduction,
not an accuracy gate. Remove the temporary probe afterwards. No snapshot bytes
or ROMs are included in the evidence.

Routine validation: 116 passed, 0 failed, 6 fixture tests ignored.
The four-test PAL fixture run passed separately. Clippy and formatting passed.

Source correction: [PR #1725](https://github.com/emu198x/emu198x/pull/1725),
head `d1dc71475fe8f5d45b0b628522445ea04bb48389`. Primary observation record
committed locally in umbrella `36d090b0`; the umbrella was not pushed.
