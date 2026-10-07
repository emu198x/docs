# Preserve and integrate the Amiga accuracy campaign

Lane: best-in-class campaign. The user explicitly authorised committing,
reconciling, pushing and merging the completed work, with preservation first.

1. Archive all tracked modifications and untracked files in the umbrella,
   emulator and docs repos. Preserve index/worktree patches, original HEADs,
   file modes and content hashes. Verify archives before integration.
2. Fetch current remote heads and inspect overlap. Create isolated integration
   worktrees; leave the existing dirty checkouts intact.
3. Separate the approved signal-display and Amiga/68020 accuracy changes from
   unrelated work. Commit coherent dependency groups with normal hooks.
   Record any inseparable pipeline changes explicitly rather than fabricating
   intermediate states that never passed verification.
4. Reconcile each group with current main, preserving both upstream fixes and
   campaign behaviour. Run relevant tests, release build, formatting/Clippy,
   archived negative/positive comparisons and both Amiga video gates.
5. Push reviewable branches, open PRs, inspect required checks and merge when
   they pass. Do not bypass branch protections or failed checks.
6. Verify remote ancestry and final repository status; report commits/PRs and
   exactly what remains local. Preserve recovery archives and original trees.
