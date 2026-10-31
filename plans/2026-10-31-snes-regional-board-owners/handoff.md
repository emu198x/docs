# SNES split: schema decision pending

The asynchronous question requests approval to write complete v2 envelopes,
retain a cartridge-bearing v1 reader and reject blank v1 states whose omitted
firmware cannot be recovered. No v2 production code has been written.

Source branch `refactor/snes-fixed-board-owners` starts at 7b7128fa3. Commit
94ecede00 contains the first green cache fixes and six original v1 fixtures.
The extraction and further fixes are staged in the source worktree. Do not
publish or merge them as complete: `a_blank_save_retains_firmware_for_a_later_cartridge`
correctly remains red pending the schema decision. Other original tests passed
before that probe; owner tests (7 each), the six original progressive/interlaced
continuations, SRAM region-switch regression, strict Clippy/rustdoc and registry/
fixture/ignore guards pass. Current branch registry: 89 machines, 34 binaries.

The temporary capture export generated three project-written cartridges;
no original SNES software was found in the configured ROM workspaces. There
is no new historical-software qualification or public boot capture. The pinned
player catalogue has no SNES module; regional pages must omit a player.

Durable worktrees:
- `/Users/stevehill/Projects/198x/Emu198x/.worktrees/snes-source`
- `/Users/stevehill/Projects/198x/Emu198x/.worktrees/snes-docs`
- `/Users/stevehill/Projects/198x/Emu198x/.worktrees/snes-site`

The site branch has only two strict board mappings, a legacy redirect and route
expectations/test additions. It has not been built or published. Docs PR #169
holds the plan and red evidence. Umbrella PR #289 is merged at a3eca5a8; the
OpenSFC primary record establishes shared NTSC-U/J motherboard scope. The
reference-only worktree was removed after remote retention was verified.

On approval: implement v2 independently stored IPL with atomic validation,
read loaded v1 states using their embedded IPL, and keep the original v1 fixture
bytes immutable. The baseline can use a test-only legacy encoder to compare
all original fields and outputs; separately check all v2 metadata and blank/
loaded firmware cases. Do not regenerate the six original captures. Then run
full source checks/CI, finish docs/site/live verification, update #2144, and
remove these worktrees after verified remote retention.

Primary checkouts and unrelated locked worktree records remain untouched. The
umbrella checkout stays on `model/spectrum-solidcraft`; do not move it to main.
Use absolute umbrella paths for primary references from these linked worktrees.
