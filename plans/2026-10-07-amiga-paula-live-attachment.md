# Verify live Paula attachment switching

The user approved verification of attachment changes during playback. Continue
the Amiga accuracy campaign using the existing pinned reference extraction and
single board clock. Start with evidence; do not assume that muted raw samples
are harmless when software can subsequently unmute the channel.

1. Add `test-data/commodore/amiga/paula-audio/live-attachment-probe/reference.py`.
   Reuse pinned WinUAE/vAmiga transition methods. Cross normal/volume/period/both
   initial and final modes, all channels, manual/DMA playback, short/normal
   periods and boundary-adjacent switch times. Place a holding-word arrival
   before/after the switch on the same clock. Observe source buffer/sample,
   audible gating, target registers, DMA request and interrupt edges separately.
2. Run an explicit native example in
   `crates/emu198x-commodore-paula-8364/examples/live_attachment_probe.rs`.
   Validate a nonempty exact inventory, count differences by observable and
   retain complete baseline logs. Keep reference disagreement visible; do not
   equate the vAmiga sampler's repeated-edge suppression with the raw buffer.
3. Trace any disagreement through
   `crates/machine-commodore-amiga-ocs/tests/paula_phase2_machine.rs` and live
   OCS/ECS/AGA restore using existing runtime facilities. Prefer a bounded
   representative trace once the component matrix identifies the mechanism.
4. Record primary observations under the umbrella Amiga reference library,
   then update this plan with findings, limits and the concrete next correction.
   Verification alone must not be described as a hardware-accuracy fix.
5. Run the existing component regressions, formatting and strict Clippy for
   changed diagnostic code. Commit and preserve the verification evidence.
   If correction requires a materially different saved stage, write its design
   and follow the existing approval requirement before changing that schema.

## Verification result

The reference matrix contains 60,928 observations in 5,632 scenarios. Both
references agree on source buffer, state, IRQ, target registers, requests,
held loop and delivery. vAmiga's repeated-edge sampler suppression accounts
for 8,304 raw-sample disagreements; keep these visible rather than treating
its sampler as a second raw-output oracle.

The native example matches every timing/control observable but has 31,152
buffer and sample mismatches, including 7,680 unchanged-mode controls. There
are 1,824 unmuted sample mismatches. The concrete native failure is:
`left: [0, 0, 31152, 31152, 0, 0, 0, 0, 0]`,
`right: [0, 0, 0, 0, 0, 0, 0, 0, 0]`.

`crates/runtime-commodore-amiga/examples/paula_live_attachment_board.rs`
reproduces a period-eight volume-to-normal transition on OCS/ECS/AGA and all
four channels. All 48 restore checkpoints preserve deterministic replay but
fail the reference's audible-zero interval: `left: 48`, `right: 0`.

## Next correction

Treat the existing source output buffer as retained hardware state, independent
of whether a word is queued. Volume attachment diverts a high-entry buffer
load into the target volume latch; period transfer leaves the output buffer
alone. Ordinary high entry loads the persistent DAT holding latch rather than
requiring a queued-word marker. Audit manual startup, DMA startup, normal high
entry and idle/startup cancellation against that same rule.

Prefer correcting the existing `current_word`/holding stages, preserving the
request and interrupt logic that this sweep already validates. Start by
checking whether those fields can retain the physical buffer through every
state without conflating it with fetch eligibility. Do not assume a schema
change is needed; if an additional saved latch proves necessary, record the
concrete design before applying the existing breaking-change approval rule.
The alternative of fixing only unmute would hide the incorrect retained state
and is rejected by the reference buffer observations.

Production code and snapshot version 60 are unchanged by this verification.
The next fix should promote these diagnostics into enforced regressions and
repeat the existing modulation/handover/restore and waveform gates.

Verification checks pass: all 114 existing component tests, strict Clippy on
both diagnostic packages/all targets, Rust formatting and Ruff. Both diagnostic
executables were rerun after final edits and exited 101 only after completing
the full expected inventories. Logs and hashes are retained in `validation.json`.
