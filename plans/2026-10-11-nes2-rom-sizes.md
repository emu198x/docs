# Decode NES 2.0 exponent/multiplier ROM sizes

Issue #81 covers several missing header fields. This correction addresses
its confirmed ROM-boundary calculation first, within the existing parser API.
Submapper, timing, console and RAM metadata remain part of the full issue.

1. Reproduce rejection of exponent-encoded PRG and CHR sizes in
   `crates/format-nintendo-nes-ines/tests/nes2_rom_sizes.rs`. Compare the same
   payload under linear and exponent headers, verify CPU/CHR reads and
   trainer offsets, and test odd multipliers with explicit byte lengths.
2. Check the format specification and the vendored Mesen2 `NesHeader.cpp`
   reader. Record new source-backed facts in the primary reference library.
   Exercise the reference's size methods independently where their 32-bit
   result can represent the specified size.
3. Correct the existing calculations in
   `crates/format-nintendo-nes-ines/src/format.rs`, using checked integer
   arithmetic for exponent sizes and total file offsets. Reject truncated
   or unrepresentable declarations before constructing a mapper. Retain
   the existing header struct and mapper/snapshot interfaces.
4. Run the parser suite, affected NES machine/runtime tests, Clippy and
   formatting; require actual regression failures before the fix. Review
   mapper read boundaries exposed by the newly accepted sizes rather than
   assuming a successful parser return proves safe reads.
5. Commit this bounded change, require source PR CI before merge, publish
   the evidence and update #81 without claiming its omitted fields are done.

## Result and evidence

Source [PR #1730](https://github.com/emu198x/emu198x/pull/1730), tested head
`f3604fa2e752dabe1e6a4274d6fd41e3b4bbdf95`, corrects both encodings without
changing the public header or save-state format. The bounded primary note is
`reference/by-system/nintendo-nes/2026-nes2-rom-size-observations.md` in the
umbrella repository.

Before the fix, a 40,976-byte exponent image was rejected with
`iNES file too short: expected 63905808 bytes, got 40976`. A trainer-bearing
odd-sized image was rejected with
`iNES file too short: expected 95617552 bytes, got 12816`.
The corrected decoder then exposed a second fault: a 4 KiB NROM CHR payload
could reach an out-of-bounds index of 4096. The loader now rejects sizes that
cannot fill the existing mapper implementation's bank windows before creating
the mapper. These are implementation limits, not container-format limits;
we do not pad payloads or infer board mirroring from the file size.

Six new integration tests cover byte-for-byte linear/exponent equivalence,
trainer placement, all four odd multipliers, exact CHR boundaries, truncation,
extreme-size errors, existing mapper limits, supported mapper windows and
linear high nibbles. The equivalence fixtures deliberately use exponent forms
where the specification prefers linear encoding. Odd-sized fixtures are
parser controls; they do not establish historical board wiring.

The compiled comparison checks all 4,096 size-byte pairs for both ROM areas:
7,926 results match Mesen2 within its 32-bit range; the remaining 266 are
checked with exact integer arithmetic. Ten results exceed 64-bit address
space and are rejected. This is a helper comparison, not a Mesen2 boot test.

The affected parser, machine and runtime invocation passed 186 tests with
zero failures. It left 135 explicitly ignored fixture/diagnostic tests
unexecuted; this is not a claim that the complete hardware corpus passed.
All six new tests ran, as did synthetic boot and save-state round trips.
All-target Clippy with warnings denied, workspace formatting and diff checks
passed. The portable evidence host passes Ruff and reproduces the comparison.
See [the evidence bundle](2026-10-11-nes2-rom-size-evidence/README.md).

## Remaining issue #81 scope

Keep [#81](https://github.com/emu198x/emu198x/issues/81) open. Submapper,
timing/region, console type, explicit PRG/CHR RAM and NVRAM metadata still
need integration. In particular, absence of CHR ROM still follows the existing
mapper RAM defaults; this change does not implement NES 2.0 RAM sizing.
A legal container layout rejected by a mapper needs board-specific evidence
and a mapper correction before it becomes supported. Public metadata or
snapshot changes require the existing design/approval process.
