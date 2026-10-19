# Verify generic Amiga disk changes and native persistence

The approved fix at `6ff929f366e8762d5d5b9dadf53367b2cc692821` restores live
`load_media` notifications without changing startup, reset or snapshot policy.
The previously failing generic route now saves, cold-loads and runs Bank or Risk.

## Fix and regression tests

`insert_floppy_bytes` accepts the caller's mount policy. Reset explicitly
uses the original firmware startup policy. `load_media` leaves change pending
when runtime time is nonzero, including instruction stepping before the first
video frame. Pre-execution startup remains unchanged; A1000 startup continues
to leave change pending. Snapshot reattachment is unchanged.

The new `disk_change` tests cover drive state and the CIA-A /DSKCHANGE input
on eight PAL/NTSC models spanning OCS, ECS, AGA and A1000. They cover live
replacement, insertion after eject, startup/reset, pending-change restore and
acknowledged-change restore. Two live-mount tests failed before the fix;
all four now pass. The other suites verify existing runtime/drive behavior.

| Check | Passed | Failed | Ignored |
| --- | ---: | ---: | ---: |
| Runtime library, lifecycle, disk-change, snapshot | 183 | 0 | 1 |
| Floppy peripheral | 52 | 0 | 0 |
| Headless Amiga/MCP | 34 | 0 | 0 |

The single existing ignore is an explicit wall-clock benchmark, not a
correctness gate. Focused Clippy with warnings denied, workspace formatting,
and the locked offline native build pass. Logs retain commands' output.

## Native outcome

The pinned stock PAL A1200 and lawful runtime/ROM inputs are the same as the
[original investigation](../README.md). Every insertion in this replay uses
**generic `load_media`**; none uses the Amiga-specific `insert_media` escape.
The immediate export still equals the unmodified blank disk. The pending
signal becomes visible before execution and is acknowledged by guest stepping.

Native Save writes a valid OFS filesystem containing `finish.amos`, 17,734
bytes. Both `verify` and `manifest` succeed. Reading through the OFS linked
blocks and the logical pointer ranges yields the same program. The file and
whole saved disk equal the previous successful explicit-notification control.
`storage-checks.json` retains their identities.

An independently cold-booted editor loads that file from the saved disk and
F2 reports no errors. F1 requests the system volume for runtime/font access;
returning it through `load_media` allows the styled title to appear. SPACE,
R and B then roll six and bank six points in round one. Every retained native
capture is byte-identical to its earlier successful control, including the
expected system-volume request. This is persistence and basic execution
verification, not a learner trial or a general Amiga accuracy claim.

## Reproduction and provenance

`build.json` binds the tested native binary to the source revision and build
command. Rebuilding after the final source comment change produced the exact
same executable hash. The public source fix is separate from this docs PR.
No dependencies or public APIs changed.

`requests/` retains exact JSON-RPC arrays, with `${RUN}` for a fresh isolated
output directory and `${REPRO}` for the lawful original private reproducer.
Emit their objects as separate JSON lines to the tested binary's `--mcp`
mode, using model `a1200` and the matching Kickstart. Preserve dependent state
outputs between phases. Every native subprocess was bounded to 50 seconds.
The phase sequence is generic, generic-save, generic-confirm; cold-boot,
cold-editor, cold-1500, cold-2000; cold-load-request, cold-path-tab,
cold-directory, cold-directory-fixed, cold-filename, cold-native-loaded,
cold-native-run, cold-runtime-disk, cold-native-play.

The retained directory corrections replay the exact diagnostic interaction;
they are not a proposed learner-facing workflow. Licensed disks, programs,
ROMs and snapshots remain private. Original source ROM/media hashes were
rechecked unchanged. Active user game sessions were left intact.
