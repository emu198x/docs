# Native original-firmware evidence

**Qualification, 2026-11-03:** the PAL 1.3 images below already contain the
complete disk/hand graphic. Their white-screen interpretation came from the
inspection viewer and is disproven by native/captured/decoded-pixel agreement.
See [the qualification and strict regressions](../2026-11-03-board-qualification-batch.md).
The original captures and receipts remain unchanged; the older negative
interpretation below is historical.

The new captures use the working tree committed as source `015808f53` (PR #2236).
`fixed_ocs_boot_capture` runs complete native fields through the shared session,
checks RGBA framing, writes unaltered PNGs and records input/output SHA-256,
actual RAM and field counts. No ROM/disk contents are distributed. Native
screens were visually inspected; completing a run alone is not a boot claim.

| Fixed owners | Firmware | Actual RAM | Observation |
|---|---|---|---|
| A1000 PAL/NTSC | Original bootstrap and Kickstart 1.2 disk | 256 KiB chip | Original CPU disk loader reaches WOM handoff at fields 1388/1655. Eject at handoff; the 2600-field captures show the 1.2 insert-disk screen. |
| A500 rev 5 PAL/NTSC | Kickstart 1.3 | 512 KiB chip | Insert-disk screen at 650 fields. |
| A500 rev 6a PAL/NTSC | Kickstart 2.04 r37.175 | 512 KiB chip | Insert-disk screen at 650 fields; stock RAM selected explicitly rather than the legacy modified/maxed preset. |
| A2000CR rev 6 PAL/NTSC | Kickstart 2.04 r37.175 | 1 MiB chip | Insert-disk screen at 650 fields. |

The additional 1.3 tests distinguish firmware combinations: both NTSC mixed
boards reach the screen; both PAL mixed boards remain white at 650 fields.
The PAL failure was independently reproduced on the unchanged original engine
at evidence tag `evidence/amiga-ocs-v67-original-baseline` (`0e480f619`, whose
production source is `c06321677`). Only an untracked capture example was added;
tracked production files remain untouched. `before-extraction-capture.rs`
retains that helper. Both complete RGBA hashes equal the extracted engine's
`f28bfeb54f3397f7983077641057b561e150627267c133eaeafbd7552624d436`.
This is a preserved compatibility gap, not a new boot qualification or a
claimed explanation of the mechanism. Keep the negative images and receipts.

`native-manifest.json` joins every receipt to its source and input/output
identities. All PNGs remain raw, including the NTSC canvas's unused lower
rows and border samples. No crop, replacement golden or tolerance conceals a
failure. These observations do not qualify Workbench, every PCB population,
Buster/Zorro backplanes, host menus/audio devices or broader software coverage.
