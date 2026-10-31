# PET correction evidence

Source PR [#2219](https://github.com/emu198x/emu198x/pull/2219) follows the
already approved three-board correction. The prior `pre-split-red.log` and
probe retain the four v4 queue-loss failures; the final v5 regressions pass
for all three boards.

`reference-runs.json` records exact input SHA-256 identities and bounded VICE
3.10 commands. The monitor scripts and losslessly compressed logs retain native CRTC register dumps,
elapsed clocks and typed calculation. VICE's monitor `keybuf` converts host
text to PETSCII; lowercase host `print` produces the intended uppercase PET
command. Emu198x types through actual graphics/business matrix contacts.

| Configuration | Stable native clocks | Active aperture | Comparison |
|---|---:|---:|---|
| 2001N/3032 32K | 16,640 | 320 × 200 | 1,000 identical screen bytes, zero differing pixels |
| 4032, editor 901498-01 | 20,000 | 320 × 200 | 1,000 identical screen bytes, zero differing pixels |
| 8032, editor 901474-04 (`668870…`) | 19,992 | 640 × 250 | 2,000 identical screen bytes, zero differing pixels |

Run `python3 verify_pixels.py` to compare the retained typed captures. The
raw screen dumps are losslessly compressed. The comparison uses fixed active apertures; host colour/palette and presentation
borders differ. The PNGs show Commodore firmware output, reproduced to verify
emulator behaviour. No manufacturer ROMs are included.

`negative-continuation.log.gz` records the expected failure after flipping one
byte in a frozen v5 continuation; the fixture was restored before the green
run. The public source fixtures contain only project-written firmware.

Local verification: 76 tests passed, zero failed, eight external-ROM tests
ignored in the ordinary run; all eight were separately run and passed with
matching original firmware. Strict Clippy/rustdoc, registry, generated status,
fixture-guard and ignore-reason checks passed. The pixel verifier also rejects a single changed active pixel (`pixel-negative.log.gz`). Site tests (130), build and all 100 content routes in both accessibility themes pass. Source CI is green at `ce33008f9`; its rebase merge `7b7128fa3` has the identical source tree. Each owner has seven exclusive passes with no skips. Shared evidence records 421 passes, eight ignored external-input tests and nine recorded fixture skips; the separately staged PET firmware tests all passed. Site PR #40 is merged at `fee043b21`; deployment run 41223861235 passed. The live check verified 114 routes, 88 registry machines, 51 qualified players, all three PET PNG hashes, no PET embeds and the legacy redirect. See `live-verification.json`.

The former failed hybrid/prototype evidence remains in the neighbouring
2026-10-11 plan directory. No firmware-test wait was extended to hide that
failure. All three corrected boards reach READY within the existing 120-frame
budget. Wider PET family work remains open in #355.


The additional `firmware_restore_probe.rs.txt` was run as a temporary test
module in `runtime-commodore-pet`, then removed with a clean source diff.
Its log retains 12 original-ROM cases: all three boards at 3, 137, 500,000
and 700,000 instructions from reset. Each compares the first three resumed
framebuffer/audio/clock tuples and complete state, then checks that reset is
byte-identical to a fresh machine with those ROMs. All cases passed. This
external-input probe supplements the permanent fixture-free CI regressions;
it is not counted among the 76 normal source tests.
