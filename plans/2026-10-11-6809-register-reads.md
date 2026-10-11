# MC6809 register instruction discarded reads

Engineering-frontier accuracy work, continuing the verified bus-read correction
in source PR #1716. The compiled full XRoar CPU exposes wrong discarded reads
in 22 additional documented register instructions. Their current stages drive
FFFF where the reference reads the next program byte. Total cycle counts and
all defined result flags agree in the sampled cases. This is separate from
the pending indexed-memory sequencer and Dragon snapshot design in docs PR #92.

## Evidence and limits

The probe covers 34 encodings, eight A values (B is A XOR A5), four CC seeds
and PCs 4000/FFFE/FFFF: 3,264 rows. It includes the ten corrected opcode/control
encodings from PR #1716. The additional candidates are DAA, SEX, ABX, MUL,
ANDCC, ORCC, and A/B forms of COM, ROR, ASR, ASL, ROL, DEC, INC and CLR.
The full unchanged reference is pinned to XRoar
`b8491ab945d3e83fc1e98d62359813cf8a537d1d`; baseline core is
`8aabf2ec56e41870429c17a9d8fc9faca70344be`.

Two findings are not part of this bus selection change:

- TSTA/TSTB take three cycles in this XRoar revision, while Motorola's
  [opcode map](https://www.maddes.net/m6809pm/appendix_f.htm) specifies two.
  Preserve all 192 diagnostic rows, but do not adopt the reference timing or
  claim its trace is authoritative for these two instructions.
- DAA differs only in V in 48 rows. Motorola calls V undefined in the
  [DAA entry](https://www.maddes.net/m6809pm/appendix_a.htm); XRoar cites a
  hardware-derived calculation. Keep this as a separate undocumented-flag
  investigation. The bus regression masks only DAA V when comparing results;
  it still compares every bus event and every defined flag.

No new fields, enum variants, schema, public interface or dependencies are
needed. Use `read_next` to enter the existing `Internal`/`Clr*Internal` stages.
ABX and MUL retain their existing remaining-cycle count; subsequent internal
cycles still drive FFFF. ANDCC/ORCC read the next PC after consuming their
immediate byte. Do not change the generic dummy-cycle helper.

## Work and verification

1. Retain reference wrapper, public-pin probe, complete 3,264-row output and
   baseline comparison under this plan. Record source and output hashes.
2. Add `register_reads_match_full_reference_bus_traces` in
   `crates/motorola-6809/src/lib.rs`, backed by
   `crates/motorola-6809/tests/data/register-reads.txt`: 3,072 qualified rows
   after excluding TSTA/TSTB. Assert per-opcode coverage, next-fetch pins,
   values, counts, memory and ordered bus reads. Verify failure before edits.
3. Change only demonstrated read selection in the existing instruction arms.
   Update the official PC-window test to require the independently verified
   next-PC access for these encodings instead of rejecting it.
4. Run CPU/Dragon machine tests, formatting and targeted Clippy. Preserve the
   failing baseline evidence; report DAA V and TST limitations explicitly.
5. Commit, push and open a bounded source PR and evidence PR. Merge only after
   checks pass. Keep issue #130 open for the remaining opcode/timing work.

## Validation

The permanent regression initially failed with `1472 / 3072 bus vectors
differ`. It now passes all 3,072 qualified rows, including the ten earlier
opcode/control encodings, both PC wrap positions and the next-fetch pins.
The full 3,264-row diagnostic retains all 192 TSTA/TSTB timing mismatches and
48 DAA V differences; no other value, cycle or trace differences remain.

The existing dummy-access test had incorrectly used CLRA as an FFFF-read
example. It now checks ABX's independently verified sequence: next-PC read,
then FFFF. This preserves a positive assertion of the generic internal-cycle
pin shape instead of deleting that coverage.

- 92 CPU unit tests, 75 Dragon machine unit tests and 2 synthetic-firmware
  integration tests pass, none ignored.
- Targeted CPU/Dragon Clippy with `-D warnings`: pass.
- Workspace Rust formatting: pass.
- State fields, state enum variants, public interfaces and snapshot version
  remain unchanged; only initial read-address selection changes.

Reproduce the full reference (XROAR points to the pinned checkout):

```sh
cc -std=c11 -O2 -Wall -Wextra -Werror \
  -I "$XROAR" -I "$XROAR/src" -I "$XROAR/portalib" \
  reference.c "$XROAR/portalib/delegate.c" -o reference
./reference > regenerated.txt
cmp reference.txt regenerated.txt
python3 compare.py reference.txt before.txt
python3 compare.py reference.txt after.txt
```

The reference wrapper supplies memory and the instruction-end hook; instruction
semantics come from the full external CPU. Build `probe.rs` with Rust 1.99
against the matching `motorola-6809` rlib, as in the indexed diagnostic.
Full output and hashes are retained beside this plan. The wrappers compare
address/read-write/data events, not a new physical capture or every sideband
signal. The regression checks next-fetch pins separately in our core.
