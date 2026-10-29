# Restored SVI media and VIC-20 regional board identities

Lane: engineering-frontier. SVI #2189 is the first task under the request to
continue. The VIC-20 split below was approved on 2026-10-29, including the internal API,
private-dependency and release-wait agreement.

## SVI #2189: restore owns the media that reset will use

Root cause reproduced in #2189: `set_machine` installs the live machine without
recovering host media caches. A fresh receiver retains `bios_bytes = None`, so
reset clears the restored machine; an occupied receiver can rebuild stale media.
The v7 machine already contains firmware/cartridge bytes and immutable cassette
wave spans alongside mutable transport position.

1. Add `crates/runtime-spectravideo-svi-328/tests/restored_media.rs`. Cover both
   regional boards, fresh and previously occupied receivers, soft/hard reset,
   absent cart/deck replacing stale media, active cassette progress, stopped
   transport at insertion/reset, and invalid-restore atomicity. Reproduce the
   current failure before changing production code.
2. In `crates/common-spectravideo-svi-328/src/cassette.rs`, provide a cloneable
   immutable cassette image handle over the existing waveform spans, with
   private fields. The existing serialized `Cassette` fields and order remain
   intact. Expose capture/insert operations that recover media and rewind a new
   transport; capture must not advance, stop or rewind the live transport.
   This follows the existing image/cache versus transport boundary, including
   `loading-a-tape-is-not-pressing-play.md`; firmware still controls the SVI motor.
3. Add BIOS/cart/image accessors to `common-spectravideo-svi-328/src/lib.rs` and
   forward them in `runtime-spectravideo-svi-328/src/machine.rs`. Keep board
   construction fixed and concrete. No dependencies or schema changes.
4. Update only the private host caches in
   `runtime-spectravideo-svi-328/src/runtime.rs`: store the immutable cassette
   waveform for staged/rebuilt media, recover all caches from the successfully
   restored machine, and clear stale caches when the restored state has none.
   Preserve `snapshot.rs` v7 layout, normal insertion, active live transport and
   reset's existing cold-boot semantics. Do not reconstruct original CAS bytes
   from signal timings or retain a duplicate live CPU/transport as a media cache.
5. Verify frozen pre-split v7 re-encode/continuation, native frame and audio/input
   tests, reset/media matrix, CLI and fleet tests, strict Clippy/rustdoc and
   formatting. Run identified BIOS and Mini Golf CAS where available. A focused
   negative control must fail with the cache recovery removed. Push a linear
   PR; merge only after all exact-head checks succeed or are intentionally
   skipped. Close #2189 only after verifying the behaviour and CI outcome.

## Proposed next split: VIC-20 NTSC/PAL

Recommended: apply the existing Sord/Coleco/SVI static common-core pattern to
VIC-20. Alternative: complete #2189 and do reference/data corrections alone.
The current machine already contains `Vic20Model::{Pal,Ntsc}`, corresponding
runtime profiles and MOS 6560/6561 video. RAM expansion cartridges stay add-ons.
VIC-20 cassette/disk support (#364) and VIC-I timing/open-bus work (#1644/#1678)
remain separate; no chip or clock behaviour changes belong to this split.

- Introduce private `crates/common-commodore-vic-20/` and
  `crates/machine-commodore-vic-20-{ntsc,pal}/`; move input/keyboard and common
  wiring/history into the common owner, with fixed concrete board constructors.
  Neither machine depends on the other. Replace the internal shared model-based
  construction API and its `cold_boot(model, expansion)` operation with fixed
  board construction and family-runtime selection. The family still ships as
  `emu198x-vic-20` and uses `runtime-commodore-vic-20`.
- Update `Cargo.toml`, `Cargo.lock`, affected runtime/app imports and dispatch;
  add no external registry package and publish nothing. Add distinct machine IDs
  and explicit board evidence owners in `docs/status/systems.toml` and profiles;
  retain profile IDs/aliases, firmware conventions and family browser route.
- Capture synthetic v8 states and full video/audio/input/native-frame observations
  before moving code, including RAM-expansion and cartridge mappings. Preserve
  serialized machine fields and the v8 envelope's separate `cartridge_image`.
  Verify reset after restore still uses the saved cartridge. Keep regional ROM
  selection and external user-port/modem line behaviour intact.
- Source-check board differences against the primary VIC-20 library and vendored
  VICE, then verify fixed-board identity and wrong-board rejection. Compare
  original execution methods after field qualification. Run existing machine,
  runtime, CLI, fleet, registry/evidence and status-generation checks, strict
  Clippy, formatting and available matched regional ROM boots. Report fixture
  gaps explicitly. Update only the completed VIC row in #2144.
- Start this row before release #2170 only if explicitly approved as an extension
  to #2144's existing Sord/Coleco/SVI exceptions. The three private workspace
  crates/new dependency edges and replaced construction API require agreement
  under umbrella AGENTS.md. No general approval for other families is inferred.

Use current `origin/main` and linear task history: the repository permits only
rebase merges. Preserve unrelated primary branches/untracked plans and existing
locked worktrees. Verify remote retention, inspect all task files, stop owned
processes and remove worktrees/build caches before reporting completion.
