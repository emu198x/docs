# Remove unsupported Paula sample compression

Follow the approved sampling correction with the next bounded audio accuracy
issue. Keep pushing deferred. Do not mix this production change into the
sampling/v61 commit.

1. Verify the current cubic conversion in
   `crates/emu198x-commodore-paula-8364/src/lib.rs` and its provenance. Commit
   `3a5adcfd` attributes `x - 0.02*x*x*x` to A500/WinUAE measurements without
   identifying a capture or curve. The pinned WinUAE scalar path and vAmiga
   `penhi`/`penlo` instead retain the nominal signed byte amplitude. HRM ch.5
   defines digitised amplitude samples and their signed limits. Keep actual
   chip-specific DAC errors distinct from this unsupported generic polynomial.
2. Reproduce amplitude discrepancies at forced-full volume, where the PWM
   phase question cannot affect output. Sweep all 256 encodings on all four
   channels against the documented nominal signed-amplitude scale and stereo
   routing. Preserve the failing inventory before changing production.
3. Replace only the cubic table conversion with signed-byte normalisation.
   Retain volume, routing, host gain, mute, pipeline and snapshot v61. This is
   a small correction with no new architecture, dependency or public schema.
   Record explicitly that it supersedes the historical port plan's suggestion
   to inherit the archive DAC curve. Do not claim physical DACs are perfectly
   linear; a measured nonlinearity model needs actual evidence.
4. Run component and affected runtime/audio tests, strict Clippy, release
   build and ROM-backed waveform gate. Recheck the signed endpoints, zero,
   full-volume routing and half-volume ratio. Record the primary evidence,
   update the decision, and commit the correction separately.

## Reproduced and corrected

The new reference runner reuses the pinned handover extraction and executes
the actual WinUAE scaling macro and vAmiga startup/sample methods. Both
references agree on every signed amplitude in 2,048 cases: all 256 encodings,
all four channels, and forced-full volumes 64/127. Empty and corrupted output
are rejected. The final native test consumes the compiled CSV and fails in
2,040 cases before correction; only the eight zero-amplitude cases agree.

The production change removes the unsupported table and normalises the
retained signed sample directly. All component tests pass. No pipeline or
snapshot field changes; snapshot v61 remains current. The primary evidence
explicitly supersedes the inherited-curve suggestion in the old port plan.
All 120 component tests and 128 affected runtime tests pass, including the
65 snapshot cases and both Paula board tests. Strict Clippy, the release
build, all three ROM-backed waveform cases, formatting and Ruff pass.
Both references' CSVs, compressed C++ and source-provenance report regenerate
byte-for-byte. Full-volume right RMS is now 0.353238153 and half-volume RMS
is 0.176619079; routing and 3464.4351464435144 Hz measured cadence pass.
The first runtime command named two nonexistent targets; the corrected
command ran their coverage in `snapshot_roundtrip` and both actual board
test targets. Logs, that command failure and final results are archived in
the amplitude corpus's `validation.json`. This is a second separate local
correction; nothing is pushed.
