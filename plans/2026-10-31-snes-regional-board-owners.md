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
   cartridge SRAM, nondefault IPL, DMA and interlace where supported. Prove a
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
