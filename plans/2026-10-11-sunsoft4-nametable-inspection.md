# Make Sunsoft-4 screen inspection follow live nametable reads

This is best-in-class campaign work under NES mapper coverage issue #92.
Sunsoft-4 implements `Mapper::nametable_read` for its CHR-ROM nametable
mode but inherits `nametable_peek`, which returns `None`. The trait explicitly
requires these views to agree. `Nes::effective_nametable` consequently reports
CIRAM instead of the cartridge bytes supplied to the PPU.

The correction is bounded: override the existing side-effect-free method and
have the existing read method delegate to that same mapping. No new state,
public signature, serialized field or dependency is needed. Leave unrelated
mapper behaviour and the machine's CIRAM fallback unchanged.

## Work and verification

1. Add regressions in
   `crates/format-nintendo-nes-ines/tests/parser.rs`: compare peeks with live
   reads across all four mirroring modes, all 4,096 nametable addresses,
   bank changes, ROM write rejection and disabling ROM mode. Confirm failure
   before editing production code.
2. Add `crates/machine-nintendo-nes/tests/sunsoft4_screen.rs`. Run a real
   CPU program that selects ROM nametables, reads them through buffered
   PPUDATA and stores the results in RAM. Compare those guest observations
   with `effective_nametable` for each mirroring mode, including attribute
   bytes and both logical pages. Require the completion marker and nonzero
   observations.
3. Fix `crates/format-nintendo-nes-ines/src/mappers/sunsoft4.rs` by sharing the
   existing mapping through `nametable_peek`. Run affected mapper/machine
   tests, Clippy with warnings denied and formatting. Record red/green evidence.
4. Open a source PR, require its exact-head CI, then merge if ready. Update
   the broad mapper issue with the bounded result; it is not closed by this fix.

## Reference context

The vendored Mesen2 `Core/NES/Mappers/Sunsoft/Sunsoft4.h`,
`UpdateNametables`, and ares `ares/fc/cartridge/board/sunsoft-4.cpp`,
`readCHR`, both select the ROM nametable bank after applying the configured
mirroring. This change does not infer new chip behaviour from those sources:
it makes our existing observation API describe the same memory as our live
PPU path. The direct read/peek invariant is the decisive regression.

## Executed result

Both new regressions fail before the correction. The mapper assertion reports
`left: None`, `right: Some(128)` at mode 0, banks 0/1, address $2000.
The completed CPU guest reports `left: 0`, `right: 133` at mode 0, PPU
address $2000: inspection returns empty CIRAM while PPUDATA returns $85.

After sharing the existing mapping through the read-only hook, both pass.
The mapper regression covers 49,152 live/peek comparisons (four modes,
three bank pairs, 4,096 addresses), rejected ROM writes and 49,152 disabled
mode checks. The machine regression covers 32 actual guest reads over four
modes, including tile and attribute bytes, with a required completion marker
and nonzero data that distinguishes ROM from empty CIRAM.

Local parser and machine test commands report 126 passes, zero failures and
133 ignored tests. The two new tests execute without fixtures or skip paths.
Affected all-target Clippy with `-D warnings` and workspace formatting pass.
No claim of running the ignored cartridge corpus is made.

The correction is source [PR #1731](https://github.com/emu198x/emu198x/pull/1731),
head `e0739e5afa9e9d08a048a5f90e09edc7adbcfeb0`. Required CI is running;
merge and exact-tree verification are not yet claimed.
