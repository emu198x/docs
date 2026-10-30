# Aquarius regional board owners

Continue the approved #2144 split programme in the engineering-frontier lane.
Use the established common engine, fixed board owners and family runtime enum.
Private workspace crates only; no registry dependencies or publication.

1. Freeze the original `machine-mattel-aquarius` NTSC and PAL payloads and
   continued native frame/audio output with project-owned firmware in
   `test-data/mattel-aquarius/board-split-v4/`. Capture the existing NTSC
   runtime version-4 envelope too. Prove a corrupted fixture fails.
2. Move the engine and component tests into `common-mattel-aquarius` without
   changing hardware algorithms or serialized field order. Make
   `machine-mattel-aquarius` the fixed NTSC owner and add
   `machine-mattel-aquarius-pal`. Expose checked state binding, not unchecked
   deserialization or mutable access to the raw state. Give both owners direct
   synthetic boot, input, cartridge/expansion and native-boundary evidence.
3. Update `runtime-mattel-aquarius/src/{machine,profiles,runtime,snapshot,input,queries}.rs`
   to select fixed owners. Retain `mattel-aquarius` as the default NTSC profile;
   add `mattel-aquarius-pal` for the already modelled PAL engine. Keep version 4,
   firmware discovery and save paths. Reject foreign hardware before changing
   runtime state. Test live continuation and reset/media behaviour after restore.
4. Add PAL to `docs/status/systems.toml`, regenerate status, and verify exclusive
   evidence ownership. Run common/owner/runtime suites, strict Clippy/rustdoc,
   formatting and fleet capability conformance. Run locally available firmware
   separately; do not equate synthetic boot evidence with manufacturer boot.
5. Update current docs and site profile mapping/routes, with an embed only if
   the pinned player has the exact profile. Run site tests/build/accessibility.
   Push, review CI, merge using repository policy, check deployed pages and
   update #2144. Remove task worktrees and caches after verifying retention.

The reference library documents PAL/NTSC sync differences but lacks a primary
service manual. This extraction preserves the existing engine's regional clocks,
scanlines and palette; it does not newly certify those values or infer board
revisions or maker identities from branding. Any timing correction is separate
source-backed work. Expansion RAM, character-ROM revision and the Mini Expander
remain configurations, not additional board owners.
