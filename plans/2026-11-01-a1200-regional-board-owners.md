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

The approved fix freezes the original coefficient bits in a portable table.
All eight original continuations now match exactly on both macOS and Linux ARM.
No tolerance or skipped assertion has been introduced. The split and its site
publication remain gated on final Linux x86 CI.


Source PR: [#2226](https://github.com/emu198x/emu198x/pull/2226).
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


## Approved portable resampler correction

Steve approved the focused coefficient fix on 2026-11-01. Freeze the existing
macOS ARM kernel as explicit little-endian f64 data, retaining its formula,
normalisation and original production coefficient bits. Runtime construction
loads this fixed table rather than calling host sin/cos. Keep the standalone
original formula generator and SHA-256 provenance with the data. This adds no
dependency, changes no history layout and preserves the original frozen v66
continuations. It makes a previously host-dependent discretisation explicit;
it does not introduce a new analog model or promise every floating-point
filter in the fleet is portable.

Verify: generator byte identity on the original host, existing shell pulse/
settling/bounds tests, all eight unchanged A1200 fixture cases on macOS and
native Linux ARM, then Linux x86 CI. Keep all comparisons exact. If any field
still differs, diagnose it before further changes. Re-run selected strict
Clippy, consumers and the source/site/doc gates before exact-head merges.


The original diagnostic worktree, both Docker probe images and the Linux target
volume were removed after successful portable replay and positive byte checks
against committed source/docs copies. Final selected runtime tests at
`3fc8b66bc689193d93a913b04db69a834578ebee` report 75 passed and one existing
ignored diagnostic. Source CI is run 41340229567; Linux x86 remains pending.


The commit-policy check rejected the release merge commit. Rebase-linearised
the task branch only, retaining a remote backup and the verified
`pre-linearization.bundle`. The original baseline also has the durable remote
tag `evidence/a1200-v66-original-baseline`. Final linear head is
`8bf0f81710aa218a0366a98f6484b27c5c5b3894`, with the **identical** verified tree
`56b5a771b04a89b414c3d0e9b16cc9fc540a9a47`. A lease guarded the task-branch update;
no main/shared history was rewritten. The backup branch can be removed after
the bundle is retained in merged docs and final source CI passes.


## Source completion and site publication dependency

[Source PR #2226](https://github.com/emu198x/emu198x/pull/2226) merged as
`85f99c20e45814daba85197bfc0ab662248b811b` after final-head
[CI run 41340813947](https://github.com/emu198x/emu198x/actions/runs/41340813947)
passed. Both original v66 continuation binaries ran and passed on Linux x86;
the ledger records seven passed, zero ignored/skipped/failed for each owner.
The runtime ledger records 336 passed, 31 ignored and two explicit external
fixture skips. Exact replay tests have no skips. The source implementation,
fixtures and generated status files match the verified head. Parallel release
runner commit `89055fa89` changes only qualification workflow/metadata and was
preserved. Evidence tag `evidence/a1200-fixed-owners-2026-11-01` retains the
exact tested head; the original-fixture tag remains too.

[Site PR #43](https://github.com/emu198x/emu198x.github.io/pull/43) remains a
draft. Its CI passed all 133 tests, then correctly failed the build because
`https://github.com/emu198x/emu198x/releases/download/v0.46.0/dist-manifest.json`
returns 404. `gh release view v0.46.0` also reports `release not found`.
No fallback, release publication, tag change or guard bypass was introduced.
The running main-branch package qualification does not publish releases.
After v0.46.0 is published, rerun Pages on head
`a5a6eccfae0277fed5c15be46fa59b8ed0c85ac0`, merge after green checks and verify
both regional routes/images. Until then, neither page is claimed as deployed.
The task worktree is unnecessary for that retry: the branch and captures are
pushed, with all local build/accessibility receipts retained here.


## Cleanup receipt

The original, source and site task worktrees have been removed with
`git worktree remove` after checking tracked, untracked and ignored files.
Source commits are retained by the verified-head evidence tag; the unfinished
site branch remains pushed for its release-dependent CI retry. The shared UI
clone was clean and matched remote tag v0.5.0 before removal. Both Docker probe
images and the target volume are gone. The task build cache, diagnostic output
copies, generator scratch output and npm cache are removed; `df` reports 30 GiB
free, compared with about 22 GiB before this cleanup. Original code/probe data,
CI logs, captures, checksums and recovery history are retained in this repo.

Tracker #2144 records only the two implemented A1200 regional configurations
as split; other PCB/chip populations and OCS/ECS owner work remain open.
The site blocker is recorded in
[PR #43's retry comment](https://github.com/emu198x/emu198x.github.io/pull/43#issuecomment-6562868660).
The docs task worktree will be removed after its exact-head merge; no workspace
is required to retry the pushed site branch when the release becomes public.


## Publication follow-up — 2026-11-02

The public v0.46.1 release manifest resolved the former v0.46.0 gate. Site
PR #43 is now merged and deployed, including both original A1200 captures and
four new ECS pages. The [ECS continuation receipts](2026-11-02-amiga-ecs-board-owners.md)
record passing site CI, all 125 live route checks and six byte-identical image
checks. The A1200 pages still omit embeds for the A500+A501-only player.
