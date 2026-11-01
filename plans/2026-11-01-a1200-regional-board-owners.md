# Fixed A1200 PAL and NTSC owners

Engineering-frontier continuation of #2144 after #2224. Steve approved the
splits and instructed this A1200 continuation on 2026-11-01. Preserve the two
existing A1200 profile IDs, aliases, v66 save fields, hardware clocks and one
Amiga family binary. Private workspace dependencies and the replacement Rust
construction API follow the already approved split pattern.

1. Inspect the Commodore A1200 schematic oscillator/strap evidence, existing
   AGA wiring and runtime decisions. Record the implemented PAL/NTSC scope;
   do not claim every PCB revision. The three named donor archives are absent.
   No timing/chip behaviour is being replaced; consult vendored WinUAE/MAME
   if a pre-split correctness discrepancy requires such a change.
2. Before extraction, add
   `crates/runtime-commodore-amiga/tests/a1200_board_baseline.rs` and freeze
   `test-data/commodore-amiga/a1200-v66/` from source cbcda19a1. Use owned
   synthetic reset firmware, guest CPU register/RAM writes, active picture
   and audio, held/released controls, persisted synthetic floppy media,
   progressive/interlaced fields, and a half-CCK cut. Retain original save
   bytes, hashes of complete frame packets/final save bytes, complete audio
   sample bits and clocks for three following native fields. Prove pre-split
   restore/replay, plus an intentionally corrupted expected-output control.
   Capture is create-new-only and refuses any source HEAD after the baseline.
Before extraction, reproduce and fix the existing NTSC display descriptor:
`MachineCore::display` is pinned to PAL/14.187580 MHz while emitted frame
metadata already uses the live NTSC clock. Derive both pixel clocks from one
helper and report the selected TV standard and its doubled active-line count.
Do not alter frame bytes, master-clock loops or v66 fields. Compare reported
clock directly against the emitted frame signal in a regression test.

3. Move `machine-commodore-amiga-a1200` wiring/tests into
   `common-commodore-amiga-aga`. Give its core a board marker; create thin
   `machine-commodore-amiga-a1200-pal` and `-ntsc` owners with fixed regions,
   stock 2 MiB defaults and machine IDs. Preserve snapshot fields. Reject a
   foreign-region raw restore before mutation; provide no mutable raw-engine
   replacement path. Remove misleading A1000 constructors from this AGA core.
4. Keep the generic runtime/live-access shape. Update
   `runtime-commodore-amiga/src/{runtime,variants,live_access,snapshot,profiles}.rs`
   with PAL/NTSC aliases and four-arm family dispatch. Fallible board restore
   errors propagate through candidate restore. Validate the selected profile
   against its fixed owner; do not relabel a PAL machine as NTSC. Update all
   native/browser/debug consumers and workspace manifests without shrinking
   their existing surfaces. Keep OCS/ECS schemas and behaviour unchanged.
5. Add seven exclusive invariant tests to each owner: fixed identity/region/
   CPU clock, guest reset execution, native boundary clocks, chip-RAM wiring,
   active picture/audio against an inactive control, exact held-input restore
   and release, foreign-region rejection without mutation. Preserve the frozen
   pre-split fixtures, all relevant runtime tests and debugger parity.
6. Add the two machine IDs to `docs/status/systems.toml`, preserving the
   aggregate Amiga entry for the still-unsplit OCS/ECS models. Regenerate status;
   enforce zero machine-to-machine dependencies. Run selected tests, strict
   all-target Clippy, formatting/registry/fixture checks and full CI. Existing
   strict rustdoc private-link errors remain recorded, never suppressed.
7. Publish docs/status and exact board routes/capture provenance. Preserve the
   family route and its A500 browser presentation. A1200 pages omit an embed
   until the published module supports the exact A1200 profile; no substitution.
   Merge exact verified heads, verify deployed routes/images, update #2144.
8. Retain receipts/checksums and original commits remotely. Inspect tracked,
   untracked and ignored files, then remove task worktrees, captures, render
   intermediates and build caches, and verify task-owned processes have exited.
   Preserve primary checkouts and unrelated locked worktrees.


## Local verification and remaining merge gate

The fixed-owner implementation is prepared. Common AGA/runtime tests report
386 passed, 32 existing ignored external-fixture/diagnostic cases; both owner
suites report seven passed and none ignored. The eight frozen original
continuations pass on macOS ARM. Strict selected Clippy and registry checks
pass. These are local results, not a merged-release receipt.

Both native regional configurations show the Kickstart 3.1 insert-disk screen
after 250 native fields. The exact ROM identity, complete captures and command
logs are retained in [the evidence directory](2026-11-01-a1200-regional-board-owners/).
This does not qualify Workbench or a software library, original hardware,
native menus, host audio devices, or every A1200 PCB revision.

The original, untouched source also exposed a cross-host resampler-history
limit. Linux ARM matches all board bytes, pixels, emitted audio sample bits
and elapsed clocks but changes four pending f64 correction values in the final
v66 envelope. macOS ARM matches the complete frozen final saves. Every other
saved field, including analog-filter history, matches. Original Linux x86 CI
also fails the strict continuation assertion; direct x86 state has not been
captured. See [the failing baseline run](https://github.com/emu198x/emu198x/actions/runs/41332390233).

The pending choice is a focused portable-coefficient fix before merging,
recommended to retain one exact cross-host baseline, or preserving the old
host-dependent behaviour with separately captured exact platform baselines.
No tolerance or skipped assertion has been introduced. The split and its site
publication remain gated on resolving this choice and passing final CI.


Source draft: [#2226](https://github.com/emu198x/emu198x/pull/2226).
The native UI and both browser consumers compile with default features.
The site companion branch `docs/a1200-fixed-board-pages` passes 133 tests,
builds and checks 121 routes, and audits 105 content routes in both themes
with zero accessibility defects (16 redirect stubs excluded). It has not been
published: source merge and the exact final CI head remain required.

The source, docs and site task worktrees remain under
`/Users/stevehill/Projects/198x/Emu198x/.worktrees/a1200-{source,docs,site}`
for the pending DSP decision, verification and publication. Their committed
branches preserve the work. Remove them after exact-head merges and deployed
route/image verification. The original diagnostic worktree and Linux ARM
Docker image/target volume are still needed for the cross-host regression;
remove them after portable-coefficient verification or platform-baseline capture.


Retained diagnostic resources, all task-owned:

- `/Users/stevehill/Projects/198x/Emu198x/.worktrees/a1200-source`
- `/Users/stevehill/Projects/198x/Emu198x/.worktrees/a1200-docs`
- `/Users/stevehill/Projects/198x/Emu198x/.worktrees/a1200-site`
- `/Users/stevehill/Projects/198x/Emu198x/.worktrees/a1200-original`
- `/private/tmp/198x-a1200-target` (incremental-disabled local build cache)
- `/private/tmp/198x-a1200-docker` and `/private/tmp/198x-a1200-buildx`
- Docker images `198x-a1200-probe:20261101` and
  `198x-a1200-probe-arm:20261101`; volume `198x-a1200-linux-target`.

The original worktree, build cache and Linux ARM image/volume enable the pending
cross-host regression. Exact final merges and publication permit removing all
four worktrees; completing that regression permits removing diagnostic images,
volumes and build caches. No task-owned build, browser or container process is
still running. All unique code and evidence are committed and pushed; temporary
logs and output copies can be removed once their retained checksums are verified.
