# Fix CPU-visible final-scanline LY (#2182)

Lane: engineering-frontier. User approved the narrow CPU-visible LY correction
on 2026-11-05; qualify LYC/STAT separately. The retained diagnosis identifies
Kirby's first LY read and proves three exact reference matches when it reads
zero late in internal line 153.

1. In isolated worktree `/private/tmp/198x-kirby-ly-fix`, qualify the early LY
   reset boundary using pinned SameBoy and GateBoy plus primary research.
   Record provenance and limits in the shared reference library before
   introducing a hardware timing claim into production comments.
2. Add boundary/clock invariants to
   `crates/emu198x-nintendo-game-boy-ppu/src/tests.rs` and the independent
   Kirby case to `test-data/game-boy/commercial-screens/expected.json` and
   `crates/runtime-nintendo-game-boy/tests/commercial_screens.rs`. Run red.
3. Change only CPU-visible LY in the PPU's `src/lib.rs`; preserve internal
   scanline, frame timing, and existing LYC/STAT behaviour. Add independent
   boundary, LCD-off and colour-mode scope tests. No dependencies or save
   schema change. Update the commercial-screens README to describe all cases.
4. Run PPU/common/runtime/board tests and explicitly enabled commercial
   fixtures, strict Clippy and format. Preserve frozen snapshot specimens.
   Verify the exact Kirby hashes against the independently retained reference.
5. Commit/push source, create a focused PR, follow CI and merge the verified
   head. Record merged outcome and remove task worktree/caches/processes.

Task-owned temporary paths: `/private/tmp/198x-kirby-ly-fix`,
`/private/tmp/198x-kirby-ly-target`, `/private/tmp/198x-kirby-ly-evidence`.
Preserve unrelated worktrees, `tools/__pycache__/`, the ZIP draft and umbrella
asset/Amiga work. Archives named by rule 25 were checked during diagnosis and
are absent; this fix is new code against the current PPU, not an archive port.

## Verified implementation

Source PR #2304 at `18720ec98ed27ed8de10fb47a9df5421e788d2cc`. The independent
reference interval probe confirms four readable-153 dots followed by zero
while mode 1 continues. Both the new boundary and Kirby tests fail before the
fix (exit 101). After it: 29 PPU tests, 183 family tests (27 fixture-ignored),
all 3 explicitly enabled commercial tests, Clippy and formatting pass.
33 frozen specimens and the original two game expectations are unchanged.
Pinned SameBoy source identities rechecked. Evidence is in the adjacent
`2026-11-05-kirby-ly-fix/` folder. Shared reference note is pushed at umbrella
commit `588b4fe4`. Hosted PR checks are running.
