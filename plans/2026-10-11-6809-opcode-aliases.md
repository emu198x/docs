# MC6809 opcode aliases and bus verification

Part of https://github.com/emu198x/emu198x/issues/130, not its complete resolution.

The live core halts after one cycle on 1B, 01/41/51/61/71 and
05/45/55/65/75. David Banks's hardware-validated undocumented-opcode record
identifies these as NOP, NEG and LSR aliases; XRoar routes them through those
same operations. The corresponding documented instructions complete in 2-7
cycles in the current core. This gives a bounded correction using existing
stages, with no schema, API or dependency change.

## Steps

1. Preserve the original hardware source in a primary observation note. Compile
   the unchanged XRoar MC6809 core in an isolated memory/trace wrapper. Capture
   address, read/write and byte events for all eleven aliases and documented
   controls. Verify its alias traces agree with their documented counterparts.
2. Add failing regressions in `crates/motorola-6809/src/lib.rs` through public
   CPU pins. Compare registers, memory writes, cycle counts and bus addresses;
   cover operand and condition-code boundaries, plus addressing modes. Check
   independent reference traces, rather than relying on two paths through this
   emulator agreeing with each other. NOP's discarded read currently appears
   different from XRoar; measure and resolve that before claiming trace parity.
3. Extend existing opcode match arms with the confirmed aliases. Correct only
   demonstrated bus-address selection in the existing instruction stages.
   If a correction requires new state or changed snapshot schema, record the
   concrete design and obtain approval before implementing that extension.
4. Update diagnostic-halt tests that currently use a now-supported alias; keep
   the remaining unimplemented-opcode diagnostic behaviour explicitly covered.
   Keep official opcode metadata distinct from observed undocumented aliases.
5. Run CPU/Dragon tests, formatting and Clippy, commit and open a bounded PR.
   Keep #130 open for other opcodes, prefix behaviour and indexed-postbyte work.

Sources:
- https://github.com/hoglet67/6809Decoder/wiki/Undocumented-6809-Behaviours
- XRoar revision `b8491ab945d3e83fc1e98d62359813cf8a537d1d`,
  `src/mc6809/mc6809.c`, `mc6809_common.c` and `src/mc680x/mc680x_ops.c`.

The hardware source and reference implementation are different evidence layers.
XRoar's HCF loop itself is not a complete hardware bus model, so unrelated
undocumented behaviours must not be accepted wholesale merely by matching it.

## Measured fault and staged correction

The unchanged full XRoar CPU ran 1,056 cases: eleven alias/control pairs,
six operand values, four condition-code seeds, and PCs 4000/FFFF. All 528
aliases halt in Emu198x. All 528 documented controls finish with the expected
values and cycle counts but differ in bus addresses or placement of accesses.
The [comparison](2026-10-11-6809-opcode-aliases/before-summary.json) retains
examples. The reference wrapper supplies memory and an instruction-end hook;
it does not replace reference instruction logic. A first wrapper compile
needed parentheses around pointer arguments to XRoar's register macros; the
corrected wrapper compiles with all warnings treated as errors.

For direct NEG, the reference sequence is opcode, operand, FFFF read, data
read, FFFF read, data write. Our sequence is opcode, operand, data read, data
write, FFFF read, FFFF read. Moving the two idles after the write preserves the
total but changes when peripherals observe it. Extended and indexed forms
show the same early read/write problem. Inherent forms discard-read PC+1 in
the reference, whereas our existing stages drive FFFF.

### A: Existing stages, no snapshot change

Correct NOP and register NEG/LSR discarded reads in their existing stages and
enable their five inherent aliases. Verify all 480 corresponding reference
rows, including PC wrap, before committing. Keep the six memory aliases and
memory timing correction together in stage B; do not enable them against the
known-wrong bus schedule. This does not close #130.

### B: Proposed stage extension — approval required

Extend the existing CPU address/RMW sequencer rather than changing the CPU
interface or building an instruction-level execution path:

- Add an address-idle stage retaining the resolved RMW address and operation
  before the operand read (direct/extended forms).
- Add a write-idle stage retaining the computed address and result between
  the operand read and write. Finish the instruction at the actual write;
  TST keeps its two no-write idle cycles instead.
