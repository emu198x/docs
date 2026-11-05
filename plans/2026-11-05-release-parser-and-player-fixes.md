# Publish the parser and responsive player fixes

Lane: engineering-frontier release work. Publication and downstream rollout
authorised on 2026-11-05 following merged PRs #2297 and #2298.

1. Verify release PR #2274 includes both fixes and has green checks. Review
   its version/changelog changes, then merge its checked head through the
   normal rebase-only policy. Confirm the resulting v0.48.0 tag and release
   build refer to the merged source.
2. Run `.github/workflows/publish-crates.yml` through its normal publication
   path. Verify the registry's `emu198x-shell` 0.44.3 archive contains strict
   script parsing, rather than trusting only the workflow result.
3. Follow the suite release and `.github/workflows/publish-npm.yml`. Verify
   `@emu198x/player` 0.48.1 provenance/build revision, bundled firmware flag
   and the corrected CSS in the actual published tarball.
4. Update only the exact player pin and lockfile in `emu198x.github.io`, using
   its existing tests/build and browser checks. Commit, push and merge with
   green CI, then verify the deployed A500 page's package revision, document
   width and keyboard-accessible model control. Close #2238 on positive live
   evidence.
5. Record release/package/site references and verification outcomes here.
   Preserve unrelated local work and remove task-owned downloads, browser
   profiles, processes and temporary build output before finishing.

Use the existing release pipelines and pinned npm delivery decision. No site
build compiles Rust, and no copied published bundle is patched.

## Release-runner prerequisites

The first publication attempt exposed missing ALSA development files in
`publish-crates.yml` (`Package 'alsa', required by 'virtual:world', not found`).
The preceding full main release also failed because current Homebrew refuses
to load the generated `198x/package-test` formulae until explicitly trusted.

Fix only these prerequisites: install the existing native build requirements
through `scripts/ci/apt-install.sh`, and authorise each generated test formula
with `brew trust --formula` before exercising it. Retain corrupt-archive
checksum rejection, real installation and package smoke checks. Verify the
Homebrew path with a regression that refuses untrusted formulae, then the real
Linux installer jobs. Use a new patch release for the corrected pipeline;
preserve the existing v0.48.0 tag.

## Evidence so far

- Release PR #2274 merged as `691b4957e7dd2735bfac3e3374297d0def37eb3a`;
  Maintain release run 41992835825 tagged that revision v0.48.0. Cancelled
  release runs 41992871034 and 41992837206 before the known installer failure.
- Crate publication run 41992837474 reached Cargo verification and failed on
  the missing ALSA development files. No shell 0.44.3 archive was available
  at the first registry check.
- Prerequisite repair PR #2299 adds the existing ALSA/udev build requirements
  to the publisher and formula-specific trust to the Linux qualification.
  Its regression failed with `Checksum rejection was not exercised:
  Refusing to load formula from untrusted tap` before the change, then passed
  with independently checked corrupt and original HTTP archive bytes.
  Ruff, actionlint and the apt-workflow self-test passed locally.
- Real Linux qualification run 41993564348 checks both ARM and x86-64 release
  packages from run 41908017868 using the repaired installer path.

## Site rollout prerequisite

The unmodified site's tests fail on the source registry's generated
`0 (board tests in [emu198x/apple-ii](https://github.com/emu198x/apple-ii))`
crate-count cell. Before updating the package pin, adapt only
`src/lib/evidence.js` to accept this precise annotated integer form. Add
`tests/evidence.test.mjs` coverage for the real form and malformed suffixes;
retain rejection of arbitrary non-numeric counts. Run the complete site
tests after `vale sync`, then the normal build and browser checks with the
published package. The isolated workspace is
`/private/tmp/codex-player-release-site`; remove it after its commits are
retained remotely and the deployment is verified.

Both Linux jobs passed. The site evidence regression reproduced the original
failure, then the full suite passed (140 tests). A second baseline failure
identified the retired aggregate `atari-5200` capture identity. The source
registry positively names three replacement board owners; recaptured the
original CA018087 with the real macOS ARM package from run 41908017868,
explicit `--board ca018087`, local BIOS and 320 frames. Updated its recipe,
board ID and BIOS rights note; no firmware is committed. The new image shows
the synthetic Emu198x plate. The site build currently stops on the expected
404 for the unpublished v0.48.0 manifest; rerun after v0.48.1 is published.

PR #2299 merged with every required check green as `b232e0484`. Crate
publication run 41995863155 succeeded. Downloaded shell 0.44.3 directly from
crates.io; SHA-256 `aee922fed362c3818ef37316d5f7f20e6c7650aca18916d32b6a91887dd21ba0`
matches the registry, and `src/script.rs` contains both unknown-field denial
and the fieldless-action deserializer. Registry publication time:
2026-11-05 08:38:27 UTC.

Release PR #2300 prepares v0.48.1 at
`cd7901deaf43876d1d2f9de27f757a84ce271429`. Verified all 262 changed lockfile
entries change only the workspace version, retaining dependencies and
checksums. The only other changes are the root suite version and generated
changelog. Rebase auto-merge waits for the required checks.
