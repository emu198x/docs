# Atari 5200 and Oric board audit

Lane: engineering-frontier work, following fixed machine ownership (#2144).

## Scope and order

1. Reproduce Atari 5200 #421 on current source main before extracting its
   CA018087, CA020108 and CA021374 boards. The retained October investigation
   already identifies port loss, direct keypad injection and missing upper
   fire. Do not claim the three boards work by copying this incomplete path.
2. Correct the 5200 input path and shared physical POKEY scanner only after
   the snapshot policy below is approved. Preserve existing analogue scale
   and unrelated audio/timer behaviour. Keep 800XL's existing injected
   keyboard path until its separate matrix correction.
3. Reinspect the Oric manufacturer manual for physical PCB and circuit
   revisions, including changes that affect emulation. Do not equate the
   Oric-1 and Atmos product names with distinct PCBs without evidence.
4. Select concrete board owners only after their wiring is established.
   Preserve profile aliases where their board mapping is known. Record
   unresolved mappings explicitly rather than fabricate qualification.

## Controller correction design

The detailed design and executable reference evidence are in
[the October plan](2026-10-11-atari5200-controller-wiring.md). This continuation
updates paths and version reservations against source main `d57ba23fa`.

- `crates/emu198x-atari-pokey/src/lib.rs`: optional physical KR1/KR2 scan
  stage, six-bit address/compare, four-state detector, retained modifiers,
  Break edge and /114 divider phase. Save complete state; audit the chip's
  separate `save_state`/`load_state` surface too. The chip knows neither
  controller selection nor 5200 key names.
- `crates/emu198x-atari-gtia/src/lib.rs`: read the existing CONSOL latch;
  no new GTIA saved field.
- `crates/machine-atari-5200/src/lib.rs`: four physical held key matrices,
  upper-fire lines and raw pots. Derive selected keyboard returns and common
  pot supply from CONSOL. Preserve ghost paths for simultaneous switches.
- `crates/runtime-atari-5200/src/{input,runtime,snapshot}.rs`: route ports
  1–4, preserve primary alias 0, ignore invalid ports, hold independent keys,
  map fire2, save all four directional/axis caches and restore atomically.
- `crates/runtime-atari-{800xl,7800}/src/snapshot.rs`: version shared chip
  layout changes before decoding positional payloads.

Current versions are 5200 **19**, 800XL **21**, 7800 **6**. Proposed writers:
**20**, **22**, **7**, respectively. Reject earlier layouts before decoding;
missing scanner phase and unsaved host-cache history cannot be recovered
exactly. Recheck reservations before implementation and merge. This is a
schema change requiring approval; it is not implied by the split approval.

## Verification

- Run the original guest probe on current main and retain complete captures
  and advancing execution markers. Compare with the frozen baseline rather
  than assuming its old failure count remains current.
- Run unchanged reference scanner, ghost-network and scheduled-transition
  sweeps; retain their negative controls.
- Test every port/selector, both fires, all keys, scan enable/debounce,
  select/release transitions and opposing held directions.
- Compare uninterrupted and restored execution between scan edges, including
  IRQs, KBCODE/SKSTAT, pots, subsequent input events and snapshot bytes.
- Assert earlier versions reject without changing live machine or caches.
- Run POKEY, GTIA and all three affected Atari families' focused tests and
  Clippy; run real firmware/cartridge checks with verified assets where
  available. Read CI results before merging a tested tree.
- For Oric, cite exact manual pages and distinguish physical PCB revision
  from electrical circuit revision. Preserve primary provenance and hashes.

## Workspaces and cleanup

Task source and docs worktrees are `Emu198x/.worktrees/board-audit-source`
and `Emu198x/.worktrees/board-audit-docs`. The old locked Atari investigation
registration has no directory and contains no production correction; retain
it until its evidence and branch have been explicitly reconciled. Preserve
all unrelated primary-checkout work. Remove task worktrees and caches after
verified retention on the remote, or state precisely why they remain.

## Approved controller correction and adjacent restore defect

Steve approved the physical scanner and writers 20/22/7 on 2026-11-02.
Source correction is PR #2239, commit `172835c59`. The current-main guest
reproduced all 222 known failures; the corrected 420-case guest passes.
The frozen scanner, full ghost-network and scan-phase restore checks pass.

A reset check then exposed an older independent defect: restoring a live
5200 into a blank runtime installs the machine but leaves `cart_bytes` and
`bios_bytes` empty. Queries report no media, and reset discards the machine.
Those restore/reset paths are unchanged from the original main. Correct this
before board extraction as a separate commit:

- Add read-only cartridge/BIOS byte accessors and a constructor accepting an
  already validated `Cartridge` in `machine-atari-5200`.
- In runtime `set_machine`, derive media caches and the positive cartridge
  layout from the restored machine. Use that explicit layout when rebuilding;
  rediscovering it from a headerless byte copy would lose type-6 evidence.
- New cartridge insertion clears the cached layout and detects it afresh.
- No additional saved field or version: all media and layout already live in
  the versioned machine payload. The runtime cache is derived on restore.
- Prove the defect with a failing public-runtime test, then cover reset,
  firmware replacement and cartridge replacement for linear, two-chip and
  banked images. Re-run the 5200 tests and Clippy before a separate PR.

## CI verification blocker

The original #2240 Linux Test job failed before it could finish or upload its ledger.
GitHub's check annotation reports `System.IO.IOException: No space left on
device` while writing the runner's own diagnostic log. Keep the failure
annotation with the evidence; this is not a test assertion failure.

Bound this job's artifacts in source `.github/workflows/ci.yml`: set
`CARGO_INCREMENTAL=0`, `CARGO_PROFILE_DEV_DEBUG=0` and
`CARGO_PROFILE_TEST_DEBUG=0` at job scope, and give the test cache a new
shared key. Add `df` before/after cache restore and an always-run disk reading
so a subsequent failure has capacity evidence. Do not change test selection,
collector, doctests or their failure semantics. Verify workflow lint, then
require an executed complete ledger before merging either correction.


The media fix is now #2241 (`0d380944e`), replacing #2240 with the same
verified tree on a linear branch. No history was force-pushed. The closed
superseded PR retains its head; its remaining CI run was cancelled.

The pristine original source worktree was verified clean and its commit
verified on remote main before removal. Oric audit #294 merged as
`db20637ae7555a895aab5f4f845d1cc69ac90eb9`; its clean worktree was removed
after checking the exact original head in remote `refs/pull/294/head`.

Documentation completion updates `systems/atari/5200.md` only for the corrected
controller paths, snapshot writer and unresolved board owners. It also adds
the manufacturer-backed board-identity boundary to `systems/oric/atmos.md`.
Other historical accuracy claims in these pages are outside this correction.
Commit current-behaviour wording only after the source changes merge.


Scanner correction #2239 merged as `4a253729351e010c4a1846f96c6e37d5ba1b7d57`.
Its complete CI ledger records 8,573 passes, zero failures, 713 ignored and
110 skipped tests. The test run executed 1,155 binaries and finished with
78 GB free after the cold build. Mac/Windows, Apple hosts, browser parity,
Clippy, format, registry, firmware and remaining checks passed.

For the board-extraction follow-up, CI timed the exhaustive controller guest
binary at 324.8 seconds and the POKEY scan binary at 42.7 seconds. Preserve
all cases. Benchmark the eventual common engine's optimized test codegen
against exact captures before choosing any package-level optimization; do
not infer a fleet-wide speedup from one timing.


The media PR's parent merged by rebase, so its old base was no longer an
ancestor of main. Preserve `0d380944e` in the verified remote tag
`evidence/atari5200-media-before-parent-rebase`, then rebase only the private
task branch using an exact lease. Current head `701667175` has the identical
final tree `1107a75b0078ff70489b365c0b003c90de5191d4`; shared main history was
not rewritten. Its new CI checks are pending. The old full ledger records
8,574 passes and zero failures; the Mac build never acquired a runner.

For future batches in this rebase-only repository, merge the parent before
opening a dependent fix PR. That avoids duplicate histories and repeated CI
when the parent receives new commit IDs on merge.


The fresh suite on `701667175` passed 8,574 tests with zero failures. The
only unavailable hosted gate was macOS runner acquisition. Inspecting the
workflow showed its validation is exactly `cargo check --workspace
--all-targets`. That full check passed locally on native ARM64, pinned Rust
1.99.0, with the same clean source tree. Retain its log and the complete
hosted-check snapshot as the fresh Mac validation; do not report the queued
hosted job as a passing run. No test was disabled, no check status overridden,
and shared history or protection rules were not changed.
