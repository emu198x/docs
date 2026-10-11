# Four-screen nametable probes

Sixteen complete CPU guests demonstrate four panics and four lost-nametable
results in Emu198x. All eight ordinary mirroring controls pass. The local Mesen
core completes all sixteen cases with the expected data, identically on a
second run. This is executable reference evidence, not a new hardware capture.

## Cases and observations

The matrix covers mapper 0 and mapper 4, iNES and NES 2.0, the four-screen flag
clear/set, and $A000 writes 0/1. Each original guest waits for the PPU to accept
writes, sets the mapper register, writes $11/$22/$33/$44 to the four nametable
page starts, then reads them back through buffered $2007 reads. A required
$A5 completion marker distinguishes a finished guest from startup RAM.

- Four-screen NROM: the accepted header reaches the PPU, which panics on the
  third page: `index out of bounds: the len is 2048 but the index is 2048`.
- Four-screen MMC3: the parser retains the flag in its header but constructs
  an ordinary MMC3. Results are `$33,$44,$33,$44` after mirroring write 0,
  and `$22,$22,$44,$44` after write 1. The four independent expected bytes
  are `$11,$22,$33,$44`.
- Unflagged controls: both kinds of ordinary aliasing return the expected
  final bytes. NROM ignores $A000; MMC3 changes between the two layouts.

The synthetic NROM case proves a crash in an accepted image; it does not
identify a retail NROM board. The MMC3 case directly checks the independent
four-page configuration and its immunity to the mirroring register.

## Files

- `probe.rs`, `baseline.txt`, `panics.log`: initial public parser/PPU probe.
- `build_roms.py`: original 6502 programs and sixteen synthetic cartridges.
- `guest.rs`: full Emu198x machine host, reporting data or the captured panic.
- `reference_guest.cpp`: full Mesen CPU/PPU/mapper host using the real C API
  definitions, without modifying the reference source.
- `compare.py`: complete-case, repeatability and control checks. It rejects
  a deliberately modified reference image with the four-screen flag cleared.
- `guest-results.json`: initial complete capture, source identity and binary
  provenance; `comparison.json`: independently rerun comparison and negative
  control. ROM hashes in the first capture must match a rebuilt corpus.

Source head: `e0739e5afa9e9d08a048a5f90e09edc7adbcfeb0` (the tested Sunsoft-4
correction, whose merge has the same tree). Mesen source beside the local core:
`fabc9a62174f8734a113df6d244f5539ef6b8fcf`. The prebuilt core was not rebuilt
for this probe, so its binary SHA-256 is recorded separately:
`281ed37fcd1421eef1c5e60e06f1ede360ee89ee214a9c2a0c7c128376395c68`.

## Reproduce

Build the NES machine and parser in the named source checkout. With the same
Rust toolchain, set `NES_DEPS` to its `debug/deps`, `INES_RLIB` to the one
fresh parser `.rlib` and `NES_RLIB` to the one fresh machine `.rlib`:

```sh
rustc --edition=2024 guest.rs -L "dependency=$NES_DEPS" \
  --extern "format_nintendo_nes_ines=$INES_RLIB" \
  --extern "machine_nintendo_nes=$NES_RLIB" -o /tmp/four-screen-guest
python3 build_roms.py /tmp/four-screen-roms
```

Compile the reference host with clang++ C++20, include directories at the
Mesen root, `Core` and `Utilities`, and link its compatible `MesenCore.dylib`.
Place a copy of that dylib beside the host; the comparator runs from that
directory to resolve the macOS install name. Then:

```sh
python3 compare.py /tmp/four-screen-guest /path/to/reference_guest \
  /tmp/four-screen-roms /tmp/four-screen-comparison
```

The comparator requires exactly the sixteen distinct cases and all four
bytes per successful observation. A caught Emu198x panic is a reported defect,
not a passing cartridge result. Its successful exit means the capture and
reference controls are valid; read the explicit defect counts.

The original implementations agree on four independent pages: Mesen
`BaseMapper::SetMirroringType(FourScreens)` maps 0/1/2/3 and
`MMC3::UpdateMirroring` leaves that selection alone. ares's TVROM path in
`ares/fc/cartridge/board/hvc-txrom.cpp` routes two additional pages to cartridge
RAM alongside CIRAM. These are implementation precedents, not proof that
every board uses identical RAM chips or wiring. Existing primary context is
`reference/by-system/nintendo-nes/mmc3-reference.md` and `memory-map.md`.

Ruff and Rust formatting checks pass. The corpus, compiled hosts and
third-party binaries are generated locally and are not committed.
