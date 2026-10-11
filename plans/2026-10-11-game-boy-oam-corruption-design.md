# Investigate DMG OAM corruption before extending the CPU/PPU stages

Issue #1728 has five failing original OAM singles plus a failing aggregate.
This step establishes a bounded signal-driven design. It does not authorize
new public CPU pins, persisted stage state, or a snapshot version change.

1. Reconsult the CPU bus-interface and SM83 granularity decisions and inspect
   `sharp-lr35902/src/{lib.rs,opcodes/arith.rs,opcodes/load.rs,opcodes/control.rs}`,
   `machine-nintendo-game-boy/src/lib.rs`, and
   `nintendo-game-boy-ppu/src/lib.rs` for existing address and OAM scan stages.
2. Diagnose the SameBoy standalone seventh-ROM nontermination using a read-only
   Core host trace. Preserve original bytes, reference code and exact run
   controls; do not count the successful aggregate as proof for that single.
3. Inspect original OAM test sources and reference corruption stages. Identify
   the actual externally visible event needed for INC/DEC, memory access and
   combined cases. Document timing uncertainty instead of extending precision
   without an observer.
4. Write alternatives, the recommended bounded stage extension, exact affected
   files, snapshot/API consequences and acceptance gates. Ask for agreement
   before implementing any change covered by the project's Ask First rules.

Reference evidence starts from SameBoy
`208ba4afabffab9edde416f2dbb8ae459e34adb8`; the unmodified original test corpus
is pinned in `test-data/game-boy-blargg-oam-interrupt.md`. The existing primary
observation record is
`198x/reference/by-topic/cpu-sm83/2026-blargg-oam-interrupt-observations.md`.

## Findings

The CPU-only guest executes `LD DE,$FE00; INC DE; DEC DE`. Both internal
cycles positively execute. After INC, DE is FE01 but addr remains 0103;
after DEC, DE is FE00 but addr remains 0104. The existing memory request,
read and write strobes are all low. There is no old-DE address event for the
machine to observe. The probe checks both cases actually execute; it is a
baseline observation, not a passing accuracy regression.

SameBoy `cycle_oam_bug` makes the pre-update register address visible before
changing it, including INC/DEC register pairs and stack/control paths.
`GB_trigger_oam_bug` and the read-specific path combine this with the PPU's
accessed OAM row. `display.c` advances that row during its existing sprite
scan. The read patterns also distinguish DMG, MGB and SGB2 revisions; these
must not silently collapse into one universal formula.

The current Emu198x PPU has a dot counter and per-dot execution, but no saved
accessed-OAM-row stage. The machine applies ordinary CPU reads/writes after
four PPU dots. This cannot be repaired by treating every inaccessible OAM
read/write as one generic event, or by decoding CPU opcodes in the machine.
The CPU must expose the increment/decrement unit's address activity alongside
its existing pins, and the PPU must expose its scan state at the relevant
phase. Exact sampling positions remain a reference-trace validation task.

### Standalone seventh-ROM fixture defect

The reference anomaly is explained by the original ROM's diagnostic writer,
not by a failed OAM CRC. The read-only trace catches the null terminator at
PC C3F4 writing C000 at frame 861, followed by a character store at PC C3FF.
That overwrites work-RAM code copied there at startup. The author's
`common/shell.s` text writer increments its A004-based pointer without a
BFFF bound. The verbose seventh test emits enough differences to reach code.

An intact control has no suppressed writes and remains running through frame
3,600. A separately labelled controlled-environment run suppresses only
out-of-range stores by those two reporting instructions: 4,675 suppressed
stores, original status 0 at frame 1,458. The original test instructions,
OAM operations and expected CRC are unchanged. This is diagnostic evidence,
**not an unmodified-ROM pass**. The original aggregate passes subtest 7 and
remains the unmodified oracle. Do not demand a terminating verbose single as
proof of faithful hardware, or hide its failure in a successful suite total.

The [evidence folder](2026-10-11-game-boy-oam-corruption-evidence/) retains the
seven original host/probe/log artifacts and SHA-256 manifest. Reference core
and external ROM identities are those in the previous corpus plan. The host's
optional `guard-report` argument enables only the clearly labelled control;
without it, the memory callback always permits the write.

## Approaches

1. **Extend the existing CPU pins and PPU scan stages — recommended.** Retain
   M-cycle CPU scheduling and the existing per-dot PPU loop. Make the missing
   address activity explicit, sample it against the PPU's actual row stage,
   and preserve it in snapshots. This fits the current signal-driven model.
2. **Replace the CPU's scheduler with a T-cycle machine.** A larger rewrite
   would affect every instruction, bus observer and save state. No current
   probe establishes that such a rewrite is necessary. The binding SM83
   decision rejects added precision without a concrete observer requiring it.

