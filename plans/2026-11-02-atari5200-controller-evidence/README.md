# Atari 5200 controller correction evidence

[Scanner correction #2239](https://github.com/emu198x/emu198x/pull/2239) and
[restored-media correction #2241](https://github.com/emu198x/emu198x/pull/2241)
precede the three physical-board extractions under #2144.

The unchanged October original guest runs on a pristine `d57ba23fa` checkout
and the corrected source. All 420 cases have advancing guest loop counters:
222 fail before correction, none fail after. The original guest, complete
reference scanner, connectivity and scheduled-transition harnesses remain in
[the October evidence](../2026-10-11-atari5200-controller-evidence/README.md).
The scheduled reference harness was rerun: 1,748 cases pass again.

The production scanner matches all 2,048 frozen reference cases and 65,536
key-subset/upper-fire combinations at all 64 mirrored addresses. Compact
chip-state continuation covers every one of the 114 scan phases. Bypassing
debounce makes the reference test fail; moving the CPU bus write one clock
early makes the startup test fail at 160 instead of 162 colour clocks.
These are captured failures, not ignored assertions.

Local checks: 230 focused tests pass, five existing diagnostic/fixture tests
ignored; six affected chip/machine/runtime targets pass Clippy with warnings
denied. The real BIOS plus Pac-Man boot test passes separately. The adjacent
restore correction passes 61 machine/runtime tests (one fixture ignored),
including explicit header-selected two-chip and banked layouts. ROMs are not
included; identities are recorded in `provenance.json`.

The 800XL/7800 frozen outputs remain unchanged. Their original envelopes are
compared after accounting for the new envelope version and exactly one zero
Option byte for an unattached scanner; every other chip-state byte and every
frame/audio packet must match. Production readers reject old envelopes.

An initial CI test runner exhausted disk and lost its diagnostic log before
completing. `ci-disk-failure.json` preserves GitHub's annotation. The follow-up
bounds test artifacts and records free disk around the build/cache steps.
A complete executed CI ledger is required before merging.

A local comparison also detected a shared-target Cargo cache collision
between worktrees. The definitive corrected captures were taken only after
cleaning and rebuilding the affected local crates. The original executable
was retained separately; its source checkout was clean. The collided output
is excluded from this evidence.

Run `python3 verify.py`. It checks all capture identities/coverage and guest
execution counts, verifies file hashes and rejects twelve malformed-capture
controls. Passing this archive check alone does not establish a passing CI
run or a qualified physical board. Analogue charging calibration, trackball
behaviour and separate board ownership remain outside this correction.
