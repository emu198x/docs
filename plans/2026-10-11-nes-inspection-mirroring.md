# NES screen inspection and CIRAM mirroring

Lane: best-in-class campaign. Scope: the existing side-effect-free screen inspector.

## Confirmed root cause

`Nes::effective_nametable` asks the mapper for an override, then returns raw
CIRAM at `i & 0x07ff`. The PPU instead maps the address through the current
mirroring mode. Horizontal and both single-screen modes can therefore expose
bytes that a guest cannot read at the same logical address. Vertical is a control.

## Bounded correction

Keep the existing 2 KiB return shape and mapper override precedence. Expose a
read-only mirrored-CIRAM accessor in the PPU using its existing address decoder;
use it for both live PPU reads and the inspection fallback. Preserve the raw
`read_nametable` API. No clock, register, memory layout or snapshot change.
This corrects the existing inspection contract, without a new architectural pattern.
The separate four-screen cartridge RAM proposal is outside this change.

## Steps and verification

1. Add `crates/machine-nintendo-nes/tests/nametable_inspection.rs` with original
   6502 guests. Initialize distinct CIRAM contents, select each MMC1 mirroring
   mode, read all 2048 logical bytes through buffered PPUDATA into PRG RAM,
   then compare with the inspector. Require a completion marker and check actual
   bytes against independently specified physical-page mappings. Capture red.
2. Add the small shared read path in `crates/ricoh-ppu-2c02/src/lib.rs` and use it
   from `crates/machine-nintendo-nes/src/lib.rs`. Repeat the guest test and retain
   existing Sunsoft-4/MMC5 override coverage. Check repeated inspection leaves
   clock, CPU program counter and CIRAM contents unchanged.
3. Run affected tests, formatting and all-target Clippy. Publish a focused PR,
   wait for required checks on its exact head, then merge and verify the tree.

## Sources and boundaries

- Shared reference: `reference/by-system/nintendo-nes/mmc1-reference.md`.
- Reference implementation: `emulators/nes/Mesen2/Core/NES/BaseMapper.cpp`,
  `SetMirroringType`: vertical [0,1,0,1], horizontal [0,0,1,1], lower [0,0,0,0],
  upper [1,1,1,1]. This is implementation precedent.
- Binding decisions: `knowledge/decisions/nes-test-oracle-priority.md`,
  `nes-clock-topology.md`, and `tools-follow-the-machine-spec.md`.
- The invariant is inspection equals guest reads, not a claim about every
  possible scrolling screen or rendering-time mapper override.

## Evidence

The baseline fails horizontal, lower single-screen, upper single-screen and
mode-transition regressions. The vertical control passes. Examples: upper mode
returns $00 instead of the guest's $44 at $2000; horizontal/lower modes return
$44 instead of $00 at $2400.

All five corrected regressions pass: 18,432 guest bytes across nine mode phases.
The existing Sunsoft-4 guest also passes. Full affected machine/PPU suites report
140 passes, zero failures and 133 ignored tests. These are libtest counts;
fixture skip accounting remains a separate CI-ledger check. Affected all-target
Clippy and workspace formatting pass.

The full Mesen core independently reads the same expected 2048 bytes for each of
four modes; two captures per mode are identical. Rebuilt ROM hashes also match.
See [reproducible evidence](2026-10-11-nes-inspection-evidence/README.md).

Source [PR #1732](https://github.com/emu198x/emu198x/pull/1732), tested commit
`360451bd76b0412a2bcf390e59af333f721cb789`. merged as `0ec2b192848da4765d4da71822e1db440fb7f7a3` after required checks passed.
The merged tree equals the tested head and is an ancestor of fetched main.
[CI run 38166511618](https://github.com/emu198x/emu198x/actions/runs/38166511618)
records 28 machine passes, two explicit fixture skips and 133 ignored tests;
all 110 PPU tests executed and passed. Neither package has failures or
unexplained ignores. Builds, browser parity and firmware gates also passed.
