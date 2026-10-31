# PET correction and fixed board owners

Continue #2144 in the engineering-frontier lane, following the already approved
[PET board/firmware correction](2026-10-11-pet-board-firmware-design.md), merged
through docs #129. That plan already authorizes the three real configurations,
constructor/model/firmware changes, snapshot version 5 and rejection of v4.
Do not preserve the current hybrid or publish an intermediate v5 layout.

1. Recheck RULES.md and the ownership/runtime decisions. Reuse the approved
   primary-source records, VICE/MAME implementations and retained prototype
   evidence. The named donor archives are absent. Keep ROM inputs immutable.
2. Retain the four reproduced v4 failures in this plan's directory: both
   profiles lose a queued PRG and undelivered audio. Include `pending_prg` in
   the final runtime envelope and queued samples in machine state. These are
   part of the approved exact-restore v5 contract, not a new legacy policy.
3. Correct hardware before extraction. In `machine-commodore-pet/src/lib.rs`
   and a local `video.rs`, implement the approved 32K 2001N/3032 discrete board,
   4032 CRTC/graphics-keyboard board and 8032 CRTC/business-keyboard board.
   Validate discrete counters, VIDEO ON versus VERT DRIVE, CRTC sync wiring,
   paired 80-column fetches, video RAM decode, inverse/character-bank/raster
   addressing and complete displayed geometry against primary evidence and
   reference execution. Never hide a CRTC inside the discrete implementation.
4. Map BASIC 2 at C000 and BASIC 4 at B000. Extend machine `input.rs` and
   runtime `input.rs` for the business matrix and real modifier combinations.
   Update runtime `profiles.rs`/`runtime.rs` with matching ROM lengths and
   model-specific sources. Preserve old 40/80 profile IDs, add
   `commodore-pet-2001n-32k`, and correct display names/year/support claims.
5. Complete `runtime-commodore-pet/src/snapshot.rs` version 5 once its state
   layout is final. Check early v4 rejection without mutation, pending loads,
   queued samples, arbitrary CPU/video phases, first resumed pixels/audio/
   clocks, held keys, firmware selection and reset. Validate malformed payloads
   before installing anything. Freeze corrected complete states and three
   native continuations with project-written ROMs; corrupt a fixture to prove
   the comparison fails. No third-party firmware enters public fixtures.
6. Move the corrected engine/regressions into `common-commodore-pet`. Add
   `machine-commodore-pet-2001n-32k`, `machine-commodore-pet-4032` and
   `machine-commodore-pet-8032`, with fixed wiring and checked raw-state binding.
   Keep one runtime and runner with `runtime-commodore-pet/src/machine.rs`
   closed dispatch. Document the narrow runtime-shape exception. Add seven
   exclusive tests per owner and independent `docs/status/systems.toml` roots.
   Private workspace edges follow the approved split pattern; no new registry
   dependency is planned.
7. Run original/synthetic firmware, board/video/input/persistence tests and
   selected runtime/runner/fleet checks, strict Clippy/rustdoc, and fixture/
   ignore/registry/status/ownership guards. Identify matching firmware by full
   hash; require actual READY, typed output and final raster pixels within
   reference-measured bounds. Preserve the earlier failed tests as evidence;
   do not lengthen waits merely to make the old hybrid pass.
8. Publish current docs, three boot pages and exact pinned-player mappings,
   retain legacy URLs, and run site tests/build/accessibility. Inspect source
   CI owner counts, merge exact green heads and verify live routes, players
   and image hashes. Update #355/#2144 with explicit remaining limits.
9. Save receipts, verify remote retention and inspect ignored files/processes,
   then remove task worktrees, caches and helpers. Preserve primary checkouts
   and unrelated locked worktree records.

BASIC 1/chiclet machines, other RAM fittings, 60 Hz CRTC variants, second-PIA/
IEEE-488 completion and full 6545 interlace remain separate work. The bounded
correction and three owners do not close the wider PET family issue #355.
