# SNES regional board owners

Engineering-frontier continuation of the approved fixed-owner splits (#2144).
Keep existing behaviour and v1 saves unless a reproduced omission makes that
impossible. No new registry dependency or chip timing change is planned.

1. Read current rules and machine/runtime decisions. Compare the present core
   with the Nintendo reference books, local schematic provenance, vendored
   ares and OpenSFC's firsthand board reconstruction. It models NTSC and PAL;
   Super Famicom remains an NTSC profile, not an invented third motherboard.
   Specific PCB/chip revisions, front-panel differences and CIC handshake are
   unqualified. The named donor archives are absent.
2. Before extraction, reproduce restore/reset cache defects in
   runtime-nintendo-snes/src/runtime.rs and snapshot.rs. In particular, check
   restored IPL, SRAM and empty-state replacement. Preserve v1 bytes when the
   necessary information already exists in the saved machine. Validate board,
   PPU, firmware and vector bounds before changing runtime state.
3. Freeze complete original v1 states and the first three native frame/audio/
   clock continuations for all three profiles, including held controls,
   cartridge SRAM, built-in IPL, DMA and interlace where supported. Supplied
   firmware is checked separately by the restore/reset and v2 matrix tests. Prove a
   corrupted continuation fails. Retain the original generator and receipts.
4. Move machine-nintendo-snes intact to common-nintendo-snes. Create fixed
   machine-nintendo-snes-ntsc and machine-nintendo-snes-pal owners. Preserve raw
   v1 serialization through checked bindings, forwarding the existing machine
   operations without mutable access to replaceable raw state. Keep one family
   runtime/runner, profile IDs, aliases, destination selection and optional IPL.
   Record the narrow closed-dispatch runtime exception before implementation.
5. Add seven direct invariant tests per owner. Change systems.toml to two
   evidence roots, regenerate status and verify firmware/ignore/ownership guards.
   Run machine/runtime/runner/fleet checks, strict Clippy/rustdoc and full CI.
   Identify and exercise available real software without distributing it.
6. Publish current docs, exact board pages/captures and qualified player
   mappings. Keep the legacy URL. Run site tests/build/accessibility, verify the
   live end of the chain, and update #2144 with explicit remaining limits.
7. Commit and push green increments, merge exact verified heads, retain evidence
   and inspect all ignored files and remote retention. Remove task worktrees,
   caches and processes; preserve primary checkouts and unrelated locked records.

## Additional reproduced v1 omission — v2 approved 2026-11-01

A firmware-bearing runtime with no cartridge saves `machine: None`. Its IPL
exists only in the runtime cache and is absent from the v1 envelope. A restored
blank state therefore cannot recover that firmware for a later insertion.
The red regression is `a_blank_save_retains_firmware_for_a_later_cartridge`.

Proposed: write v2 with an independent optional IPL field, validate it against
any embedded machine before installation, retain a reader for cartridge-bearing
v1 states and reject v1 blank states whose firmware is unknowable. The original
six v1 fixtures remain immutable: test their raw machine/envelope continuation
through a test-only legacy encoder, and separately test complete v2 round trips
for blank/loaded, built-in/external IPL, reset and replacement. Steve approved this v2 policy on 2026-11-01. Validate malformed and inconsistent
firmware without mutation, and preserve the original v1 fixture bytes.
