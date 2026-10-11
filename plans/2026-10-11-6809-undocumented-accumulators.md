# MC6809 undocumented accumulator operations

Engineering-frontier accuracy work for issue #130. The core diagnostic-halts on
42/52, 4B/5B and 4E/5E. Published original-device observations identify these as
conditional NEG/COM, DEC with carry, and CLR preserving carry. The full XRoar
CPU implements their two-cycle register operation and next-PC discarded read.

This bounded correction uses existing arithmetic helpers and existing
`Internal`/CLR stages. No new fields, enum variants, APIs, dependencies or
snapshot version are required. Memory forms, prefix behaviour and other
undocumented instructions remain separate work; this is not a replacement for
the pending timed memory sequencer in docs PR #92.

## Design

- 42/52: choose existing NEG when input C=0, otherwise existing COM.
- 4B/5B: perform existing DEC and set C from whether the original byte is nonzero.
- 4E/5E: clear the accumulator with N=0, Z=1, V=0, preserving input C.
- Use the existing one-cycle discarded next-PC read after the opcode.
  Do not add serialized RMW variants for operations completed during decode.

[Hardware observations](https://github.com/hoglet67/6809Decoder/wiki/Undocumented-6809-Behaviours)
and XRoar revision `b8491ab945d3e83fc1e98d62359813cf8a537d1d` independently
anchor the semantics. No new physical measurement is claimed.

## Work and verification

1. Preserve source-backed observations in the primary reference library.
   Compile the unchanged full XRoar CPU over six opcodes and all 256 value/CC
   combinations: 393,216 results. Check the two-read bus sequence and unchanged
   registers in the wrapper; retain result byte and complete flags with hashes.
2. Add a regression in `crates/motorola-6809/src/lib.rs`, with
   `crates/motorola-6809/tests/data/undocumented-accumulators.bin`.
   Run all reference cases at PCs 4000/FFFE/FFFF (1,179,648 executions), comparing
   complete flags, unchanged registers, bus reads, count and next-fetch pins.
   Confirm the diagnostic-halting baseline fails before changing decode.
3. Add only these six decode cases using the existing operation/stage patterns.
   Update the opcode coverage test's explicitly supported undocumented slots.
   Preserve diagnostics for all remaining unimplemented slots.
4. Run CPU/Dragon tests, targeted Clippy and workspace formatting. Commit and
   push a scoped PR, ordered after the preceding DAA correction. Merge only
   after exact-head CI succeeds. Retain #130 for remaining behaviours.

## XDEC reference exception found before implementation

The unchanged reference results disagree with the published hardware rule in
XDEC carry: XRoar's `op_xdec` sets C when the input is zero. David Banks's
original-device record, his 6809Decoder `xdec_helper`, and MAME's `XDEC8`
all set C when the original input is nonzero. Preserve the full XRoar binary
unchanged. Qualify every other result bit against it, then require XDEC C
separately from the published hardware rule. No flag is left unchecked.
The exception applies only to 4B/5B's C bit; no bus event or other flag is masked.

The permanent baseline regression initially fails all 1,179,648 runs because
the core diagnostic-halts. Repeat that red check after adding the explicit
hardware-carry assertion, before production edits.

## Validation

All 1,179,648 public-pin executions pass with the hardware-correct XDEC carry.
A deliberate production mutation using the reference's inverted XDEC carry
fails exactly 393,216 executions; restoring the implementation makes the
regression pass again. The unchanged reference fixture remains intact.

94 CPU tests, 75 Dragon machine tests and two synthetic-firmware integration
tests pass, none ignored. Targeted Clippy with `-D warnings` and workspace
formatting pass. Only six decode arms and their explicit supported-slot test
entries change; existing operation/state enums and snapshot schemas remain
unchanged. All input flag patterns, accumulator values, unchanged registers,
normal/wrapping PC reads and next-fetch pins are covered.

Reproduce the unchanged reference (XROAR points to the pinned checkout):

```sh
cc -std=c11 -O2 -Wall -Wextra -Werror \
  -I "$XROAR" -I "$XROAR/src" -I "$XROAR/portalib" \
  reference.c "$XROAR/portalib/delegate.c" -o reference
./reference > regenerated.bin
cmp results.bin regenerated.bin
```

The 786,432-byte fixture stores output accumulator followed by complete CC,
in opcode order 42/52/4B/5B/4E/5E, then input byte 00..FF and CC 00..FF. The
reference wrapper asserts both reads and unchanged registers. Hashes and all
red/green/mutation evidence are retained beside this plan. Memory variants,
prefix handling and remaining undocumented instructions are still outstanding.
