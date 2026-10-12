# Shared BASIC tokenisers — emu198x/emu198x#1542

Lane: Spectrum launch-hardening, with the same dependency correction for C64. The user agreed to replace the emulator's local BASIC tokenisers with the published Format198x crates after the keyboard review.

## Bounded design

Use `format198x-sinclair-zx-spectrum-bas` 0.1.3 and `format198x-commodore-c64-bas` 0.1.1, the current stable registry releases. Remove the two unpublished local leaf crates and their workspace memberships. Update the four consuming Cargo manifests and Rust imports. Keep the loaders, machine clocks and snapshots unchanged.

The Spectrum native loader currently selects the AST analysis tokeniser, while the editable browser selects the listing tokeniser. The native user-source path must also use `tokenise_listing`, as Build198x does, to preserve the ROM's stored representation. Convert the shared crates' structured listing errors at the existing String/loader-error boundaries. Public BASIC program arguments use the published crate's equivalent type as part of this dependency migration.

## Steps and verification

1. Add independent failing regressions before changing production dependencies. In `crates/emu198x-spectrum-web/tests/`, compare the actual exported TAP payload with Format198x's provenance-recorded ROM editor captures. In `crates/runtime-commodore-c64/src/file_loader.rs`, check stored PRG bytes for PRINT shorthand and line 0. Exercise the Spectrum native source-loader path with the real 48K ROM and inspect installed bytes.
2. Change `Cargo.toml`, `Cargo.lock` and manifests for `runtime-sinclair-zx-spectrum`, `runtime-commodore-c64`, `emu198x-spectrum-web`, and `emu198x-spectrum`. Update the affected loader/browser imports and error conversions, then remove `crates/format-sinclair-zx-spectrum-bas` and `crates/format-commodore-c64-bas` after confirming no consumers remain.
3. Run the new regressions and affected crate suites, including actual ROM-backed loader execution. Run formatting, Clippy and native/WASM checks. Compare representative Code198x sample outputs with Build198x where practical; do not assert correctness merely because two consumers import the same crate.
4. Review the diff, commit the bounded correction, prepare its PR and record exact validation. Preserve all unrelated work. The docs checkout at `/private/tmp/198x-basic-docs` is task-owned and must be removed after its commit is safely retained on a verified remote ref.

No chip, CPU or timing implementation changes are in scope. The published tokenisers and their existing ROM captures replace duplicate implementations; no archive port or new tokenising algorithm is needed.

## Results — 12 October 2026

The negative controls reproduce the issue at source base `5d10f595`:

- The browser TAP path disagrees with 10 of 13 captured Spectrum ROM-editor lines. It also accepts `10 PRINT 1 000`, which the ROM refuses.
- The native Spectrum family loader installs 740 bytes for the captured program; the ROM stores 706. It used the AST analysis path, independently of the stale dependency.
- C64 file import stores ASCII `?` (`$3F`) where the ROM stores PRINT (`$99`), and refuses valid line 0 with `Line 1: line number 0 out of range (1–63999)`.
- The live C64 probe first types `0 ?42:POKE 49152,73` through the emulated keyboard. The ROM stores the line, while the old file loader refuses it. This is actual ROM execution in Emu198x, not a physical-machine observation.

The corrected paths pass those controls. Spectrum native loading and the built WASM package both preserve all 706 captured bytes; the browser TAP path matches all thirteen individual captures and refuses the ROM-rejected examples. The C64 file and direct loaders match the independently typed ROM program, including its line links and end marker. Both machines execute a BASIC POKE and produce the expected memory result.

Validation:

- Affected crate suites (`runtime-sinclair-zx-spectrum`, `runtime-commodore-c64`, `emu198x-spectrum-web`, `emu198x-spectrum`): 497 passed, 0 failed, 142 ignored. The two new firmware tests were then explicitly executed, both passed with no skips; this does not claim the other ignored suites ran.
- `cargo clippy` on those crates with `--all-targets -- -D warnings`: passed.
- `cargo fmt --all --check`: passed.
- `cargo check -p emu198x-spectrum-web --target wasm32-unknown-unknown`: passed.
- `scripts/build-npm.sh`: built package 0.4.3 with the existing genuine-ROM hash guard. No package was published during this task. The first sandboxed attempt could not access the tool cache (`Operation not permitted (os error 1)`); the authorised build completed with the same configuration.
- The committed `crates/emu198x-spectrum-web/tests/shared-basic-package.mjs` executes the built WASM package, validates BASIC storage/execution and the assembly launcher, and optionally compares three maintained Code198x tapes with the Build198x executable. Meet BASIC, Sonar and Night Patrol match byte for byte: 63, 3,062 and 11,390 bytes respectively. This is a selected sample comparison, not a whole-curriculum sweep.
- Regenerated `docs/status/current-system-usability.md` to account for the two removed workspace crates. The renderer's `--check` passes for all 30 machines.

Run the artifact comparison after building the npm package:

```sh
node crates/emu198x-spectrum-web/tests/shared-basic-package.mjs \
  /path/to/build198x /path/to/code-samples
```

The native Spectrum loader's existing cold-boot requirement remains: a second call after the banner is gone reports `boot was not detected within 250 frames: copyright banner not visible`. Its execution test uses a fresh machine, matching the browser host's documented usage. This correction does not broaden warm-session loading or 128K-editor support.

The build reports local wasm-pack 0.14.0 with 0.15.0 available. That tool update is outside this correction. Snapshot schemas and chip timing are unchanged. The source PR bumps the npm patch version so merging can publish the corrected package; updating website consumers is subsequent release integration.
