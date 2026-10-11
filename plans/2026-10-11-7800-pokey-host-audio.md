# Atari 7800 cartridge POKEY host-output gap

Engineering-frontier investigation of issue 193. Existing cartridge parsing
and machine wiring are present; verify the actual host-output chain before
claiming the issue is fixed.

## Plan

1. Build CPU-driven synthetic A78 cartridges for every accepted single-POKEY
   location and both regions, with silent, TIA-only, POKEY-only and mixed cases.
2. Capture the runtime AudioSink output and inspect the separate POKEY queue.
   Require nonempty inventories and positive/negative audio controls.
3. Trace actual clock/sample rates, existing mixer/resampler facilities and
   save-state boundaries. Avoid sequential packets or per-frame interpolation
   that changes simultaneous signals into concatenation or loses sample phase.
4. Preserve the failing probe and update issue 193 with the current mechanism.
   Any retained mixer state must have a concrete design and schema agreement.

Files: this plan and adjacent probe.rs/chip-red.log/summary.json. No production
change is authorised by the evidence alone; preserve the native MARIA WIP.

## Confirmed outcome

All **32 POKEY-active host cases fail**, while all **32 silent/TIA controls
pass**. The 64-case matrix covers NTSC/PAL, A78 v3/v4, all four accepted
single-POKEY locations ($0440/$0450/$0800/$4000), and four source combinations.
Real 6502 guest instructions program the chips and write a completion marker.
Every case emits four nonempty, finite host packets.

A separate direct-machine run provides the chip-output control, allowing a
future fixed runtime to consume its own queue fully. POKEY produces nonzero
samples in every active case. At the runtime sink, POKEY-only output is silent
and mixed output is byte-identical to TIA-only output. All 64 runtime runs leave
a separate POKEY queue undrained, including muted cartridges.

After four frames, the NTSC host has 2,104 TIA samples labelled 31,560 Hz while
3,216 POKEY samples remain queued at 48 kHz. PAL has 2,504 host samples labelled
31,300 Hz and 3,863 queued POKEY samples. These are current-core observations,
not a claim that nominal TIA rates represent exact hardware timing.

Cargo exits 101:

```text
assertion `left == right` failed: cartridge POKEY must contribute to host audio
  left: 32
 right: 0
```

The probe also requires the runtime to consume its POKEY queue after delivery.
That assertion follows the audible-output assertion, so the current failure
stops at the first one. Direct chip controls are separate from the runtime
queue and do not require a corrected runtime to leave samples behind.

## Root cause and correction boundary

`machine-atari-7800` already instantiates POKEY from cartridge metadata, routes
reads/writes and clocks it. `take_pokey_audio_samples` returns its 48-kHz queue.
The runtime calls only `take_audio_samples`, which drains TIA, and forwards that
one stream to `AudioSink`. No production caller drains the POKEY queue. Issue
193's claim that the machine lacks POKEY instantiation is therefore stale,
but its missing-audio outcome is still real.

The shared `AudioSink` is a single interleaved stream. Its capture implementation
rejects a change of rate/channels and the native implementation appends converted
packets. Sending a POKEY packet after a TIA packet would concatenate time,
not mix simultaneous signals. Frame-local interpolation would also lose the
fractional sample history at frame and snapshot boundaries.

The existing TIA core integrates channel volumes at colour-clock resolution
and emits at phases 37 and 149 of each 228-clock line: intervals alternate
between 112 and 116 clocks. Treating those as uniformly spaced nominal-rate
samples is not sufficient evidence for accurate mixed output.

A bounded correction should extend the existing machine audio path to combine
held TIA and POKEY signals on one master-clock timeline and emit one host stream.
Retain sample phase, partial contributions and any filter history in snapshots.
Keep chip clocks separate from host sample deadlines and route the native MARIA
clock correctly when integrating its pending branch. The proposed timed POKEY
stages address that clock/sample separation, but do not currently include this
TIA/POKEY host mixer. Additional saved mixer state needs a concrete extension
to that design and coordinated versioning; do not silently broaden its scope.

Gain/clipping and physical mixing remain validation gates. The
[Atari7800_MiSTer output mixer](https://github.com/MiSTer-devel/Atari7800_MiSTer/blob/29aaacbbed127c670972c8a0a950ca82dc87e5df/rtl/top.sv#L359)
combines held TIA and cartridge outputs before
host output, with explicit gain handling; this is implementation precedent,
not calibrated hardware amplitude. Its [cartridge IRQ](https://github.com/MiSTer-devel/Atari7800_MiSTer/blob/29aaacbbed127c670972c8a0a950ca82dc87e5df/rtl/cart.sv#L211)
is optional, so the old
issue's IRQ requirement must be checked against the supported board before
adding a connection. Neither electrical IRQ wiring nor gain is established by
the host-sink test.

No production change is made here. The temporary test is removed afterward.
Relevant source files are byte-identical to origin/main `03372dda`; hashes and
counts are in `summary.json`. Native MARIA work remains untouched.

## Reproduce

Copy `probe.rs` into an isolated source worktree as
`crates/runtime-atari-7800/tests/pokey_host_probe.rs`, then run:

```sh
cargo test -p runtime-atari-7800 --test pokey_host_probe -- --nocapture
```

Expected result on the recorded source: Cargo exit 101, 64 completed cases,
32 host failures and 64 undrained runtime queues. Remove only that temporary
probe afterward. `rustfmt --edition 2024 --check` passes for the retained probe.
