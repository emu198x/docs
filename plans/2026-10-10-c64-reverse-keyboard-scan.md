# C64 reverse keyboard scanning

Fix the missing direct PB-to-PA keyboard connection exposed by the maintained
Joystick Reading sample. Lane: engineering-frontier, failure-driven C64 accuracy.

The recorded PAL/NTSC probe holds Return (matrix position 0,1), drives PB1 low
with DDRB=$FF and sets DDRA=$00. VICE reads PA0 low; Emu198x reads it high.
Both detect Return in a forward scan. `C64::refresh_keyboard_scan` supplies
only joystick pins to PA, and `cia1_port_a_read` bypasses the keyboard entirely.

The approved bounded correction extends the existing direct-contact matrix
scan to the other direction. Read raw DDR-resolved drives, including PB timer
outputs and joystick pull-downs, rather than feeding previously resolved pins
back into the scan. No new state, snapshot schema, dependency or architecture.
The existing multi-key ghosting/output-contention limitations are not closed
by this correction; VICE has additional network and analogue approximations.

1. Add machine regressions in
   `crates/machine-commodore-c64/src/machine.rs`: reproduce Return, enumerate
   all 64 positions in both directions, release/DDR turnaround, joystick
   connections, timer-driven PB6/PB7 and snapshot continuation. Run them red.
2. Extend `src/keyboard.rs` with the reciprocal direct-contact scan. Wire PA
   input and CPU reads in `src/machine.rs`; use raw drives consistently for
   forward scans and the existing light-pen line. Preserve the public forward
   scan contract and serialized matrix representation.
3. Run machine, runtime and CIA tests, format and Clippy. Rebuild the native
   C64 runner. Rerun the maintained sample's PAL/NTSC probe and joystick suite;
   explicitly require the previously differing Return rows to match VICE.
4. Retain evidence and exact revisions/tool identities here; commit each repo
   separately, push and merge when its checks pass.

Sources: MOS Technology 6526 datasheet, sheet 5/8 (DDR, pin reads and timer
outputs); Commodore C64 Programmer's Reference Guide, p.94 and pp.320–322
(matrix and pin assignments). Implementation precedent: vendored VICE 3.10,
`src/c64/c64cia1.c`, `read_ciapa`, `read_ciapb` and light-pen wiring. The frozen
Older keyboard implementation was inspected: it has the same one-way scan
and supplies no missing reverse implementation to reuse.

## Results

Emulator source `a1679f5d9736c8c519c593039cdbeb08344602b2`; maintained samples
`f67d4aeb6921d5fefa87b529f996c20bf39de211`. The adjacent source identity file
records hashes of both changed Rust files. The native record carries the
assembler, reference/emulator binary, guest sources, PRGs and image hashes.

- Six new machine regressions failed before the correction (two existing
  forward-scan tests passed). All eight pass afterwards.
- Machine, runtime and CIA tests: 290 passed, 70 external-fixture/diagnostic
  tests ignored by default. Both real-ROM boot checks were explicitly run
  afterwards and passed. This is not a claim that the 70 skipped tests ran.
- Matching three-package Clippy with all targets and warnings denied passed.
  Workspace format, diff whitespace, doc-link checks and native release build
  passed.
- All ten native keyboard probe rows now match VICE, including both Return
  cases. The previous record's two reverse-scan mismatches are closed.
- 412 joystick state/display checks and 48 native captures still pass. Four
  deliberately broken held-Fire runs are rejected.

Reproduction from the source repo:

```sh
cargo test -p machine-commodore-c64 -p runtime-commodore-c64 -p mos-cia-6526
cargo clippy -p machine-commodore-c64 -p runtime-commodore-c64 -p mos-cia-6526 --all-targets -- -D warnings
cargo test -p machine-commodore-c64 --lib boots_kernal_to_ready_prompt -- --ignored
cargo test -p runtime-commodore-c64 --test boot_invariants real_kernal_reaches_ready_prompt -- --ignored
cargo build --release -p emu198x-c64
```

From the pinned sample's `commodore-64/patterns/assembly/input/joystick-reading`:

```sh
python3 verification/verify.py --emulator /path/to/emu198x/target/release/emu198x-c64 --output /path/to/new-evidence
```

The historical sample verifier permits the known reverse-scan difference and
prints an unconditional final message about it. Its final message is not the
result of this correction. The strict adjacent `check-record.py` additionally
requires all ten rows to match, requires the expected non-empty coverage and
rejects the old pinned sample record with exit 1. The new record passes:

```sh
python3 plans/2026-10-10-c64-reverse-keyboard-scan/check-record.py plans/2026-10-10-c64-reverse-keyboard-scan/native-results.json.gz
```

The local ignored hardware distillations under `knowledge/systems/` and
`knowledge/chips/` were updated to describe both directions and the remaining
matrix-model boundary. This plan preserves that boundary in version control.
