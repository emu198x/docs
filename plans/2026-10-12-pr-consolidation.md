# Merge the outstanding accuracy work

The user requested that authored draft and unmerged PRs be brought into main.
This task consolidates completed evidence and implementation without presenting
unfinished hardware work as verified.

1. Inventory open PRs in `emu198x/docs` and `emu198x/emu198x`; retain exact heads,
   changed files, merge state, body and checks. Inspect each documentation
   proposal's evidence and scope. Draft status alone is not a reason to leave
   a completed investigation unmerged.
2. For docs PRs #55, #75, #89, #92, #99, #104, #106, #110, #114, #117, #119,
   #124, #125 and #129, verify captured evidence, checksums and any included
   verifiers/negative controls. Preserve explicit unresolved questions and
   implementation gates. Check #4 separately against the WASM sequencing
   decision. Update stale present-tense process claims where needed.
3. Mark reviewed docs PRs ready, rebase-merge against the reviewed head, and
   verify each returned merge commit is in remote main. Record outcomes here.
4. Review source PR #1704 against its unresolved NMI/POKEY gates and the local
   uncommitted follow-up. Do not merge the known intermediate snapshot layout.
   Review source #1282's conflict and peripheral semantics, resolving and
   testing in an isolated worktree if within the approved design.
5. Review the generated release PR #1685 and its actual CI evidence before
   merging; merging publishes the suite release through the existing workflow.
   Dependency bot PRs are separate from the authored accuracy changes.
6. Report exact merges and remaining blockers. Remove clean completed review
   worktrees only after merge readback; retain all active work and branches.

The PET source prototype and three new failing discrete-board regressions
remain preserved in `fix/pet-crtc-ports`. The user approved proceeding with its
staged board/firmware correction before requesting this consolidation.

## Verified results

All 15 previously open documentation PRs are merged. Each merge commit is an
ancestor of remote main, and every changed file blob matches the reviewed head.
The archived September browser plan is explicitly superseded; pending hardware
designs remain proposals unless their own approval is recorded.

| PR | Merge commit |
|---|---|
| [#55](https://github.com/emu198x/docs/pull/55) | `116067a48e59a60d6c7eef0e21e7e4268147b8ef` |
| [#75](https://github.com/emu198x/docs/pull/75) | `52f67fb1fe4c89d0a0d9995607be92647689ff2f` |
| [#89](https://github.com/emu198x/docs/pull/89) | `5c522f7aa5f5643a8a4ebda99c20b47785f69dcd` |
| [#92](https://github.com/emu198x/docs/pull/92) | `90cb3240314740f2f49ea7a9d83f2356f9db93bd` |
| [#99](https://github.com/emu198x/docs/pull/99) | `26a74483f48f92c0840bae859b7c3228d6372fa6` |
| [#104](https://github.com/emu198x/docs/pull/104) | `fb31b2a4c394b3b89f53e14b055b321c0c11495f` |
| [#106](https://github.com/emu198x/docs/pull/106) | `8748176ccf276555bd3cdbfd144416259c55c6fc` |
| [#110](https://github.com/emu198x/docs/pull/110) | `784f5e5e1cd294a9d0667679243911400af2dcc6` |
| [#114](https://github.com/emu198x/docs/pull/114) | `961110de018eb791050ac5cb2d265ede690c0349` |
| [#117](https://github.com/emu198x/docs/pull/117) | `2730f6c80dba134e38763db34634d90997edc5e1` |
| [#119](https://github.com/emu198x/docs/pull/119) | `282c9f1c6f76a089017757c8a19d4097618ad86e` |
| [#124](https://github.com/emu198x/docs/pull/124) | `2ece37639b38a13d3d57dbe09aa08e9b4ed0d190` |
| [#125](https://github.com/emu198x/docs/pull/125) | `48fd52f0bdedb671e7af063a775a8b8d23f60d33` |
| [#129](https://github.com/emu198x/docs/pull/129) | `8f4182a1b15e6b558980f14ee7d68e713b5db161` |
| [#4](https://github.com/emu198x/docs/pull/4) | `5e2f3c2adcc1113d0122220c94080caba150fe8e` |

Evidence checks included 172 C64 comparator tests and eight complete capture
verifiers; all 96,800 MC6809 indexed cases and nine comparator tests; PET port
and wiring captures with negative controls; Atari 5200 controller matrices;
PSG noise and strobe captures; the NES mapper matrices; all 64 Sega VDP timing
results against their RAM captures; SG-1000 intervals; and recorded artifact
hashes. Passing a verifier confirms the reported failures and controls; it does
not mean the proposed hardware fixes are implemented.

Source [#1685](https://github.com/emu198x/emu198x/pull/1685) merged as
`55b48c921a55c5e0f30d25e27796f9b9cf64e8ce`. Its exact-head CI ledger contains
7,808 passed tests, zero failures, 687 ignored tests (96 without a stated reason)
and 96 fixture skips across 234 packages. Its release checks passed before
merge; the existing publishing workflow subsequently started for v0.31.1.

Source [#1704](https://github.com/emu198x/emu198x/pull/1704) remains draft.
The physical NMI assertion and width, consecutive one-line DLI delivery,
POKEY chip-clock versus host-sample separation, and actual timing-ROM acceptance
are still unresolved. Green CI does not settle these gates. The local POKEY
and Atari 7800 follow-up is preserved, as is the approved PET correction.

Four clean completed documentation worktrees were removed after confirming
merged content, main ancestry and absence of untracked or ignored files.
Branches were retained. Active source investigations remain intact.

Source [#1282](https://github.com/emu198x/emu198x/pull/1282) was rebased onto
v0.31.1 in an isolated worktree. Its only conflict was the crate changelog;
both entries are retained. The machine and three affected runtimes pass 86
tests, with one ROM-dependent boot test ignored. All-target Clippy and workspace
formatting pass. Disabling the UART read route fails the targeted regression;
restoring it passes. The reviewed head is
`0b033608c72bcfd0095566e70e563894f64d1df6`. Fresh CI completed successfully:
7,810 passed, zero failed, 687 ignored and 96 fixture skips across 234 packages.
The 96 ignored tests without a stated reason remain unchanged from the release
baseline. All platform builds, Linux package exercises, firmware and browser
checks passed. It merged as `9790f2437f6a1dd16d5f004233f51fe79d444740`.

This sweep covers Emu198x source and documentation. Open PRs in other family
projects and unrelated organisations were inventoried but are separate work.
The two Emu198x dependency-bot PRs are also outside this authored-work sweep.
