# Correct PET CRTC port routing and establish status timing

Lane: engineering-frontier accuracy. Investigation follows the merged 6845
register-mask correction, source PR #1737. No PET production correction has
been merged yet. A vertical-drive prototype has exposed a firmware/model
mismatch; its [evidence](2026-10-11-pet-vertical-drive-evidence/) and
[proposed correction](2026-10-11-pet-board-firmware-design.md) are retained
separately. The data/status-port fault below remains unfixed.

## Confirmed fault

In `crates/machine-commodore-pet/src/lib.rs`, writes use `$E880` for the CRTC
register selector and `$E881` for data, but reads return selected-register data
at `$E880` and `$FF` at `$E881`.

An original 6502 guest selects R15, writes each possible byte, reads both ports,
and stores the results in ordinary RAM. All 512 guests complete across the
40- and 80-column profiles. **510 selected-data reads fail**. The two `$FF`
controls pass because that value matches the erroneous constant. This uses
CPU-executed `LDA`/`STA`, not debugger peeks of the I/O decoder. Debugger reads
only collect the guest's RAM results.

Baseline source is `34d793f52d33275b0edfda428adf0a4582e1cb52`; merged source
`f7c6b0342e76ab604d7d1a2feb5cc2ee64f067d6` has the identical complete tree.
The original source, full capture and completion checks are in
[`2026-10-11-pet-crtc-port-evidence/`](2026-10-11-pet-crtc-port-evidence/).

## Primary evidence and reference boundary

- Commodore schematic **8032029**, revision F, sheet 10: buffered A0 connects
  to CRTC RS, and buffered R/W connects to its R/W pin. Sheet 1 supplies the
  page decode. [Manufacturer scans](https://www.zimmers.net/anonftp/pub/cbm/schematics/computers/pet/8032/index.html).
- Commodore MOS Technology **6545-1 CRT Controller**, November 1981 preliminary,
  page 6: RS low writes the selector and reads status; RS high accesses the
  selected register. Page 9 marks cursor R14/R15 readable and writable.
  [Manufacturer scan archive](https://www.zimmers.net/anonftp/pub/cbm/documents/chipdata/6545/c6545.zip).
- The same datasheet, pages 7–8: status bit 5 means vertical blanking, with
  VSYNC shown as a shorter interval. Bit 6 latches a light-pen strobe and clears
  on an R16/R17 read. Page 7 calls bit 7 unused, while page 9 labels it U; this
  preliminary-document inconsistency remains explicit.
- VICE `src/pet/petmem.c` decodes selected I/O chips, including simultaneous
  selects, then calls `src/crtc/crtc-mem.c::crtc_read`. That function separates
  even status from odd register-data accesses, confirming the port fault.
  Its light-pen readback and status bits 6/7 are marked incomplete.
- **Do not copy VICE's status timing without resolving its source.** Its
  `crtc_read` returns `crtc_offscreen()` in bit 5. `crtc.c` derives that field
  from VSYNC for CRTC retrace mode and video enable for the other mode. This
  does not itself prove the manufacturer's status-bit waveform. MAME's
  `mc6845_device::status_r` instead uses the vertical line-enable latch.

## Work and verification

1. Trace the supported 4032/8032 board decoders and retrace wiring, including
   the VIA input. Read the model configuration selecting VICE's retrace mode.
   Keep CPU status, external sync and vertical blanking distinct.
2. Extend the original guest to sweep isolated CRTC address aliases, R14/R15
   selection/readback and status at known raster positions. Use whole-frame
   coverage and nonzero controls. Extract unchanged reference stages where
   practical; record conflicts against the primary documents.
3. Write the bounded correction design from those results. Prefer the existing
   chip and machine stages. If a true MOS personality, new saved state or
   breaking API is needed, obtain agreement for that concrete change before
   implementation. Do not relabel MC6845 as a complete MOS 6545 model.
4. Add regressions in `crates/machine-commodore-pet/tests/crtc_ports.rs`, prove
   they fail before production edits, then correct
   `crates/machine-commodore-pet/src/lib.rs` and any evidenced shared-chip
   behaviour in `crates/motorola-6845/src/lib.rs`. Keep unrelated PIA/IEEE work
   separate, but document simultaneous-select cases that depend on it.
5. Run the unchanged guest sweep, chip and PET tests, PET firmware boot and
   affected-package Clippy. Any shared-chip timing change also requires the
   BBC/CPC regressions and firmware checks. Verify save/reload at each new
   phase if a phase is introduced. Publish results and update current chip/
   machine documentation only after the verified correction.

This investigation does not close issue #166 (interlace/skew), #349 (the second
PIA) or #355 (additional PET models). It must not be presented as a complete
6545 implementation.
