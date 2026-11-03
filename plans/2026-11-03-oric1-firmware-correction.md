# Oric-1 firmware selection correction

Engineering-frontier accuracy for source #345. The distinct firmware contract
from the October plan was approved on 2026-11-03. The existing workspace sha2
0.11 dependency is also approved for strict runtime tests only.

1. Reproduce the shared-ID/generic fallback on current source using the
   retained author-distributed BASIC 1.0/1.1 images. Verify both SHA-256 and
   independent MAME SHA-1 identities; keep firmware private.
2. In runtime-oric-atmos/src/profiles.rs add Model::firmware_id and oric1-rom,
   model-specific names and EMU198X_ORIC1_ROM. Atmos keeps oric-rom and its
   current environment/name conventions. Update runtime.rs lookups/errors
   and lib.rs exports. No CPU/ULA or snapshot changes.
3. Defer --rom specifications in emu198x-oric-atmos/src/app.rs until the
   final model is known, then use the shared FirmwareOverrides parser and
   builder. Use that same resolution in UI, headless and MCP startup.
4. Add default regressions for missing/wrong firmware IDs, synthetic custom
   images, both argument orders, directory/name/environment precedence,
   both-model switches and failure atomicity. Run subprocesses with isolated
   environments rather than mutating process-global environment in tests.
5. Add opt-in runtime real-ROM tests with full SHA-256 identity gates, exact
   banner/Ready and keyboard-entered STR$ behaviour. Retain a wrong-ROM
   negative control. Run the affected machine/runtime/binary tests, default
   UI bridge tests, Clippy, format and applicable CI before merging.
6. Record migration, passing evidence and the unresolved physical-board
   qualification boundary. Close #345 only after the real resolver and
   strict ROM regressions pass. Update #2144 without claiming new boards.

Source worktree: /private/tmp/198x-oric-firmware-source; docs worktree:
/private/tmp/198x-oric-firmware-docs; build cache:
/private/tmp/198x-oric-firmware-target; private transient inputs:
/private/tmp/198x-oric-firmware-assets. Preserve unrelated primary checkouts
and earlier locked Atari/PET investigations. Retain exact task commits and
useful evidence before removing worktrees, caches and transient copies.
