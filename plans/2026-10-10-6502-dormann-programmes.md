# First-class Dormann interrupt and decimal programmes

Address source issue #124 in the engineering-frontier validation lane. Reuse
the existing signal-driven CPU and external-fixture harness conventions. No
production CPU behaviour, API, snapshot layout or dependencies change unless a
reproduced defect establishes the need for a separate correction.

## Fixture evidence

- Dormann's canonical source is staged under
  `assets/test-suites/6502/klaus-functional-tests`, revision
  `7954e2dbb49c469ea286070bf46cdd71aeb29e4b`.
- Gopher2600 revision `823f26b152140feccc3be79d9719140c6797e4db` supplies Bruce
  Clark's decimal programme binary/source/listing at
  `hardware/cpu/tests/klaus2m5/decimal_mode/`. It enables A/N/V/Z/C comparisons
  over valid and invalid BCD. Its prose claiming V is disabled is stale; inspect
  the actual binary comparison code. Entry $0200, DONE $024B, ERROR $000B.
- `freewilll/apple2-go` revision
  `5899396fb6d578289eb67b7a83333282cade04c3` supplies the interrupt binary, source
  and listing under `cpu/`. Ignoring whitespace, source differences from
  Dormann are only zero-page origin $0000 instead of $000A and code origin
  $0800 instead of $0400. Feedback remains $BFFC, active-high bits 0/1 for
  IRQ/NMI, no DDR, NMOS decimal-flag preservation. Its image spans 64 KiB.
- The bundled AS65 is a 32-bit Linux executable; the existing container lacks
  `/lib/ld-linux.so.2`. Use the published, pinned binaries rather than adding a
  toolchain dependency. Keep third-party payloads outside the source repo.

## Tasks and verification

1. Capture fixture/source hashes and inspect listing success locations against
   binary bytes. Add a stdlib-only staging script with fixed upstream revisions
   and SHA-256 verification, without changing the downloaded sources or binaries.
2. Add `tests/dormann_programmes.rs` and a strict programme-directory resolver
   in `tests/support/mod.rs`. Tick public CPU pins against RAM. Reflect feedback
   register writes onto IRQ/NMI each cycle. Require the interrupt success loop
   and actual IRQ/NMI activity; require decimal DONE plus ERROR=0 and execution
   of the operand sweep. Bound both runs and reject traps or missing fixtures.
3. Run both programmes. Prove the gates reject disabled feedback and a decimal
   CPU with decimal arithmetic disabled. Add small hermetic guards for false
   success and timeouts if needed. Restore production code exactly if any
   temporary mutation is used.
4. Run core unit tests, existing Dormann functional programme, focused Clippy,
   formatting and test-hygiene checks. Record logs and exact source/fixture
   identities. Update local knowledge and publish a tracked validation report.
5. Commit and submit the bounded change, merge after CI and close #124 only when
   both programmes genuinely pass. Keep a discovered defect open with evidence
   if it cannot be corrected within this design.

## Oracle finding and final gate design

The immediate-feedback run stops at $0B5C after 2,721 cycles. This is the
programme's `unexpected B-flag` assertion in the NMI handler, whose source
explicitly warns it may fail on real NMOS silicon during concurrent BRK/NMI.
The live run records one NMI vector selected after BRK pushed status with B set.
The existing jsbeeb `src/6502.js::brk` likewise keeps the pushed B flag when NMI
redirects a BRK vector. No production CPU correction is justified here.

A controlled 0–12-cycle external-feedback sweep found:

| Feedback delay | Outcome |
| --- | --- |
| 0–4 cycles | Documented B-bit collision, $0B5C, 2,721 cycles |
| 5 cycles | Programme success, $0AF5, 3,016 cycles |
| 6–9 cycles | Earlier IRQ-timeout trap $0834, 197 cycles |
| 10–12 cycles | Earlier IRQ-timeout trap $0834, 78 cycles |

Five cycles is a chosen stimulus for long-form completion, not a claim about a
real peripheral. The final design keeps the immediate/1–4-cycle cases as a
separate gate: it requires this specific trap, the concurrent-test marker and
one NMI vector read following a B-set status push. The five-cycle completion
cannot hide a changed immediate-feedback result.

The negative mutation disabled only NMI vector hijacking in the shared core.
That made the unmodified immediate-feedback programme reach its success loop,
and made our collision gate fail as required. The CPU source was then restored
byte-for-byte; `git diff --exit-code` confirms no production changes. This is
why the original acceptance criterion needs the documented collision caveat:
a nominal programme pass alone could reward less accurate emulation.

## Verified results

Source commit `cf594222f73c60d5a5e5ec49ee09a4aedd1f04d5` is the submitted
change. Its affected files are unchanged from tested commit `ccb953774b96a47cc9897264bec49cea6cb40d00`
after rebasing over the unrelated AY port-B merge; the scoped diff is empty.

- Eight new harness tests pass, including the full decimal and delayed-feedback
  interrupt programmes, all five collision schedules, disconnected feedback,
  binary-only arithmetic, false-success jumps and timeout controls.
- Decimal ERROR=0 after 53,953,825 cycles; exactly 131,072 ADC and 131,072 SBC
  decimal operations execute. Configuration checks A/N/V/Z/C, including invalid
  BCD. The 2A03 negative control fails ERROR=1 after 3,824 cycles.
- Delayed interrupt completion observes six IRQ and six NMI assertions, eleven
  IRQ/BRK vector reads and six NMI vector reads. Disconnected feedback traps
  at $0834 after 78 cycles.
- Existing Dormann functional programme passes at $3469 after 96,241,367 cycles.
- All 39 shared-core unit tests pass; focused Clippy, workspace formatting,
  Ruff and both fixture/ignore hygiene checks pass.
- The staging script successfully downloads and verifies the pinned source,
  listings and binaries. Corrupted bytes fail checksum verification; a different
  existing fixture is rejected without overwriting it or writing other payloads.
  Staging also succeeded at the default asset path. An explicit nonexistent
  directory fails with exit 101 even after the default fixtures are present,
  proving the resolver does not silently substitute the fallback.

Reproduction:

```sh
python3 scripts/prepare-dormann-tests.py --output /private/tmp/dormann-programmes/staged
EMU198X_6502_DORMANN_PROGRAMMES_DIR=/private/tmp/dormann-programmes/staged cargo test --release -p emu198x-mos-6502 --test dormann_programmes -- --include-ignored --nocapture --test-threads=1
cargo test --release -p emu198x-mos-6502 --test dormann_tests run_functional_test -- --exact --ignored --nocapture
cargo test -p emu198x-mos-6502 --lib
cargo clippy -p emu198x-mos-6502 --test dormann_programmes --test dormann_tests --lib -- -D warnings
cargo fmt --all -- --check
ruff check scripts/prepare-dormann-tests.py
ruff format --check scripts/prepare-dormann-tests.py
python3 scripts/check-fixture-guards.py --self-test
python3 scripts/check-ignore-reasons.py --self-test
```

Source implementation: `tests/dormann_programmes.rs`, the programme resolver in
`tests/support/mod.rs`, `scripts/prepare-dormann-tests.py` and
`test-data/6502-dormann-programmes.md`. The local-only MOS 6502 knowledge page and
log now record the completed programme coverage and its limits. No third-party
payloads are added to either source or docs repo.

Full command output and fixture hashes are retained in the adjacent directory.
`probe.log` is the initial unmapped oracle collision; `hijack-mutation.log` is an
intentional negative control. Neither is an unresolved production failure.
The build initially needed a missing test-helper brace and executable permission
on the new Python script; both were corrected before the recorded final checks.

