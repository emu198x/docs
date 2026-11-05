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
   `@emu198x/player` 0.48.2 provenance/build revision, bundled firmware flag
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

All checks passed (CI run 41996155409). PR #2300 merged at 08:56:59 UTC as
`6366b15babc91e1566a8d2af62885a893885e67c`; the v0.48.1 tag resolves to that
exact commit. Tagged release run: 41998443790. The old main build was
superseded normally by the new main push.

Downloaded the tagged run's Apple silicon Spectrum artifact (artifact
13401184671). Archive SHA-256:
`58ed60d96fe2bb284bfd8fa862232016182c37486204f13b075a529694759114`.
The executable rejects `run_until_pc.max_ticks`, `step.count` and fieldless
`query_cpu.unexpected` with exit 1 and the offending field name. Against a
synthetic NOP ROM, a valid 16-instruction script reports PCs 1 through 16;
the final step and CPU query independently agree on PC `$0010`.

## Player publication prerequisite

While native qualification ran, checked the previous npm failure (run
41662776592, player job 126010123131). The original PET profile was added
without extending `web-player/fixtures.mjs`'s BASIC-ROM selection, so the
full publication parity check supplies 12 KB where the runtime requires
8 KB. The regular CI browser job does not run this full fleet check.

Reproduce the fixture's wrong size for the real four PET profiles; change only
the selection so BASIC 4's 12 KB image serves the two BASIC 4 profiles, and
the existing 8 KB image serves both earlier profiles. Add a regression that
checks actual fixture bytes against each runtime's declared BASIC size,
including the original PET. Run that check in the existing browser CI job,
and retain the complete native/WASM publication parity gate. Cut the next
normal patch release with the checked correction; do not retarget v0.48.1.
The site pin and live verifier must use that resulting published version.

The regression reproduced the exact 12,288/8,192-byte runtime error before
the change, then passed for all four PET profiles. A complete local player
build passed every gate, including native/WASM parity for 85 variants; 52
variants explicitly require additional local firmware. Workflow lint passed.
The correction and regular-CI regression are commit `4bf5fb57d`, on
`fix/player-pet-publication`. Local wasm-pack 0.15.0 reports 0.15.1 available;
no tooling upgrade is part of the fix.

Task-owned build output: `/private/tmp/codex-player-fixture-target`,
`/private/tmp/codex-player-fixture-output`, and its bounded log
`/private/tmp/codex-player-fixture-build.log`. The build's temporary stage in
the pre-existing source `target/` was removed by its `finally` block.

Native v0.48.1 is published (564 assets; publication time 09:29:41 UTC).
Release run 41998443790 finished successfully, including Homebrew publication.
The public Spectrum checksum sidecar matches the tested tag artifact above.
Stopped npm run 42003489432 because it contains the reproduced fixture bug.
PR #2301 holds the checked correction and has rebase auto-merge enabled.
The final player publication therefore targets the next normal patch,
v0.48.2, rather than rebuilding or retargeting either existing tag.

The first PR #2301 browser CI run failed compiling its new native probe:
`failed to run custom build command for libudev-sys v0.1.4`. The formerly
WASM-only job had no native library prerequisites. Added the existing bounded
pkg-config/ALSA/udev installation to that job; local runtime regression,
actionlint and apt-policy self-tests pass. The complete player preflight
already passed with the corrected fixtures; no runtime or fixture change was
needed for this CI prerequisite.

Site prerequisite commit `f4ffdae` passed 140 tests and its full build:
147 routes, browser-module verification, spacing, internal links and prose.
The route update adds 14 positively identified registry board pages and
removes none. Accessibility passed 129 content routes in both themes;
18 redirect stubs were explicitly skipped. This prerequisite is a separate
site PR so it can restore the public build while the player correction runs
through the checked release pipeline. The exact player pin follows later.

Site PR #47 merged with green CI as `87e95be3abb7c69716561108dc1ed13358a7899a`.
Deployment run 42005542019 passed. Verified the live CA018087 board page,
BIOS rights note, redirect from `/systems/atari-5200/`, v0.48.1 download URLs
and the exact recaptured PNG bytes (SHA-256
`b4b4240a2c59ca245e84da35ac4eac6ecb7cf92ae91c59ce106a5d59474a92c3`).
The live player remains 0.44.2 pending qualified npm publication. Reused the
same isolated worktree on branch `fix/published-player-pin` from the merged
site main; no package pin has been changed prematurely.

PR #2301 passed CI run 42003869842 and merged as
`7ca5fff3578182345d07fbcd5f18a35d39bc4ba2`. The browser job's log positively
shows all four PET profiles passing the new runtime fixture check.
Stopped the redundant main packaging run 42006495311; the next tag still
runs the complete native publication qualification. Maintain release run:
42006493986.

Release PR #2302 prepares v0.48.2 at
`18575d9d455f3229862a44759e6fe44d8e090e6d`. Confirmed its only files are
the generated changelog, root manifest and lockfile; all 262 changed lockfile
entries alter only the suite patch version. Rebase auto-merge waits for CI.

Removed the completed local player build cache and output on 2026-11-05;
both paths above are verified absent. `df` available space increased from
104,000,000 to 106,800,000 KiB (about 2.8 GB). Source changes are retained
on main and full preflight results remain recorded here.

PR #2302 passed every check in CI run 42007100070 and merged at
10:19:46 UTC as `79b5fc12ed2b3fb884686600579edad6795c148f`. The v0.48.2
tag resolves to that exact commit. Tagged release run: 42009837730.
Cancelled duplicate main packaging 42009799292 and duplicate main CI
42009799828 after verifying its tree matches the successful PR tree
`48e2d8a0200878a46c66e34384ab90f5f695f770`. The complete tagged
publication qualification remains enabled.
