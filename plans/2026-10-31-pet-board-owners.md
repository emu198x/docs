# PET board owners and qualification gates

Continue #2144 in the engineering-frontier lane. The candidate split is the
implemented CRTC 40/80-column pair. Preserve existing profile/firmware IDs and
aliases. Do not equate the current implementation with the original 1977 PET
2001, which has no CRTC, or claim complete 4032/8032 hardware by changing names.

1. Recheck `RULES.md`, `knowledge/decisions/each-machine-has-its-own-machine-crate.md`
   and `knowledge/decisions/runtime-internal-shape.md`. Consult the umbrella PET
   reference and original board/ROM records; VICE is available at
   `emulators/c64/vice-3.10`. The three named donor archives are absent.
2. Before extraction, reproduce save fidelity through
   `runtime-commodore-pet/src/snapshot.rs` and `runtime.rs`: a pending PRG is
   outside the envelope, while `machine-commodore-pet/src/lib.rs` skips queued
   audio. Retain diagnostic source and red output in this plan's directory.
   Request approval before any save-schema change. Proposed complete version 5
   includes both and rejects version 4 before decoding; an approximate v4 reader
   is the alternative, not an implicit compatibility claim.
3. Confirm the support boundary before board qualification. Current BASIC is
   restricted to 8 KiB at C000-DFFF, while VICE's BASIC 4 image is 12 KiB. The
   logical input table is explicitly the graphics keyboard for both widths,
   and both profile years say 1977. Proper 4032/8032 qualification requires
   BASIC 4 mapping/firmware selection and matching graphics/business keyboard
   input, plus primary confirmation of the board's video RAM/clock wiring.
   Agree this prerequisite scope before implementing it; otherwise defer PET
   and select another documented regional split rather than inventing boards.
4. Following approval, repair save fidelity in the machine/runtime before
   extraction. Verify queued loads, queued samples, arbitrary CPU/CRTC phases,
   first resumed pixels/audio/clocks, held keys and restored reset. Freeze full
   corrected states and three native continuations with project-written ROMs;
   deliberately corrupt a fixture and prove rejection.
5. Extract the engine and regressions into `common-commodore-pet`. Add fixed
   `machine-commodore-pet-40col` and `machine-commodore-pet-80col` owners, checked
   raw-state binding and `runtime-commodore-pet/src/machine.rs` closed dispatch.
   Keep the family runtime and runner; document its narrow runtime-shape
   exception. State qualified historical boards and remaining limits precisely.
   No new registry dependency is planned; private workspace edges follow the
   approved splitting pattern. Add seven direct tests per owner and independent
   registry/evidence roots in `docs/status/systems.toml`.
6. Run selected common/owner/runtime/runner and fleet tests, strict Clippy and
   rustdoc, fixture/ignore/registry/status/ownership guards and real-ROM checks.
   Review mutable/raw-engine escapes, skipped transient fields, reset caches
   and malformed payload rejection before pushing the final source head.
7. Publish current docs, two boot-capture routes and exact pinned-player
   mappings, retaining the family URL as a default-profile redirect. Check site
   tests/build/accessibility, source CI ownership counts, exact green heads and
   deployed route/player/image results. Update #2144 and retain receipts.
8. Verify remote retention and inspect tracked/untracked/ignored files and local
   task processes, then remove worktrees, caches, probes and helpers. Preserve
   primary checkouts and unrelated locked worktree records.
