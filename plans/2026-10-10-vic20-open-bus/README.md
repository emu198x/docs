# VIC-20 open-bus measurement evidence

All 512 open-bus samples disagree with each corresponding hardware dump.
The two raster-register columns agree exactly. The [plan](../2026-10-10-vic20-open-bus.md)
records the source analysis, physical-machine differences and next investigation.
This is measurement evidence, not a completed accuracy correction.

`emulated-{pal,ntsc}.bin` and `native-{pal,ntsc}.bin` contain the complete
1,088-byte `$17C0`–`$1BFF` buffer without a PRG header. The compressed JSON
files list every differing offset and byte. Original physical dumps remain
external fixtures; the diagnostic pins their identities. `verified.log.gz`
records the completed diagnostic; `negative.log.gz` records its failure after
temporarily XORing the first raster sample with one. That mutation was removed
before the verified run. No fixture was changed.

Run from the emulator source repository, using a new output directory:

```sh
EMU198X_STRICT_FIXTURES=1 VIC20_TIMING_OUT=/private/tmp/vic20-timing-new \
  cargo test -p machine-commodore-vic-20 --release --test vici_vice_survey \
  survey_timing_measurements -- --ignored --nocapture
```

The existing survey fixture and ROM environment variables are supported.
The diagnostic requires both guest completion and a passing stability guard;
it asserts the raster control bytes and reports the unresolved open-bus bytes.
Its green result does not mean those bytes agree.

From this directory, with native VICE installed:

```sh
python3 capture.py --output /private/tmp/vic20-native-new
python3 compare.py --emulated /private/tmp/vic20-timing-new \
  --native /private/tmp/vic20-native-new --output /private/tmp/vic20-comparison-new.json
```

Both scripts accept `--testbench`; the capture also accepts `--roms` and
`--xvic`. Native capture stops when the guest writes its passing stability
result, saves the full buffer, checks completion and length, and records its
command and log. A second capture reproduced both byte arrays exactly.

`failed-monitor-setup.log.gz` is the discarded first capture attempt. VICE
reused checkpoint 1 after deletion, but the script assigned the save command
to checkpoint 2. It reached the cycle limit without producing a measurement;
the corrected script and verified captures are retained here.

The private primary observation note is
`198x/reference/by-system/commodore-vic20/2026-open-bus-measurement-observations.md`.
Its provenance is the staged upstream README, not a new physical experiment.
`sha256.json` covers the retained evidence files.
