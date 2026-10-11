# Respect 6845 register widths and write protection

Lane: engineering-frontier accuracy. This is a correction to the existing
register file, with no new state, dependency, architectural pattern or public
type change. It follows the independently tested sync-width correction #1736.

## Root cause and evidence

`write_data` stores every input byte in R0–R17. The hardware has fewer writable
bits in several registers, and R16/R17 are read-only. Most counter uses mask
their inputs, but R6's display comparison and readable address bytes expose the
stored invalid bits.

An original public-port probe on source `411092c1` produces 1,852 failures in
2,560 cases. R12 (S only) and R14 return invalid high address bits; both variants
allow software to replace light-pen readback. Toggling only R6 bit 7 changes the
display-enable trace in all 256 alias comparisons. Writable R15 controls pass.

Primary masks and access permissions: Motorola 1977 PDF p. 11, Table 2;
Hitachi U70-A (1987) printed p. 147 / PDF p. 158. Source records and page images
were inspected for #168. MAME's `mc6845_device::register_w` applies the matching
R4–R7/R9–R15 masks and rejects writes to R16/R17. MAME stores all bits of R3/R8
internally for its wider family; use the manufacturer table for each supported
personality rather than copying that storage choice.

## Work and verification

1. Compile unchanged MAME register-write switch cases in a small harness for
   the shared masks and light-pen protection, retaining its source hash.
2. Add public-port regressions in
   `crates/motorola-6845/tests/register_writes.rs`: all 256 values, both parts,
   address readback, preserved light-pen values, and equivalent display-enable
   traces when only the unused R6 bit changes. Demonstrate failure before code.
3. Extend the existing per-variant register logic with the documented masks.
   Reject writes outside R0–R15. Preserve the existing readback selection and
   data-port behavior for unselected/unreadable registers. Do not add a light-pen
   capture implementation or claim the strobe works.
4. Keep snapshot loading compatible: apply masks to new guest writes, with no
   schema change or new rejection of existing saves. Verify normal round-trip
   and preserved read-only values, including values supplied by a prior save.
5. Run the unchanged 2,560-case probe and chip regressions; rerun affected
   machine/Gate Array tests, the selected 16 firmware checks and Clippy. Rebase
   the bounded commit onto merged #1736 before opening its source PR.
6. Publish the captures and update chip/private knowledge after verified merge.
   Keep unrelated changes and active investigations intact.

This does not close #166: full interlace/skew still needs separate timing work.
