# Reject truncated SN76489 register states before mutation

Engineering-frontier bug fix discovered while auditing issue #149's save-state
boundary. `Sn76489::save_state` emits 30 register bytes, but `load_state` checks
for only 27 before reading all 30. Inputs of 27–29 bytes can panic after partial
mutation. The claimed 27-byte size in its layout comment is also wrong.

This small correction preserves the existing byte layout and public signature.
Use the actual encoded size, 30, as the minimum; reject incomplete payloads
before changing the chip. It neither adds serialized fields nor changes runtime
snapshot versions. The separate serde-based full-machine format and the pending
stereo pipeline are outside this fix.

1. Add regressions in `crates/ti-sn76489/src/lib.rs` comparing the encoder's
   output length with accepted input, checking every truncated length and
   unchanged destination registers, and verifying trailing bytes remain unread.
   Run against the old guard to establish a failing baseline.
2. Change the minimum byte count and layout documentation in the same file.
3. Run the chip suite, targeted Clippy and workspace formatting. Verify the
   public-API truncation probe switches from panic/mutation to error/no mutation.
4. Commit, push and merge a scoped PR after its exact-head checks pass. Keep
   #149 open: this repairs its audited loader, not the panning/output fault.

## Evidence

The public-API baseline confirmed all three lengths, 27/28/29, both panic and
change destination registers. The new unit regression also failed at length 27:
`index out of bounds: the len is 27 but the index is 27`.

With the two-line production/documentation correction, all 30 incomplete
prefixes return an error without changing encoded registers. Complete records
round-trip and consume exactly the encoder's output length, leaving an appended
sentinel untouched. All 18 chip tests pass, with targeted Clippy (`-D warnings`)
and workspace formatting clean. No format bytes, public signatures, dependencies
or serialized fields changed.

The probe, red/green logs and SHA-256 hashes are retained beside this plan.
Build `ti-sn76489` at the recorded source revision, compile `probe.rs` with
`rustc --edition=2024`, passing that build's `libti_sn76489.rlib` through
`--extern ti_sn76489=...` and its `deps` directory through `-L dependency=...`,
then run the executable. The baseline exits 101 with three bad lengths; the
corrected source exits zero with `truncated cases=30, bad=0`.
