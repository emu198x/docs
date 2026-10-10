# Oric cassette recording: verify the signal before capture

Lane: engineering-frontier accuracy. Follow-up to the shared VIA output correction.

## Result

The real Atmos BASIC ROM executes a keyboard-entered `CSAVE"X"`, drives the
motor for 1,958,469 observed CPU clocks and returns to Ready. During that
window the probe observes 7,410 PB7 transitions, no CB2 transitions, and
ACR's timer-1 PB7-output bit enabled throughout. No tape bytes are captured
or exported by the current machine/runtime.

A negative control samples CB2 in place of PB7 and fails with
`recording must contain a substantial PB7 waveform`, reporting zero edges.
Both programs, output, ROM/library/binary hashes and commands are retained
in the adjacent folder. No firmware is included. The first standalone link
failed with `Unknown attribute kind (105)` because the release libraries
contain Rust LTO bitcode; compiling the probe with `-C lto=thin` resolves
that toolchain mismatch without rebuilding or changing the machine.

The probe samples at instruction boundaries. It establishes the output
route and the missing capture boundary; it does not establish exact edge
phase, complete framing or recording round-trip fidelity. It saves an empty
BASIC program, so it does not cover memory blocks, slow mode or arrays.

## Sources

The [Oric Products International service manual](https://oldcrap.org/wp-content/uploads/2023/04/oric-service-manual.pdf)
(1984), pp. 18–20, describes timer-generated recording and printer signals.
The [original Oric-1 48K schematic](https://homepages.uni-regensburg.de/~hep09515/oric1/oric1-1p.gif)
connects PB7 to tape output and PB6 to the relay, while CA2/CB2 connect to
AY BC1/BDIR. IC6 pin 17 is PB7; pin 16 is PB6. MAME `via_b_w` and
Oricutron `via_main_w_iorb` independently corroborate the board routes.

The private reference correction is merged as umbrella PR 60. Source PR
1698 corrects stale labels in the crate documentation; it changes no
executable source and its warnings-denied rustdoc build passes.

## Remaining issue #342

1. Capture actual PB7 output transitions at the machine's CPU clock boundary,
   including timer output and PB6/DDR motor changes. Capturing ORB writes alone
   loses the timer waveform. Preserve raw durations so unknown/custom signals
   are not discarded by a decoder.
2. Preserve in-flight capture, motor state and completed recordings in saves.
   This needs an agreed snapshot schema change; the current Oric version is 7.
3. Decode supported ROM framing and use the existing
   `format198x-tangerine-oric-tap` dependency's `encode` at the runtime boundary.
   The codec already exists; do not create another format crate. Its binding
   decision rejects ambiguous STORE array records until they can be preserved.
4. Expose recording export through the appropriate shared capability. Export
   creates a new file; neither playback mounting nor recording writes back to
   the original input path. A sidecar flush is not the project's persistence
   model: snapshots preserve machine/media changes.
5. Verify ordinary BASIC and memory-block SAVE → exported TAP → real-ROM LOAD,
   fast and slow recording, multiple files, motor interruptions and save/restore
   at partial-pulse/header/body boundaries. Reject unsupported conversion
   explicitly while retaining the underlying recording.

No capture-stage, API or snapshot design is approved or implemented by this
wiring correction. Keep #342 open until its recording requirements pass.
