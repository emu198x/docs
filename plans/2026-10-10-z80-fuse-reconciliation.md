# Reconcile the FUSE exception record

Close source issue #123's remaining documentation gap. The tracked source report
`test-data/fuse-z80-validation.md` already records six precisely constrained
exceptions with die-derived evidence. The local knowledge index still says
five and retains a removed Tom Harte allowlist; the issue body also describes
the wrong fields and observation point. No CPU or harness behaviour changes.

The binding `spectrum-test-oracle-priority.md` decision's 2026-09-24 evidence
update applies: judge the disputed value at the observation point each oracle
actually measures. Do not change CPU behaviour merely to eliminate an exception.

## Tasks and verification

1. Run all FUSE cases using an explicit vendored corpus path, with no case or
   count filter. Record hashes and output. Run the harness's ordinary guard
   tests, including its deliberately rejected mismatch, empty-corpus and
   unmatched-selection controls.
2. Run the existing two integration tests for the disputed repeat flags and
   HALT fetch/NMI return observations. These preserve earlier die-derived
   observations; this task does not rerun the external transistor simulator.
3. Correct the local knowledge index and clarify the chip page from the
   executable values and tracked report. Retain this public evidence record,
   replace the inaccurate issue body with current results and scope, and close
   #123 after the record is merged. Keep the six exceptions unchanged.

## Results

At source revision `fd431e8b0023d3d3725ea3923d36b5439d5424e0`, the full vendored
FUSE 1.7.0 corpus reports **1,350/1,356 exact, six accepted disagreements, zero
unexpected failures**. All eleven ordinary parser, guard and support tests also
pass: 12 Rust tests including the full-corpus test. The two selected integration
tests each pass with one executed test.

The fixture hashes match the existing source report:

| File | SHA-256 |
| --- | --- |
| `tests.in` | `9f36e866f22e72ff1f8bf2100bf70ffbf58edd97b453500aab60acf1f403ebbb` |
| `tests.expected` | `15a6946f4addcf97e137b5bdd1d5fdb08124ff91f1b169f36a8bf4afe4bab6e4` |

The current exceptions, printed by the full run, are:

| Case | Instruction | Observed / FUSE |
| --- | --- | --- |
| `76` | HALT | PC `0001 / 0000` |
| `edb2_1` | INIR | AF `8a00 / 8a0c`; WZ `0001 / 0a41` |
| `edb3_1` | OTIR | AF `3403 / 3417`; WZ `0001 / 02e1` |
| `edb9_2` | CPDR | AF `ffaf / ffa7` |
| `edba_1` | INDR | WZ `0001 / 069e` |
| `edbb_1` | OTDR | AF `0903 / 0917`; WZ `0001 / 033a` |

All five block-repeat fixtures observe a repeating iteration at 21 T-states,
not instruction termination. The AF differences are X/PV for INIR, H/PV for
OTIR and OTDR, and X for CPDR; the accumulator is unchanged. They are not all
X/Y bits, and the record does not establish silicon variability. HALT differs
in its exposed stopped-PC convention.

The existing [source validation report](https://github.com/emu198x/emu198x/blob/main/test-data/fuse-z80-validation.md)
contains the earlier die-derived adjudication and its limits. This task reran
its two local regression tests, not the external simulator. No core behaviour
or allowlist was changed.

Commands:

```sh
env -u EMU198X_FUSE_Z80_CASE -u EMU198X_FUSE_Z80_LIMIT \
  EMU198X_FUSE_Z80_TESTS_DIR=/Users/stevehill/Projects/198x/emulators/zx-spectrum/fuse-1.7.0/z80/tests \
  cargo test --release -p emu198x-zilog-z80 --test z80_fuse -- --include-ignored --nocapture
cargo test --release -p emu198x-zilog-z80 --test integration disputed_repeat_flags_match_die_derived_observations -- --exact --nocapture
cargo test --release -p emu198x-zilog-z80 --test integration halted_fetch_and_nmi_return_use_post_halt_address -- --exact --nocapture
```

The initial invocation incorrectly set `EMU198X_FUSE_Z80_LIMIT` to an empty
string instead of unsetting it. The harness rejected it with
`failed to parse EMU198X_FUSE_Z80_LIMIT='' as usize: cannot parse integer from empty string`
and exit 101. That log is retained separately; it is not counted as a corpus
run. The corrected full run uses `env -u` and records all 1,356 cases.

The negative guard tests require panics when an accepted observed or expected
value changes, when an extra mismatch appears, or when an exception silently
resolves. Empty corpora, zero limits and unmatched selections are also rejected.
Their expected panic output in the successful log demonstrates those controls
execute; it is not an unresolved test failure.

The local knowledge index now records six FUSE exceptions and removes the stale
Tom Harte WZ allowlist claim. The chip page records the fresh run and distinguishes
AF from WZ. Both remain local-only under the source repository's docs-site
policy; this record and the existing tracked validation report preserve the
public evidence. Issue #123 can close as a documentation reconciliation, without
claiming perfect Z80 accuracy or removing its justified exceptions.
