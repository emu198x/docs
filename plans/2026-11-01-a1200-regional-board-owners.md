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
