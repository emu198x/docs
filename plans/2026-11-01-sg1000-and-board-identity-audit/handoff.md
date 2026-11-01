# SG-1000 timing agreement pending

The reference audit is merged in umbrella PR #291 at c818b4e2; its tree exactly
matches original head 1d3102eb. The Oric manual and two SG-II photos are retained
privately with verified hashes. No temporary reference worktree remains.

Draft source PR #2222 has three pushed commits ending fc3b716598cb0f706d02a9f8b548f17a692e8e1a:
Oric/5200 descriptions, SG console/early-II scope and immutable original v5
continuations, then the missing existing II profile in launch help. Existing
related local suites pass 101 tests, with one external SG cart check ignored.
Strict lint and registry/fixture/ignore guards pass. Metadata CI is run
41311120382; read its actual conclusion when resuming. It does not contain the
staged future regression and cannot establish that #2223 is fixed.

The original PAL rate probe is restored as an ACTIVE STAGED SOURCE TEST:
crates/runtime-sega-sg-1000/tests/clock_agreement.rs. It fails with
“Sg1000Pal: 49254 audio frames disagree with 48804 frames of declared elapsed time”.
Do not merge around this known defect. Keep the source PR draft until the
approved implementation makes this test green. Do not commit the red-only
increment: the agreed coding cadence requires a green self-contained fix.
The reproduction source, red logs and hashes are also retained in this docs PR.

The pending async question proposes independent nominal PAL CPU/PSG and VDP
oscillators (3,580,000 Hz and 10,738,635 Hz / 2), v6 writes, exact v5 NTSC/early-II
reading and v5 PAL rejection. No reply has arrived and no timing/schema
production change is written. After agreement, correct and test the oscillators
before the fixed-owner split, preserving original fixtures. Qualify the early
II configuration without pretending to cover later TMS9118/custom-chip boards.
All tasks and explicit source/physical-qualification gaps are in the plan.

Durable worktrees retained for the pending implementation and its evidence:
- /Users/stevehill/Projects/198x/Emu198x/.worktrees/sg1000-source (staged red test)
- /Users/stevehill/Projects/198x/Emu198x/.worktrees/sg1000-docs (plan and receipts)
Remove them after the approved green work is committed, pushed, verified and
merged. Temporary target/capture/render/cache directories can be removed now.

#2144 now names the three actual 5200 board targets, the Oric memory/revision
scope and the SG clock prerequisite. #2223 tracks the measured clock defect.
Primary checkouts and unrelated locked worktrees remain untouched.
