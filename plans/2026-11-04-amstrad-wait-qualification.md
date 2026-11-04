# Retain Amstrad physical WAIT qualification

The source change is [emu198x#2285](https://github.com/emu198x/emu198x/pull/2285),
with the original catalogue investigation remaining in
[#2265](https://github.com/emu198x/emu198x/issues/2265). The user approved Z80 0.9
for explicit Spectrum adoption, with CPC held on 0.8 for
[#2284](https://github.com/emu198x/emu198x/issues/2284). Preserve all existing
catalogue expectations until changed waypoints are explained and qualified.

1. Retain the completed 103-entry registry-only recapture in
   `plans/2026-11-04-amstrad-wait-evidence/`: per-entry expected/observed hashes,
   input and binary identities, bounded capture helper, and a readable summary.
   Assert exactly 103 distinct cases, complete frame/audio results, and zero
   capture errors. Record mismatches explicitly; they are not successful oracle
   comparisons. Prove that binary, manifest and source inputs remain unchanged.
2. Retain the physical clock/WAIT, v20 legacy-rejection, whole-state continuation
   and strict real-input stream evidence. Link the published CPU/chip releases.
   Include only our source, hashes, results and clearly attributed diagnostic
   captures; never ROMs, disks, private manuals or captured executable bytes.
3. Keep reference limits explicit. Nine MAME capture sets do not establish nine
   successful boots: six show recognizable content, three remain striped, and
   Rainbow Islands' unchanged 45-track image is refused by the reference's
   configured 42-track drive. The independently observed Cybernoid fast-loader
   stream is a byte oracle; the differently timed screenshots are not pixel
   oracles.
4. Validate JSON coverage/identities, all local Markdown links and screenshot
   provenance. Run applicable repository checks, review the exact diff, commit
   and push, then use normal PR checks and merge. Update #2265 with the result
   and leave unresolved oracle qualification open.
5. This task uses `/private/tmp/198x-amstrad-wait-evidence`, an isolated linked
   docs worktree. The parent checkout's unrelated ZIP plan stays untouched.
   Remove the task worktree after its commits are verified remotely and any
   unique files are retained. The emulator task owns its separate source,
   capture processes, cache and private recovery archive.
