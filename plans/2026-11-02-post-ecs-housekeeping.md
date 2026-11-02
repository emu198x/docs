# Post-ECS housekeeping

Engineering-frontier maintenance approved after the A500+/A600 split. Preserve
primary checkout edits and active Pentagon/CRTC workspaces.

1. Audit current source/docs/site status, worktree registrations and process
   ownership. Identify missing paths separately from finished tasks. Record
   commit retention and verify recovery before removing any registration.
2. In source `crates/common-commodore-amiga/src/lib.rs`, replace the obsolete
   per-chipset machine-crate description with current shared wiring/owners.
   In `crates/common-commodore-amiga-aga/src/agnus.rs`, correct the ECS mirror
   path. In `crates/runtime-commodore-amiga/src/snapshot.rs`, document v67 and
   its explicit v66 RTC-presence migration. Comments only; verify the Rust
   token stream is unchanged, formatting and document links pass, and paths exist.
3. Verify remote evidence tag `evidence/a1200-fixed-owners-2026-11-01` retains
   the complete leftover A1200 branch before removing that branch.
4. Audit missing worktrees individually: inspect metadata, reflogs, retained
   commits, merged PRs and active processes. Preserve recovery remotely where
   needed. Remove only confirmed finished registrations, via Git. Leave
   unknown or active registrations locked and untouched.
5. Inspect tracked/untracked/ignored state and processes before clearing only
   finished generated caches. Keep firmware, fixtures and active build targets.
   Measure disk change with `df`; report concurrent activity rather than
   attributing every change to this cleanup.
6. Push verified source comments and durable plan/audit receipts. Remove this
   task's worktrees, generated caches and background processes after verifying
   remote retention. No dependency, API, snapshot or hardware behaviour changes.


## Audit results

The three source comments are corrected in source PR #2233. Every non-comment
line matches the base; a changed-version negative control fails. Formatting
and doc-link/self-test checks pass. Runtime behaviour and save bytes are unchanged.
The A1200 local branch was removed after verifying its exact tip in its remote
evidence tag.

Two absent, unlocked worktrees from merged PRs were removed individually through
Git. The detached source worktree had 24 intermediate reflog commits with no
retaining ref; a verified local recovery bundle preserves them plus its final
head. The original site PR commit was rebased, so a second verified local bundle
preserves that exact history. Bundles and original reflogs remain under each
primary repo's `.git/recovery/2026-11-02-worktree-audit/`; keep them until the
preserved histories are reviewed or retained elsewhere. Audit JSON records paths
and hashes. Unrelated intermediate work was not published.

The missing Atari/PET registrations remain locked: their own evidence records
describe unfinished hardware investigations. #421 remains open. Active
Pentagon/CRTC worktrees and the existing tilemap workspace are untouched.

Five generated, ignored caches were removed after checking their markers,
tracked/untracked source status, newest file writes and open-file ownership:
the spectrum-composite tool target, old Emu198x site dependencies/build, and
cold Build198x/Format198x targets. Source status stayed unchanged in every
owner. `df` measured 2,264,000 KiB (about 2.16 GiB) more available over this
removal, reaching about 4.23 GiB. Other sessions were allocating space during
the audit, so this is the measured interval rather than an exclusive attribution.
