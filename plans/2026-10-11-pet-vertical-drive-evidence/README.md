# PET vertical-drive prototype: wiring passes, firmware gates fail

The prototype is **not ready to merge**. It corrects the wire feeding VIA PB5
and PIA CB1 but exposes the firmware/model mismatch described in the
[board design](../2026-10-11-pet-board-firmware-design.md).

Base: `f7c6b0342e76ab604d7d1a2feb5cc2ee64f067d6`.
`prototype.patch` is the complete uncommitted machine change against that base.
The prototype capture was rerun after its final VIA pin/DDR correction.

- `before.csv.gz` and `prototype.csv.gz`: all 13,912 CPU-guest samples each.
  `python3 verify.py` checks every expected clock in all four cases and rejects
  a dropped sample, wrong VIA level and wrong PIA flag. These expectations use
  the current programmed raster; they establish signal routing, not physical
  PET frame timing.
- `retrace_probe.rs`: original public-API 6502 guest. A loop takes 23 clocks.
  The reported VIA instruction-completion clock follows its bus read by one
  clock; the PIA control read is seven clocks later. The preceding PIA data
  read clears its flag eight clocks before the reported clock. An edge can
  fall between a control read and the following clear, so not every edge must
  be visible in this polling guest. The native-clock unit regression separately
  requires both edge modes to fire.
- `retrace_reference.py`: extracts and compiles the unchanged VICE VIA port
  and PIA signal-routing functions. Generated third-party C stays outside this
  evidence directory. Reference result: 131,072 VIA direction/output cases and
  two PIA levels, zero mismatches. This is not a full VICE timing comparison.
- `retrace-test-before.txt`: the new native-clock regression fails against
  the baseline. `retrace-tests.txt`: 99 focused tests pass, seven ignored.
  `retrace-clippy.txt`: affected-package Clippy succeeds.
- `retrace-firmware-baseline.txt`: all five keyboard tests pass on the clean
  base. `retrace-firmware.txt`: prototype result **2 passed, 3 failed**. The
  command stops on that failure; it does not establish a prototype ROM-boot
  test result. No failed assertion was weakened.
- `firmware_probe.rs` and `firmware-after-trace.txt`: original diagnostic
  showing the startup text still printing at frame 120 and the expected
  `AB C` output at frame 260. That later output is evidence about the hybrid
  configuration, not permission to extend the test delay.
- `installed-fixtures.json` identifies the unchanged local inputs.
  `firmware-downloads.json` identifies original replacement candidates by URL,
  byte count and hashes. No ROM binaries are included in this repository.

To reproduce the polling guest, apply the patch to the base, build
`machine-commodore-pet` in release mode, and compile the standalone Rust source
with edition 2024, `-C lto=thin`, the built library passed through `--extern`,
and its `release/deps` directory passed through `-L dependency`. Capture stdout.
Run the unchanged firmware tests with their fixture directory explicitly set:

```sh
EMU198X_PET_ROMS=/path/to/identified/fixtures cargo test --release \
  -p machine-commodore-pet --test keyboard_type -- --ignored
```

The installed inputs combine BASIC 2 and its non-CRTC graphics editor with a
duplicated BASIC 1 character set. Screen-RAM assertions cannot detect that
glyph mismatch. The matching physical configurations need pixel checks too.
