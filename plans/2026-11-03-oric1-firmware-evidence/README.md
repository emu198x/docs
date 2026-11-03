# Oric firmware correction evidence

The source correction is [PR #2257](https://github.com/emu198x/emu198x/pull/2257).

- `current-main-probe.rs` and `current-main-red.log`: verified BASIC 1.1
  silently satisfies Oric-1 through the old shared resolver; assertion fails.
- `corrected-resolver-probe.rs` and `corrected-resolver.log`: the same
  generic-only directory rejects for Oric-1; Atmos retains it; both original
  author filenames boot to their own banners and Ready.
- `strict-real-rom.log`: both opt-in SHA-256-gated original-ROM tests pass;
  wrong-ROM, one-byte mutation and incorrect STR$ expectation reject.
- `local-suites-and-initial-lint.log`: 81 default affected tests pass;
  initial lint failure identifies a single-element loop introduced while
  narrowing the old generic-fallback test to Atmos. That loop was removed.
- `final-lint.log`: corrected Clippy run passes with warnings denied.
- `identities.json`: full SHA-256 and SHA-1 values. SHA-1 was independently
  checked against MAME's `src/mame/tangerine/oric.cpp` manifest.

The original ROMs come from the Oricutron author's v1.2 Windows distribution.
Archive SHA-256:
`0efcac032645d246b9dc363097a64d97ae5eaab7db6d73d43e5102865f2e4781`.
Firmware bytes are private inputs and are not included here. Production accepts
explicit custom/localised firmware; these exact identities gate reference
regressions only. The resolver probes are diagnostic source copies, not CI
fixture tests: their temporary paths must be supplied locally.
