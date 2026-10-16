# Producer source-lock qualification

[Emulator PR #1782](https://github.com/emu198x/emu198x/pull/1782), head
`65a449bf14dc91c6736da28d6f306234d377557d`, passed
[candidate run 38873380443](https://github.com/emu198x/emu198x/actions/runs/38873380443).
All 33 applicable PR checks passed; four publication jobs skipped.

| Native target | Independently verified packages |
| --- | ---: |
| aarch64-apple-darwin | 30 |
| x86_64-apple-darwin | 30 |
| aarch64-unknown-linux-gnu | 30 |
| x86_64-unknown-linux-gnu | 30 |
| x86_64-pc-windows-msvc | 30 |

The five target JSON files retain all 150 producer receipts. Each verifier read
the actual uploaded archive, its checksum and executable bytes. Their source
identity matches the independently fetched synthetic merge checkout
`f8b8430ef437ab291015f565cdb1efbcb56da2b8` and its committed lock. This is the
checkout GitHub built, distinct from the PR head. `verification.json` retains
the lock hash, report hashes, job links and step results.

Both Linux jobs completed installation, native CLI loading and uninstallation
for the exact 30-package workspace set. Each package first exercised Homebrew's
rejection of deliberately damaged archive bytes: 60 rejection controls and 60
successful installs across both architectures. Each Linux host also ran the NES
for two frames with a generated cartridge, checked the runtime report and
validated the PNG dimensions. No private firmware was needed by these checks.

The 15 producer/control tests passed locally and on every producer host; the
three existing release Homebrew tests, Ruff and workflow YAML syntax passed
locally. Controls cover missing/empty/changed locks, command failure, omitted
packages, wrong targets/checksums, stale/missing/mutated receipts and publication
dependencies that fail or skip.

The first run stopped Windows packaging with
`producer Cargo.lock differs from checkout commit`. A disposable Git checkout
with `core.autocrlf=true` reproduced 6,216 LF-to-CRLF translations. The narrow
`/Cargo.lock text eol=lf` attribute preserves the committed bytes; a regression
test demonstrates rejection before that attribute and success afterward. The
superseded run was cancelled; the passing candidate includes the correction.

PR signing setup and notarization skipped on both Macs. The release-only
signing/notarization path remains in the workflow; this unsigned candidate does
not qualify Developer ID signing or Gatekeeper behavior. Receipts themselves
are unsigned, and the compiled per-executable dependency/feature graph remains
unknown. Historical release-run checks retain their artifact-only scope.
