# Investigate the AY upper-address decoder

Lane: engineering-frontier accuracy. Investigation only; no shared chip,
board, API or snapshot change is approved by this record.

## Measured result

At source `44bdba6c`, all 256 valid-address controls select and write a
register. All 3,840 mismatched-address rows still modify the register file;
3,600 also replace the previously selected register. The probe exits 1.
The row count covers every address byte after every prior selection, not
just one invalid address. It does not measure analog bus voltage or every
chip revision. Of the invalid rows, 3,360 read something other than `0xff`;
this read count is reported separately from the confirmed unwanted writes.

The retained [probe and output](2026-10-10-ay-address-decode/) use only public
core APIs. The primary evidence is the GI manual's address-decoder section;
MAME corroborates the write/latch rule, while the other emulator differences
remain explicit below.

## Question and sources

`Ay3_8910::select_register` unconditionally keeps the low four address bits.
The GI AY-3-8910/8912/8913 data manual, PDF page 2 (printed 5-19), describes
DA7–DA4 as chip-select bits, normally factory-programmed to zero. A wrong
high-order address places the bidirectional bus buffers in high impedance;
a valid address latches the low four bits. The primary PDF and provenance
are under `reference/by-topic/psg-ay-3-8910/`.

MAME `ay8910_device::ay8910_write_ym` compares the high nibble to zero,
preserves the register latch on a mismatch and suppresses data writes.
Its read function returns `0xff` for an inactive chip as a high-impedance
convention. Oricutron also rejects out-of-range addresses, but returns zero
on reads. FUSE and XRoar mask the address to four bits. These implementations
disagree; their behaviour alone does not establish physical read-bus levels.

The manual's [Register Array section](https://cpctech.cpcwiki.de/docs/ay38912/psgspec.htm)
is also available as a searchable transcription. The PDF at
`https://map.grauw.nl/resources/sound/generalinstrument_ay-3-8910.pdf`
was visually inspected; its high-order/low-order diagram agrees with the
prose. Use the manufacturer source rather than inferring a rule by majority
vote among emulator implementations.

## Consumer audit so far

The core feeds the Spectrum 128K/Amstrad classes and Pentagon/Scorpion/Timex,
Oric, CPC, MSX, Spectravideo, Einstein and Aquarius. The MSX and Spectravideo
machines currently use the 8912 facade while declaring 8910 hardware; their
board-level I/O interception must be included in a correction.

In particular, Spectravideo stores another masked PSG address and applies
R15 writes directly to cartridge/RAM banking. Correcting only the shared
register file would leave invalid addresses able to change memory mapping.
MSX/Spectravideo also intercept R14 reads before calling the core. AY watches
are recorded before chip write acceptance in multiple machines. Decide and
test whether each watch describes attempted bus writes or accepted register
writes; do not silently change its meaning.

Current enclosing snapshot versions are Spectrum family 4, Oric 7, CPC 2,
MSX 6, Spectravideo 6, Einstein 6 and Aquarius 4. An added selection latch
requires an explicit version/compatibility decision across these consumers.
The audit is incomplete: chip-variant identity, physical read-bus resolution,
foreign snapshot import/export and all board callbacks still need review.

## Investigation steps

1. Sweep all 256 address bytes from all 16 prior register selections in a
   public-core probe. Separate valid-address controls from mismatched upper
   addresses. Observe register-file writes and retained selection. Compare
   read values separately; do not confuse `0xff` with physical bus drive.
2. Trace each consumer's bus/readback wiring and identify actual GI versus
   Yamaha chips before proposing a shared change. Explicitly distinguish
   chip select, stored register address, bus drive and board pull-ups.
3. Determine the state required to preserve deselection across save/restore.
   Keep existing public register-index semantics; audit snapshot versions
   for every affected runtime. Do not overload a formerly 0–15 serialized
   index silently or let old code index outside the register file.
4. Bring a concrete, bounded design for agreement if new chip state, API
   semantics or snapshot changes are needed. No production fix precedes
   that agreement and the consumer audit.

## Reproduction

From the emulator source repository:

```sh
cargo build --release -p emu198x-gi-ay-3-8910
rustc --edition=2024 -C opt-level=3 -C lto=thin \
  ../docs/plans/2026-10-10-ay-address-decode/probe.rs \
  -L dependency=target/release/deps \
  --extern emu198x_gi_ay_3_8910=target/release/libemu198x_gi_ay_3_8910.rlib \
  -o /private/tmp/ay-address-probe
/private/tmp/ay-address-probe
```

Expected exit on the recorded source: 1. Expected valid-control count: 256;
invalid-address count: 3,840. The probe asserts those counts and fails if
invalid writes change the register file or retained register latch.
