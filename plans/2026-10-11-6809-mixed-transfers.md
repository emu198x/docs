# MC6809 mixed-width transfer correction

Issue: https://github.com/emu198x/emu198x/issues/131

## Evidence and bounded design

Current `bc78410f` substitutes constant all-ones values whenever the two named
registers have different widths. Ciaran Anscomb's original Dragon observations
and Tim Lindner's 2022 real-CoCo-2B test image contradict that convention.
The vendored XRoar `src/mc6809/mc6809.c` agrees with the observed asymmetry:
A/B source words have high byte FF; CC/DP source words replicate the byte;
a byte register on the right side of EXG returns its byte with high byte FF.
Word-to-byte writes keep the low byte. EXG captures both values before writing
the right destination, then the left; D/A/B aliasing makes that order visible.

This is an existing instruction semantic correction. Change only the existing
register-read/exchange helpers, retaining the public pins, instruction stages,
six/eight-cycle schedules and snapshot layout. Undefined register selectors and
unrelated illegal opcodes remain outside #131. No new dependency or architecture.

## Steps and verification

1. Pin the original publication, downloaded test package/image identities and
   XRoar source in a primary observation note. Inspect the test source against
   the real-hardware image; do not treat a reference model as physical evidence.
2. In an isolated source checkout, add `motorola-6809` regression vectors for
   mixed named registers, CC/DP directionality and D/A/B aliases. Run through
   the public bus pins and preserve six/eight-cycle completion checks. Capture
   the old core failing before changing production.
3. Compile the relevant unchanged XRoar register-transfer switch bodies in an
   isolated diagnostic wrapper to generate value vectors for all 100 named
   register pairs for both instructions with distinct register seeds. This
   validates values/order, not bus-cycle timing; retain the wrapper and hashes
   in this plan's evidence directory. Add the resulting independent fixtures
   to `crates/motorola-6809/tests/data/` and execute them through CPU ticks.
4. Correct `crates/motorola-6809/src/lib.rs`; run chip and Dragon machine tests,
   formatting and Clippy. Check no state field changes. Commit, open a PR with
   the reproduced failure and evidence limits, and merge after required CI.
5. Close #131 only after the named mixed-width transfer behaviour is corrected
   and verified. Keep other undocumented-selector behaviour separate.

Sources:
- https://www.6809.org.uk/dragon/illegal-opcodes.shtml
- https://tlindner.macmess.org/?p=945
- https://tlindner.macmess.org/wp-content/uploads/2022/11/Test-Exg-TFR.zip
- XRoar vendored MC6809 implementation, EXG/TFR cases.

## Results

The original core failed 339 of the 800 compiled-reference vectors. The failing
run executed the complete matrix before reporting the mismatches; its first
failure is retained in [matrix-red.log](2026-10-11-6809-mixed-transfers/matrix-red.log).
The corrected helper passes all 800, including 384 mixed-width cases and 416
same-width controls. Separate public-pin tests reproduce the CoCo image's
CC/DP direction and D/A/B alias results.

Validation completed locally:

- `cargo test -p motorola-6809 -p machine-dragon-32`: 90 CPU tests,
  75 machine unit tests and 2 Dragon BASIC integration tests pass; none ignored.
- `cargo clippy -p motorola-6809 -p machine-dragon-32 --all-targets -- -D warnings`:
  pass.
- The fixture checks six/eight cycles and next-opcode fetch pins for every case.
  This preserves the existing timing contract; it does not claim a new physical
  bus-timing comparison.
- Only register-value helpers changed in production. No state fields, snapshot
  versions, public APIs, instruction scheduling or dependencies changed.

Reproduce the reference vectors with an unchanged XRoar source matching the
SHA-256 in [provenance.json](2026-10-11-6809-mixed-transfers/provenance.json):

```sh
python3 plans/2026-10-11-6809-mixed-transfers/reference_vectors.py \
  --source /path/to/xroar/src/mc6809/mc6809.c --output /tmp/6809-reference
```

The output directory must not exist. The generator compiles the reference
switch bodies and records source, wrapper and vector hashes in `reference.json`.
Compare those hashes with the [recorded result](2026-10-11-6809-mixed-transfers/reference.json).
The GPL reference source stays external; the committed fixture is register data.
