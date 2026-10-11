# Reproduce NES four-screen nametable loss before choosing storage

This is best-in-class campaign work under mapper coverage issue #92.
Production code is unchanged. A 16-case public parser/PPU probe finds four
panics in accepted NROM images and four aliased MMC3 results; eight ordinary
mirroring controls behave as expected. Both iNES and NES 2.0 are exercised.

The parsed header retains `Mirroring::FourScreen`. NROM forwards it, but the
PPU indexes a 2 KiB array with a four-screen offset: writing $2800 panics at
index 2048. MMC3 construction discards header mirroring, so its four-screen
image continues to use vertical or horizontal mirroring after $A000 writes.

## Investigation steps

1. Preserve `probe.rs`, its complete 16-row output and its panic messages in
   `2026-10-11-nes-four-screen-evidence/`. Check all expected controls and
   failure counts rather than treating a caught panic as success.
2. Generate 16 original cartridges with real CPU programs. Each writes four
   distinct nametable bytes through $2006/$2007 and reads them back after
   selecting the mirroring register. Execute through both complete emulator
   paths. Require completion, all four bytes, eight control rows and a repeat
   reference run; record the local Mesen binary hash.
3. Consult the primary MMC3 register reference and original Mesen/ares board
   code. Distinguish the actual MMC3 four-screen board from a synthetic NROM
   header accepted by our loader. Do not equate every mapper's header bit 3
   with the same physical board wiring.
4. Propose a bounded correction with explicit ownership of cartridge VRAM and
   save-state coverage. Changes to the serialized storage require approval;
   the pending MMC5 ten-bit-latch proposal does not approve this extra state.

## Design boundary

The PPU's internal CIRAM really is 2 KiB. Merely masking a four-screen address
to that capacity would eliminate the panic by preserving the aliasing bug.
The existing mapper nametable read/write/peek hooks can already represent
cartridge-owned memory. Storage placement, supported board scope and snapshot
versioning will be agreed after the complete guest probes.

## Complete guest result

The [evidence bundle](2026-10-11-nes-four-screen-evidence/README.md) contains
the original cartridge generator and both hosts. All sixteen Mesen cases
return the expected four bytes, identically on repeated runs. Emu198x panics
in all four flagged NROM cases and aliases pages in all four flagged MMC3
cases; all eight ordinary mirroring controls pass. The comparator rejects a
negative image whose four-screen bit was deliberately cleared.

## Proposed correction

Keep cartridge memory in the existing concrete mappers, through their
existing nametable read/write/peek hooks. This follows the NES architecture
decision's one-concrete-struct-per-mapper boundary.

1. Add optional four-screen nametable storage to `Nrom` and `Mmc3` in
   `crates/format-nintendo-nes-ines/src/mappers/nrom.rs` and `mmc3.rs`.
   In the flagged configuration, all four independent 1 KiB logical pages
   come from that cartridge-owned store; normalize $3000–$3EFF mirrors.
   Normal configurations continue to use the PPU's existing CIRAM.
2. Retain `Nrom::new`'s existing mirroring parameter. Preserve `Mmc3::new`
   for existing callers and add an explicit four-screen construction path
   used by `src/format.rs` when the header requests it. Hardwired four-screen
   mapping must survive every $A000 mirroring write. Existing unflagged
   MMC3 initialization and programmable mirroring stay unchanged.
3. Serialize the new storage through the existing concrete mapper snapshot
   variants. Advance the NES runtime envelope to its next version (currently
   v2, rejecting v1), with atomic rejection of old saves. Coordinate numbering
   with the separate pending MMC5 proposal; no MMC5 low-bit correction is
   included or implicitly approved here.
4. Add regressions in the parser tests and a dedicated machine guest test,
   exercising all 4,096 bytes, $3000 mirrors, $A000 writes, both header
   formats, unflagged controls and save/restore with different contents in
   every page. Runtime tests prove the extra RAM survives the versioned
   envelope and old saves fail without modifying the running machine.
5. Run affected mapper, PPU, machine and runtime tests, Clippy, formatting and
   exact-head CI before merging. Preserve the source images unchanged.

The alternative is to enlarge the PPU's internal nametable array. That hides
the cartridge ownership and still needs special handling for MMC3's ignored
header flag and mirroring writes. Recommend the existing mapper hooks.
Masking out-of-range addresses is not a valid alternative: the MMC3 probe
already demonstrates why aliased pages lose guest data.

This first correction covers the two reproduced mapper configurations.
Other uses of header bit 3 need their own board-specific audit; the iNES flag
does not have one universal meaning across every mapper. No retail NROM
board identity is asserted by the synthetic accepted-image panic test.

## Approval

Await approval for the additional serialized mapper RAM and versioned NES
saves. AGENTS.md requires agreement for “Breaking changes to APIs or data
schemas”. The original MMC5 question covers a different state change and does
not authorize this one. Investigation and reproducible probes are complete;
production implementation has not begun.
