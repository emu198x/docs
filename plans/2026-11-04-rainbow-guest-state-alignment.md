# Align Rainbow Islands by guest state

Engineering-frontier catalogue continuation of Emu198x #2265. Start from
source `eed1923b47965069b342194563b0b83849f6a5d5` and docs
`50c244ffede7c7b846fa137985b56bfcbae43d4c`. The user approved continuing the
Rainbow-first diagnosis, then the other nine +3 cases and CPC qualification.
No hash change follows merely from a successful boot or matching still.

1. Restore only the needed prior probes, identities and observations from the
   verified private `2026-11-04-amstrad-audio-phase-complete.tar.gz`; check its
   complete SHA-256 and every extracted member's internal SHA-256.
2. Extend the existing MAME Lua observer using documented read-only register,
   address-space and saved-item access. Record PC/SP, paging state, guest RAM
   and native pixels across bounded consecutive native fields. Confirm the
   actual displayed RAM bank before comparing its bytes. Preserve ordinary
   firmware boot/ENTER and the explicitly derived 42-track diagnostic view;
   never rewrite the original ZIP/disk. Require complete nonempty observation
   counts and native frame-number increments. Bound each reference run to
   90 wall seconds and 140 emulated seconds initially.
3. Reuse the existing ignored catalogue-local Rust probe with no new
   dependency, API, schema or clock change. Capture CPU registers, physical
   banks/paging, displayed screen RAM and published frame output at the
   ordinary 6000-field waypoint and a bounded continuation. Assert the normal
   RGB hash before observation. Build in the standard release profile; bound
   the complete diagnostic build/run to 600 wall seconds. Keep the expected
   catalogue hash unchanged while collecting evidence.
4. Establish matching guest code/attract-loop points from the actual original
   program and screen-memory transitions. Compare instruction/interrupt and
   memory-write progress there. Test whether reference video follows its
   changing guest memory before using screenshots as an execution oracle.
   Explain the first meaningful divergence; do not fit time/phase or alter
   memory to obtain a stored picture. Consult held primary references and
   vendored MAME/Fuse/SpecIde before any hardware fix.
5. If a bug is reproduced, make a narrow fix with a failing control and tests.
   Any new dependency, public contract or snapshot policy needs a concrete
   approval first. Only qualify an expectation once its mechanism and semantic
   anchor are supported. Otherwise publish the precise remaining blocker.
6. Preserve the remaining nine +3 expectations. Locate a genuinely matching
   earlier producer before extending audio qualification to those pre-existing
   failures. CPC remains on 0.8 under #2284 until independently qualified.
7. Publish source/docs changes through normal PR checks, update #2265, retain
   private raw observations and original signed commits, and clean every
   owned workspace/cache/process after verified archival and integration.

Owned resources: source worktree `/private/tmp/198x-rainbow-guest-state`;
docs worktree `/private/tmp/198x-rainbow-guest-docs`; evidence
`/private/tmp/198x-rainbow-guest-evidence`; if required, build cache
`/private/tmp/198x-rainbow-guest-target`. Primary checkouts and the umbrella's
existing `docs/repo-map.yaml` conflict belong to other work and stay untouched.

## Findings and the existing fixed-waypoint convention

The 64-field guest control reproduces every MAME register record, physical RAM
snapshot and pixel buffer when CPU-map reads are omitted. Both emulators have
identical original code in the shared delay and page-fade routines. The old
expected RGB hash is the BEST 5 table and appears at fields 6020–6461 in the
untuned post-waypoint timeline: 442 consecutive identical complete pictures.
At 6000 the original guest is fading the preceding credits page.

`catalogue-startup-navigation.md` already documents using the midpoint of a
measured settled page (the Banshee case). Follow that existing convention;
there is no need to introduce conditional startup or alter a public API.
Measure the complete first attract cycle without selecting by expected hash,
identify the BEST 5 page independently from the original guest's caller/stack
and displayed content, then select its measured stable midpoint. Retain both
original expected hashes. This also avoids waiting through repeated attract
cycles. Before editing the manifest, confirm the same page from MAME's
read-only code-point milestone and compare the complete stable screen bytes.

Additional probes: 1000 fields after the original waypoint, then a complete
3600-field first-cycle timeline, with only fixed-interval full RAM/PNG dumps;
all frame hashes and metadata remain complete. Save each temporary probe
version before replacing it. A first MAME milestone fired at 41.49 seconds,
well before the coarse 125.35-second observation, so capture immediately after
that first milestone and keep the later checkpoint as an observer control.

## Next baseline candidate

The Chase H.Q. +3 audio expectation was introduced by
`cf6ee98c2857c37b0683945107c695c316a49fcc` (2026-10-06, workspace 0.28.0).
Its +3 setup uses the same boot/50/5/20 navigation as current code. The v0.28.0
release tag predates the speaker/mixer recapture and differs in relevant
Spectrum audio code and manifest data, so it is not an interchangeable baseline.
Build the exact capture commit read-only in detached worktree
`/private/tmp/198x-plus3-baseline-028`, using its already-installed pinned Rust
1.99.0 and separate cache `/private/tmp/198x-plus3-baseline-target`. No manifest
or dependency changes. Bound the build to 600 seconds and stop its owned
process group if free disk falls below 512 MiB. A successful build is only a
candidate; accept it only after it reproduces the existing complete frame and
audio expectations with the original inputs. Preserve all failed results.

## Outcome

The first high-score page spans fields 1535–1976. MAME independently reproduces
all 6912 displayed bytes and 64 consecutive original-hash pictures at the
original guest-code milestone. Source #2289 changes only the waypoint to its
midpoint, 1755, with both goldens retained. The real run and snapshot replay
pass; the old waypoint still fails on the same clean producer.

The exact historical producer builds unchanged and reproduces both complete
original hashes for all five audio-only cases. Their current failures remain
open for comparison against that verified producer. Evidence and reproduction
commands are in [the report](2026-11-04-rainbow-guest-state-evidence/README.md).
Private raw evidence and both binaries are retained in the verified recovery
archive; completed workspaces and caches can be removed after integration.
