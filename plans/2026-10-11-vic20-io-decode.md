# Correct VIC-20 overlapping I/O selection

Engineering-frontier work discovered while investigating open bus issue 1678.
The existing address match recognises only the two canonical VIA blocks and
excludes simultaneous selection. VICE's `vic20.c` routes A4/A5-selected VIAs
through the entire $9000-$93FF I/O block, including the VIC's $9000 page.
Commodore schematic 324001 sheet 2 connects those VIA selects to CA4/CA5 and
their shared active-low select to I/O0. This is a bounded decoder correction
using existing state; no dependency, public API or snapshot layout change.

1. Record the inspected primary schematic and the distinction between chip
   selection and VICE's AND convention for simultaneous reads in the umbrella
   reference library.
2. Add regressions in `machine-commodore-vic-20/src/lib.rs`: all 64 I/O
   sub-blocks using register C for writes and peeks, simultaneous selection, CPU reads that
   acknowledge both selected timer interrupts, and non-destructive debugger
   peeks. Run them before editing the decoder and retain the failing output.
3. Correct CPU reads, debugger reads and writes in that same file. Selected
   reads combine like VICE; writes reach every selected chip. Undecoded I/O
   continues to use the existing value until actual CPU/VIC bus retention is
   implemented under issue 1678.
4. Run machine/chip/runtime tests, formatting and Clippy. Verify the actual
   CPU guest result and timer flags, then commit and merge after required CI.
   Update issue 1678 with the bounded result without claiming open bus fixed.

Reference code stays immutable. Use the Rust skill. Read the existing chip
implementations for side effects; do not advance clocks inside accessors.

## Result

Source commit `6df603ba` corrects the existing decoder in all three access
paths. No state field, API or snapshot version changes. A4 and A5 select the
VIAs throughout I/O0, including overlaps in $9000-$90FF. Simultaneous reads
use VICE's AND convention; every selected VIA receives its read side effects.

Both new tests fail before the correction at the first overlap: `$901C`
returns 243 ($F3, VIC alone) instead of 195 ($C3, VIC AND VIA1). They now pass
128 cases each: all 64 sub-blocks in both regions. The direct test checks
combined data and writes to every selected chip. The CPU guest reads the
combined register value, acknowledges selected Timer-1 flags and stores both
VIA flags into RAM. It must reach a completion marker. Debugger peeks are
checked separately and must leave both initially asserted flags untouched.

Verification passes:

- 99 ordinary machine, VIC-I, VIA and runtime tests.
- Eight explicitly enabled ROM tests: boot/banner, keyboard execution,
  joystick, cartridge cold start, debugger and expanded BASIC loading/run.
- The 29-case VICE raster survey retains every pre-existing exact match count.
  Some survey cases have known pixel differences; this is a no-regression
  result, not a new claim of full VIC-I accuracy.
- Machine/runtime Clippy with `-D warnings`, formatting and diff hygiene.

The adjacent logs retain the red regressions and completed validation.
Primary selection evidence is recorded in the umbrella's
`reference/by-system/commodore-vic20/vic20-io-selection.md` (commit `3a8ecf48`).
The [Commodore technical manual](https://www.w3afc.com/uploads/1/3/2/2/132249121/vic-20_the_friendly_computer_technical_manual__pn_990440___2_.pdf)
supplies the chip-select wiring. VICE `src/vic20/vic20.c` functions
`vic_via1_via2_*` and `via1_via2_*` supply the digital read-resolution precedent.
The schematic alone does not qualify analogue bus-conflict behaviour.

Issue 1678 remains open: $9100/$9200 still need real CPU/VIC bus retention.
The current VIC renderer's per-pixel memory callbacks do not represent the
physical fetch stages, so treating their last callback as open bus would not
be an accurate continuation of this fix.
