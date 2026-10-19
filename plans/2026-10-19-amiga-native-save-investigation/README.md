# Amiga native Save: disk-change investigation

`load_media` suppresses the drive-change latch on a running non-A1000 Amiga.
The unchanged emulator can save and reload Bank or Risk when the existing
`insert_media` tool leaves that latch pending. No runtime fix is included:
implementation remains deferred while the approach is reviewed.

The approved [runtime fix and generic-route verification](fix/README.md)
follow this pre-fix investigation.

Issue: [Emu198x #1877](https://github.com/emu198x/emu198x/issues/1877).
Emulator: `6cc5d5f9e7fe6507a079f237bc44da0dc95fe25c`, version 0.34.2.
Disk validator: Build198x `f7016398deb1fff9dc1efb6713dfab8c7bacf2d0`, 0.2.12.
Machine: stock PAL A1200, 2 MiB chip RAM, no fast RAM.

## Controlled results

All three branches restore the same native Save requester and mount the same
empty writable OFS disk. Both immediate exports equal the blank source bytes.
Only the change signal differs between the two Amiga-specific tool branches.

| Mount route | Change latch immediately after mount | After 60 guest frames | Native Save export |
| --- | --- | --- | --- |
| `load_media` | inactive | no new steps; cylinder 42 | corrupt |
| `insert_media`, `change_pending:false` | inactive | no new steps; cylinder 42 | byte-identical to corrupt generic export |
| `insert_media`, `change_pending:true` | pending | 44 new steps; cylinder 0 | valid OFS, `finish.amos`, 17,734 bytes |

The corrupt export fails `verify` with `unknown secondary type`; `manifest`
reports `block pointer out of range`. They are different validator commands,
not interchangeable error strings. The valid branch passes both.

The retained larger-game snapshot already contains earlier disk-swap history.
Its mounted image is AMOSPro_System; the corrupt export's root names the prior
StyledBoard source volume. Its root differs from that earlier root in only six
longwords, including the checksum, a hash bucket and dates. This is evidence
of stale filesystem metadata, not a clean single-swap corruption experiment.
The same-tool true/false comparison holds that history constant.

## Fresh boot check

A separate editor was booted from the system disk, then the two-line program
below was typed and syntax checked before any live swap:

```basic
Print "Disk change probe"
Wait Key
```

When the writable blank disk is mounted before opening Save As, selecting DF0
and saving through the generic route still reports the old AMOSPro_System as
write protected. The export stays empty. With change notification enabled,
the export is valid and contains the 60-byte native program. Its literal name
is `probe.amosS`: the scripted filename edit left a final `S` from the default
pattern. The name discrepancy does not establish filename equivalence between
branches; the volume identity and persisted bytes are the findings here.

An earlier fresh experiment swapped disks while the requester already held
its old directory lock. Both branches reported the original volume write
protected. That experiment does not show a second emulator defect: changing
physical media cannot retarget an application's existing directory lock.

## Native round trip of the larger game

The valid 17,734-byte save was mounted in an independently cold-booted editor.
The initial scripted load was invalid evidence: the requester still named
`AMOSPro_System:*.AMOS`, the removed volume. Selecting `DF0:*.AMOS` explicitly
listed `finish.amos`; clicking the filename field, entering the name and
confirming loaded the full listing. F2 reported no errors.

F1 then requested AMOSPro_System. Returning that disk and confirming Retry
allowed the font/runtime access to finish and displayed the styled game.
SPACE, R and B rolled six and secured six points in round one. The captures
show both states. This qualifies the existing explicit-notification route;
it does not qualify the still-unmodified generic route or learner outcomes.

## Cause and proposed scope

`runtime-commodore-amiga/src/runtime.rs::insert_floppy_bytes` derives
`change_pending` only from `model().is_a1000()`. `mount_adf` immediately
acknowledges the latch for every other model, including a live media swap.
The drive already asserts the latch on insertion and clears it on a selected
step with media present. `insert_media` exposes that existing model and defaults
to a pending change; the generic tool discards it before guest execution.
No evidence here calls for changing disk-write encoding or export.

The primary 1985 Hardware Reference Manual, CIA-A PA2 description (umbrella
`reference/by-system/commodore-amiga/1985-amiga-hardware-reference-manual.docling/in.md`,
line 5341), says change stays active until insertion plus a step pulse.
Vendored WinUAE `disk.cpp::drive_eject` asserts `dskchange`, and `drive_step`
clears it when media is present. The existing Emu198x drive models those
semantics; the runtime's mount policy bypasses them.

The bounded proposal is to distinguish startup/reset mounting from live
insertion in the existing runtime, preserve snapshot reattachment, and test
all OCS/ECS/AGA dispatch paths plus A1000 startup. No public API or dependency
change is proposed. Exact startup/reset semantics still need regression tests
before an implementation is accepted. No broader hardware-accuracy claim is
made from this one native application.

## Replaying and preservation

`requests/` retains MCP JSON-RPC arrays; feed each array's objects as separate
JSON lines to the pinned emulator with model `a1200` and the lawful matching
Kickstart. Substitute `${REPRO}` for the original private reproducer and
`${RUN}` for an isolated output directory. Phases are dependent: preserve
snapshot outputs between them. Each subprocess was bounded to 50 seconds.
The cold boot reaches the editor after four 500-frame phases plus Return.

The corrected load chain uses `cold-load-request`, `cold-path-tab`,
`cold-directory`, `cold-directory-fixed`, `cold-filename`, `cold-native-loaded`,
`cold-native-run`, `cold-runtime-disk`, then `cold-native-play`. The directory
phase intentionally removes the previously appended text; it is an exact
retained diagnostic sequence, not a recommended learner workflow.

`verification.json` records queries, controls and private input/output hashes.
`artifact-hashes.json` binds the public evidence. Licensed disks, snapshots,
ROMs and native program bytes remain private. Retain the local reproducer
until #1877 and its regression evidence are accepted. Active user game
sessions were left intact.