- Extend the existing indexed-delay stages to retain whether the upcoming
  cycles read PC/PC+1 or FFFF, and whether to fetch an indirect pointer before
  the final operand. Apply this scheduling correction to the RMW path first.
  Do not use total-cycle padding after a side effect to impersonate earlier
  idle cycles. Validate every currently supported indexed postbyte form.
- Serialize those real pending phases and values through the CPU's existing
  serde state. Advance Dragon-family runtime snapshots from 1 to 2, rejecting
  v1 before payload decoding or machine mutation. No migration or guessed
  reconstruction of a partially executed old instruction.

Exact implementation files: `crates/motorola-6809/src/lib.rs`,
`crates/runtime-dragon/src/runtime.rs`,
`crates/runtime-dragon/tests/snapshot_roundtrip.rs`, and the CPU fixture folder.
Check shared RMW operations, all supported indexed postbytes, next-fetch pins,
per-cycle write timing and snapshot continuation in every newly pending phase.
Run CPU, Dragon machine/runtime tests and Clippy. Other indexed load/store
schedules and the remainder of #130 stay explicit follow-ups.

Reproduce the reference (point XROAR at the pinned external source):

```sh
cc -std=c11 -O2 -Wall -Wextra -Werror \
  -I "$XROAR" -I "$XROAR/src" -I "$XROAR/portalib" \
  reference.c "$XROAR/portalib/delegate.c" -o reference
./reference > reference.txt
```

The 1,056 rows must match the committed fixture and source hashes.

## Stage A validation

The new permanent regression was red before production changes: all 480
inherent rows differed (either diagnostic halt or wrong discarded-read
address). It now passes every row. Only the five existing instruction match
arms/stages change; no fields or serialized variants change. The official
opcode-table test now distinguishes documented instructions, verified aliases
and still-unimplemented slots. The PC-window test explicitly checks the
verified second-cycle read instead of forbidding it.

- CPU/Dragon suite: 91 CPU tests, 75 machine unit tests and 2 synthetic-firmware
  integration tests pass, none ignored.
- Targeted CPU/Dragon Clippy: pass with `-D warnings`.
- Stage B remains proposed, pending explicit snapshot/design approval.

This closes the inherent portion of the matrix, not the memory timing fault
or issue #130 as a whole. The native reference's 1,056 rows remain preserved
so the unresolved cases stay visible.

## Indexed validation preparation

Before implementing stage B, extend the independent full-core wrapper to all
220 currently accepted indexed postbytes, all eleven documented memory RMW
operations, five offset-byte patterns, four complete register seeds and normal
or wrapping PCs (96,800 cases). Generate common input rows, then run those rows
through the unchanged reference and the public-pin core independently. Compare
final registers, cycle counts and every ordered read/write event. Report exact
counts and representative failures by operation/postbyte, with source/input
hashes and assertions against empty, duplicate or incomplete output.

This is diagnostic preparation only; it does not implement the proposed
snapshot extension. Keep source and generated temporary outputs outside the
reference checkout. Retain the input generator, wrappers and compressed traces
with the plan so an approved correction can be checked against the same cases.

## Indexed diagnostic result

The [archived diagnostic](2026-10-11-6809-opcode-aliases/indexed/README.md)
executes all 96,800 planned cases. All final registers, write addresses/data
and total cycle counts match the reference. Bus events differ in 96,776 rows:
every one of the 88,000 writes occurs exactly two cycles early. TST differs in
8,776 of its 8,800 traces; its 24 exact rows are coincident addresses/data,
not evidence that those addressing modes are generally correct.

Nine comparator tests verify full-reference equality, reject incomplete or
malformed inputs and detect injected register, cycle and write errors. Both
compiled probes reproduce the archived traces byte-for-byte; all three ZIP
members have verified row counts and SHA-256 hashes. This is flat-memory
reference evidence, not a physical capture or sideband/next-fetch validation.
The proposed stage B acceptance checks still need those additional checks.

Stage A merged as PR #1716, commit
`8aabf2ec56e41870429c17a9d8fc9faca70344be`, after all applicable CI checks
passed. Stage B remains pending approval; #130 remains open.
