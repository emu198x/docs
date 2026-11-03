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

## Implemented correction

[Source PR #2257](https://github.com/emu198x/emu198x/pull/2257), head
`70f1d2f4dd44d092bba40a81fe06e9d57ed73ca4`, implements the approved contract.
The pre-fix probe fails because a generic-only BASIC 1.1 directory boots
Oric-1. The corrected shared resolver rejects that directory for Oric-1,
retains it for Atmos, and selects each original author filename correctly.

Local verification: 81 affected machine/runtime/native tests passed, with
four fixture tests ignored in the default run. The two new strict original-ROM
tests were then run explicitly and both passed. The no-default-features
native build passed four unit and eight integration tests. Clippy with warnings
denied, formatting, registry validation and generated-status checks passed.
The initial Clippy single-element-loop failure was corrected without a lint
suppression; its failed output and the successful final run are both retained.

[Evidence index](2026-11-03-oric1-firmware-evidence/README.md) contains the
exact red/green resolver probes, logs and independently checked identities.
No CPU, ULA or snapshot schema/version changes were needed. The already
correct 64 KiB physical RAM profile descriptions were retained. This closes
the firmware fault only; physical PCB/fitting qualification remains open.

## Merged outcome

Source PR #2257 merged as `08c91234372dfb8a8d507bbe060077e396c2f7d7`.
[CI run 41619994789](https://github.com/emu198x/emu198x/actions/runs/41619994789)
passed for the exact reviewed head above: all four test shards, the aggregate
Test gate, Clippy, format, browser parity, firmware evidence, GTK host, registry,
workflow lint, test hygiene, test plan, synthetic cartridges and shell semver.
The [job ledger](2026-11-03-oric1-firmware-evidence/ci-jobs.json) retains the
conclusions and step records. Issue #345 is closed. Physical board qualification
remains open under #2144.
