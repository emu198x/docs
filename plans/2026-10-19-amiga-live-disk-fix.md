# Preserve live Amiga disk-change notifications (#1877)

Lane: Amiga best-in-class campaign. The user approved the bounded runtime
policy fix after the native investigation in PR #136.

1. Add a failing regression in `crates/runtime-commodore-amiga/tests/` covering
   startup, live replacement, insertion after eject, reset and snapshot restore
   through OCS/ECS/AGA runtime dispatch, including A1000 startup behavior.
   Check the actual drive latch and CIA input, not just a successful tool call.
2. In `runtime-commodore-amiga/src/runtime.rs`, separate reset mount policy
   from live loading. Preserve pre-execution startup behavior and notify changes
   once runtime time has advanced. Leave drive hardware and reattachment alone.
3. Run the new test red before the fix; run runtime, floppy and headless-tool
   regression suites green afterward. Run formatting and focused Clippy.
4. Build the headless native binary with locked offline dependencies. Repeat
   generic `load_media` Save from the retained requester, validate filesystem
   and actual program presence, then independently cold boot, Load, return
   the requested system disk, run, roll and bank. Preserve original input hashes.
5. Retain sanitized commands, output hashes and captures with the investigation
   evidence; update #1877 and PR #136. Push the source fix in a separate PR.
   No merge is authorized in this turn.
6. Verify remote commit retention and remove task worktrees/build caches.
   Private licensed repro stays under umbrella output/bank-or-risk-playtest
   until the fix and regression evidence are accepted; leave active user apps.

Workspaces: `/private/tmp/198x-amiga-disk-fix` (source),
`/private/tmp/198x-amiga-save-docs` (docs). Build cache:
`/private/tmp/198x-amiga-disk-build`. No new dependencies or APIs planned.

## Verified outcome

Implemented at `6ff929f366e8762d5d5b9dadf53367b2cc692821`. The new live-mount
tests failed before the fix. All 269 selected correctness tests pass; the one
existing ignored test is an explicit wall-clock benchmark. Clippy, formatting
and the locked offline native build pass. Native Save, cold boot, Load, syntax
check, run, roll and bank pass with generic `load_media` throughout.

The [fix evidence](2026-10-19-amiga-native-save-investigation/fix/README.md)
binds source/binary identity, commands, captures and actual persisted bytes.
Original ROM/media hashes are unchanged. The active user game is untouched.