An opcode switch in `GameBoy::service_cpu` is not a third option: it would
reconstruct CPU activity outside the CPU instead of routing visible signals,
contrary to the bus-interface decision.

## Proposed bounded extension — awaiting approval

- Extend `Sm83`'s current pins with a retained optional IDU address for the
  scheduled M-cycle. It carries the **pre-update** address for INC/DEC and
  overlapping memory operations. Ordinary access pins remain intact; an
  internal address drive does not invent a read/write strobe. Clear/repopulate
  the latch through existing scheduling helpers so no stale event repeats.
- Extend the existing PPU scan stages with its current OAM row and the
  boundary states needed to distinguish idle, first-row, ordinary-row and
  scan-end behaviour. The current per-dot loop clocks these stages. CPU-side
  events sample them at reference-validated positions within the existing
  four-dot machine step; do not add a second clock or advance extra cycles.
- Apply corruption only through actual CPU/PPU interaction. Debug `peek`,
  disassembly, fixture observation and unrelated DMA reads must not mutate
  OAM. Keep read, write and overlapping IDU cases distinct and verify event
  counts; never apply the same write-like event twice by accident.
- Carry the existing DMG-family boot-profile selection into the OAM model
  where the reference proves variant-specific patterns. Preserve existing
  constructors as DMG defaults. Do not claim unidentified DMG0 differences
  match DMG-B merely because the current default suite passes.
- Save the CPU address latch and PPU row/model state. Advance the Game Boy
  runtime snapshot envelope **2 → 3**, rejecting version 2 explicitly; test
  resume through both an internal-IDU event and a memory/IDU overlap.
  Do not guess defaults for an in-flight old save.
- Retain `Sm83::tick()` as one M-cycle. The existing SM83 decision permits
  per-dot PPU work; this proposal does not replace it with a CPU T-cycle
  scheduler. If probes identify an unrepresentable intra-cycle event, stop
  and bring that evidence back before extending the agreed design.

### Exact affected paths

- `crates/sharp-lr35902/src/lib.rs`: output latch, initialization/reset and
  existing scheduling helpers; pin-level unit regressions.
- `crates/sharp-lr35902/src/opcodes/arith.rs`: INC/DEC register pairs.
- `crates/sharp-lr35902/src/opcodes/load.rs`: HL increment/decrement transfers.
- `crates/sharp-lr35902/src/opcodes/control.rs`: stack and control-flow IDU use.
  Inspect PC fetch/interrupt scheduling in the existing CPU execution modules
  before adding cases; record their exact phase with reference traces.
- `crates/nintendo-game-boy-ppu/src/lib.rs`: OAM scan row/model state and
  corruption application against the existing dot stages.
- `crates/machine-nintendo-game-boy/src/lib.rs`: route scheduled CPU address
  events through its native four-dot step and ordinary OAM accesses.
- `crates/machine-nintendo-game-boy/src/tests.rs`: timing, non-corruption and
  original guest regressions.
- `crates/runtime-nintendo-game-boy/src/snapshot.rs`: version 3 envelope and
  reject-old/resume tests.
- `crates/runtime-nintendo-game-boy/tests/phase2_verification.rs` and
  `test-data/game-boy-blargg-oam-interrupt.md`: retain all original scores;
  clearly separate the verbose seventh-ROM logging defect from hardware
  acceptance and from any separately identified derived test fixture.

## Implementation/verification order after approval

1. Add the pin-level failure against current code, covering INC/DEC before
   and after FE00/FEFF boundaries, both ordinary memory strobes and quiet
   internal cycles. Verify the failing observer measures old address rather
   than reading the already-updated register value.
2. Implement and compare the write-like IDU corruption and PPU scan boundary
   stages against reference traces. Run original singles 2, 4 and 5, plus
   non-causes/LCD-off/VBlank controls 1, 3 and 6. Keep instructions' cycle
   counts unchanged.
3. Add independently observed read/write/IDU-overlap cases for HL transfers,
   stack traffic and PC/interrupt activity. Verify complete OAM row contents,
   event counts and unaffected rows, not just a success flag. Cover supported
   revision differences with explicit reference configuration.
4. Run the original aggregate including its seventh subtest, all other seven
   standalone ROMs and the original seventh diagnostic. Preserve that last
   fixture's intact outcome; any bounded-output derivative must have a
   separate name, checksum and derivation record. Do not mark it as an intact
   pass. Keep CPU-instruction, memory-timing and mooneye gates green.
5. Verify snapshot rejection and resumed event/row equivalence at each new
   stage. Run affected crate tests, Clippy, formatting and required PR CI.
   Close #1728 only once every hardware acceptance item is evidenced and the
   original verbose-fixture limitation is explicitly accounted for.

Approval is required for the new persisted stages and snapshot 2 → 3, under
AGENTS.md's breaking data-schema rule. Investigation and the bounded-report
reference control are complete; no production pipeline has been changed.
