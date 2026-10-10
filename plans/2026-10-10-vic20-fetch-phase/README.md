# VIC-I fetch phases from physical timing dumps

The origin-plus-four, alternating matrix/glyph schedule explains all 1,340
active-fetch samples in the four physical dumps. Retaining the CPU operand
when idle additionally explains all idle samples in the 6561E and 6560-101
captures. Their complete 1,024-byte open-bus comparison has zero differences.
The other two captures have 354 unexplained idle samples, all `$20`.

This is a diagnostic reconstruction of the fixed timing guest, not a chip
implementation. `analyse.py` asserts the captured register configuration;
its row/address arithmetic must not replace a live hardware state machine.
The [plan](../2026-10-10-vic20-open-bus.md) records the proposed stage design
and the approval needed for its snapshot change.

`trace.patch` adds observational logging at the actual CPU data-read phase.
It was applied to source commit `74856f8f7526c9473a94ccd1798204fcd76ed83e`,
used for the capture, then removed. The clean source file is byte-identical
to its pre-instrumentation version. Both completed emulated result buffers
are byte-identical to the previous open-bus baseline.

To reproduce in a clean source checkout of that commit:

```sh
git apply /path/to/trace.patch
VIC20_FETCH_TRACE=1 EMU198X_STRICT_FIXTURES=1 \
  VIC20_TIMING_OUT=/private/tmp/vic20-traced-new \
  cargo test -p machine-commodore-vic-20 --release --test vici_vice_survey \
  survey_timing_measurements -- --ignored --nocapture > /private/tmp/vic20-trace-new.log 2>&1
git apply -R /path/to/trace.patch
```

Check the test exit status before reversing the patch. The test must finish;
the analyser rejects missing or duplicated samples. `trace.log.gz` retains
all 2,048 data reads, their master-clock positions, registers and guest RAM.
It also retains the original diagnostic's completion and control results.

From this evidence directory:

```sh
python3 analyse.py --trace trace.log.gz --output /private/tmp/vic20-phase-new.json
```

The optional `--testbench` argument changes the external fixture root. All
four physical input hashes are checked. `phase-comparison.json.gz` retains
every disagreement for the reference phase and its one-cycle-early/late
negative controls; `phase-summary.log` contains the counts. The script
asserts that wrong phases fail and that the reference phase agrees for both
complete retained-operand captures. No input samples are normalized away.

The original Commodore technical manual scan is cited and hashed in the
private primary observation note. The PDF and rendered inspection pages are
not copied into this public evidence repository. `sha256.json` covers all
retained files here.
