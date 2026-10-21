# Plan: independent releases from system-family repositories

**Date:** 2026-10-21

**Status:** Planning only. The family boundary is agreed; migration and publication are not authorised by this plan.

**Lane:** Engineering-frontier work — repository ownership and release infrastructure.

We will plan around one repository per system family, with variants together.
Each family will release independently and adopt released shared dependencies
through explicit updates. The existing `emu198x/emu198x` repository is the
proposed home for shared hardware and host infrastructure during migration.

The reason is independent product versioning. We expect shared interfaces to
change less as they settle. A shared CPU or shell release should be available
to each emulator without requiring every emulator to adopt and ship it together.

This document defines the proposed migration, its checks and its stopping points.
It changes no current release policy, repository ownership or executable code.
Names, the pilot and the rollout order below are recommendations for review.

## Agreed intent and proposed details

Agreed in the planning discussion:

- One repository per system family; no repository per variant.
- Independent family versions and releases.
- Shared fixes reach families through explicit dependency updates and validation.
- The shell is normally unchanged by system work; significant shared changes
  remain possible.

Proposed implementation:

- Retain the flagship as the shared workspace, without renaming it during the pilot.
- Keep family-only chips, machines, formats, runtimes, binaries, tests and
  codebase-tied knowledge with their family, except existing independently
  published libraries, whose ownership stays intact initially.
- Publish only the library surfaces needed across repository boundaries. Internal
  family crates can remain unpublished and share their family's version.
- Keep aggregate consumers in the flagship initially. They may depend on families;
  shared libraries must not. Separate aggregate test/release jobs make that
  distinction explicit, even while they occupy one repository.
- Trial the model with Dragon before choosing a second family.

## Binding decisions to revise before implementation

The current records bind execution until their amendments land through checked
PRs. Agreement to plan is not permission to silently disregard them.

| Record | Required amendment |
|---|---|
| Source `knowledge/decisions/workspace-shape.md` | Replace the unified-workspace default for family products with staged extraction for independent releases. Record that reduced interface churn is an assumption to test. |
| Source `knowledge/decisions/versioning-strategy.md` | Replace the requirement that native binaries remain in suite lockstep forever. Preserve independent library versions and avoid per-crate versions for family internals. |
| Source `knowledge/decisions/releases-are-cut-from-commits-not-packages.md` | Scope the existing suite mechanism to the remaining suite during transition; specify the first family's commit-based release scope. Do not reintroduce release-plz merely to perform extraction. |
| Source `knowledge/decisions/versioning-milestones.md` | Apply the existing 0.x binary policy per family; preserve library API-stability criteria. |
| Umbrella `decisions/project-skeleton-standard.md` | Record the independent-release reason for extraction and correct its stale claim that Emu198x already releases machines independently. This is not a split for symmetry. |
| Source `knowledge/decisions/the-guards-apply-to-the-only-committer.md` | Preserve required checks for owners. Explain that this split addresses release ownership, rather than missed failures; use the newer rebase-only merge policy. |

The new Emu198x-specific decision belongs in source
`knowledge/decisions/system-family-repositories.md`. Cross-project repo-map and
skeleton changes belong at the umbrella. Keep the master plan here in the docs
repository; link to it from the decision.

## Evidence at the planning baseline

Source checkout: `530f66d06d9b0faa8bfcc03efc87d7d236db1403`.

The [dependency inventory](2026-10-21-system-family-repositories/dependencies.tsv)
records the root's explicit members and their recursively reachable local path
dependencies. It includes normal, dev, build, optional and target-specific edges.
An absent field is written as `-`. It is a declared graph, not evidence of which
features are compiled into a binary.
Registry dependencies and non-Cargo imports need separate execution-time audits.

The root manifest lists 232 explicit members. Walking local paths also finds
`format-commodore-vic-20-crt`, which is not in that list. An extraction inventory
must follow edges rather than assume the list is complete.

Seven manifests allow registry publication at this revision; that does not prove
their versions have been published. Most shared crates, including shell and UI,
still say `publish = false`. Publication readiness is work, not a directory move.

Within the latest 200 commits ending at this baseline, 12 touched
`crates/emu198x-shell` and 15 touched `crates/emu198x-ui`. These counts establish
ongoing changes, not API breakage or a trend. Before extraction, classify those
changes by public contract and affected consumers. Do not claim stability from
the counts alone.

Observed seams requiring explicit treatment:

| Current surface | Migration consequence |
|---|---|
| `crates/emu198x-fleet-web/Cargo.toml` | Selects 30 fleet family features and directly consumes their runtimes; its self dev-dependency enables every family. It needs released family runtimes and an explicit aggregate test matrix. |
| `crates/emu198x-web/Cargo.toml` | Generic production code, but a Spectrum runtime dev-dependency. Move that real-machine parity test to integration ownership before Spectrum extraction; preserve it. |
| `crates/emu198x-commodore-web/Cargo.toml` | Combines C64 and Amiga, including a direct Amiga machine dependency. Treat it as an aggregate consumer until its public compatibility surface is mapped. |
| `crates/emu198x-apple/Cargo.toml`, `apple/`, `scripts/build-apple-xcframework.sh` | Apple bridge consumes the fleet crate. Preserve its ABI, packaging and existing build checks. This is a host frontend, not an Apple computer family. |
| `web-player/families.json`, `web-player/build-npm.sh`, `.github/workflows/publish-npm.yml` | Player catalogue and npm release ownership must follow actual family versions. Preserve existing npm names and firmware policy. |
| `scripts/source_lock.py`, `scripts/test_source_lock.py`, `.github/workflows/qualify-packages.yml` | Native receipts discover the suite from source manifests. Re-scope that discovery per producer without weakening omission or lock-mutation failures. |
| `docs/status/systems.toml`, `scripts/status/`, `scripts/check-help-lists-flags.py` | Status and fleet checks currently assume local crates. Give them an explicit source/package inventory; absence of an extracted crate is not retirement of its system. |

To reproduce the manifest inventory with Python 3.13 or later, from the umbrella:

```sh
python3 Emu198x/docs/plans/2026-10-21-system-family-repositories/inventory.py Emu198x/emu198x --check
```

After an intentional baseline change, run without `--check` and review both the
TSV and `source-commit.txt`. The checker rejects a changed source revision even
if its manifests happen to match. The inventory is not a release manifest.

## Repository and package ownership

Proposed repository slugs use the existing family identifiers where practical.
The table covers every current fleet feature. A row is an ownership proposal,
not a claim that all models of that family are implemented.

| Proposed repository under `emu198x/` | Current fleet feature(s) |
|---|---|
| `sinclair-zx-spectrum` | `sinclair-zx-spectrum`, including existing Spectrum variants and clones |
| `commodore-amiga` | `commodore-amiga`, with OCS, ECS and A1200 implementations together |
| `commodore-c64` | `commodore-c64`, with its drive machines initially |
| `nintendo-game-boy` | `nintendo-game-boy` |
| `nintendo-nes` | `nintendo-nes` |
| `dragon` | `dragon`, keeping 32/64 together |
| `amstrad-cpc` | `amstrad-cpc` |
| `acorn-bbc-micro` | `acorn-bbc-micro` |
| `acorn-electron` | `acorn-electron` |
| `acorn-atom` | `acorn-atom` |
| `atari-2600` | `atari-2600` |
| `atari-5200` | `atari-5200` |
| `atari-7800` | `atari-7800` |
| `atari-8bit` | `atari-800xl` |
| `commodore-pet` | `commodore-pet` |
| `commodore-vic-20` | `commodore-vic-20` |
| `coleco-colecovision` | `coleco-colecovision` |
| `jupiter-ace` | `jupiter-ace` |
| `mattel-aquarius` | `mattel-aquarius` |
| `memotech-mtx` | `memotech-mtx` |
| `msx` | `msx` |
| `oric` | `oric-atmos` |
| `sega-8bit` | `sega-sg-1000`, `sega-master-system`, `sega-game-gear` |
| `sinclair-zx80-zx81` | `sinclair-zx80`, `sinclair-zx81` |
| `sord-m5` | `sord-m5` |
| `spectravideo-svi` | `spectravideo-svi-328` |
| `tatung-einstein` | `tatung-einstein` |

Sega's shared runtime and the ZX80/ZX81 grouping warrant joint review; these
groupings are proposals. A common manufacturer or CPU alone does not define a
family. BBC/Electron and Atari console boundaries likewise remain reviewable
before their extraction, without reopening the agreed no-per-variant rule.

For each extraction, produce an explicit move/retain table covering every crate
in its dependency closure and every incoming consumer. No dependency is assigned
by name alone. A family-only component follows its family; a component with
actual consumers in different families stays shared. Existing published chips
keep their package identities and versions even if only one family uses them.

Standalone format ownership still follows the umbrella graduation decision.
Do not create parallel parsers or move all formats to Format198x as a side
effect. Identify the applicable owner for each crossing format before publishing.

Published package names must carry their org prefix, preserving category words:
for example `runtime-dragon` would publish as `emu198x-runtime-dragon`. Internal
names need not change. Existing published names remain intact. Rust dependency
aliases can limit source edits during package renames; verify macro expansion
and `$crate` paths rather than assuming aliases make every rename transparent.

## Versions, adoption and integration

Each family has one binary release version, changelog and `v*` tag namespace in
its own repository. Variants ship together. Proposed initial family version:
continue from its last shipped suite version, with the next appropriate bump;
record the old repository/tag/commit so the lineage is unambiguous. Do not reset
every family to 0.1.0. Existing library versions do not reset.

Publishable family runtime libraries have their own API versions when necessary;
unpublished internals can use the family workspace version. A runtime exists on
the registry only because a real aggregate consumer needs it. The integration
workspace selects released versions; it does not force families to release
together. Its own release describes that selected combination.

For the pilot, exact requirements on direct cross-repository Emu198x libraries,
plus committed consumer lockfiles and `--locked` builds, express deliberate
adoption. This prevents a routine compatible patch refresh from silently
adopting a new direct shared version. Verify the full resolved lock diff too:
an exact direct requirement does not freeze transitive dependencies by itself.
Review this constraint policy after the pilot rather than automatically applying
it to unrelated third-party dependencies.

A shared change is released first. A consumer update PR records old/new versions,
the intended benefit, full lockfile changes and family validation. No automatic
merge or forced fleet-wide bump. A shared bug fix requires a positively enumerated
affected-consumer checklist so independent adoption does not become forgotten
adoption. Compatibility work for a breaking shell release may need several PRs;
families stay on the older release until ready.

Rust type identity is a particular gate: a fleet build must not pass a runtime
implementing one shell version's traits into another incompatible shell version.
The integration consumer must select compatible runtime releases. Independent
native versions do not promise that arbitrary versions can be linked together.
Likewise, moving crates between workspaces changes Cargo feature unification;
check default, minimal/headless, native and browser feature combinations.

Registry releases must build from their published dependency graph without local
path escapes or `[patch]` overrides. Use patches only for bounded development
checks. Detect normal dependency cycles before publication. Dev-only cycles
must be separated into integration tests where packaging or independent CI
requires it; preserve the underlying tests.

## Pilot recommendation: Dragon

Dragon has a compact family entry point and is consumed by the fleet player.
It tests both independent native delivery and downstream runtime adoption.
It is a candidate, not a declaration that its current accuracy gates pass.

Initial move candidates, each under source `crates/`:

- `emu198x-dragon`, `runtime-dragon`, `machine-dragon-32`.
- `format-dragon-bin`, `format-dragon-cas`, `format-dragon-disk`, `format-dragon-pak`.
- `motorola-6809`, `motorola-pia-6821`, `motorola-sam-6883`, `mos-acia-6551`,
  subject to checking non-Cargo consumers and existing publication commitments.

At the recorded baseline, those four hardware crates have only
`machine-dragon-32` as a direct local manifest consumer. The VDG does not:
`motorola-vdg-6847` is used by Dragon and Acorn Atom machines, runtimes and
binaries. Retain it shared. Publish the needed shell/UI/native-video/app-icon
and test-helper dependency closure before switching Dragon to registry inputs.
Recalculate that closure from manifests rather than treating this list as final.

Dragon-specific scripts, fixtures and knowledge follow the family; shared test
data provisioning stays reusable. Audit `include_bytes!`, `include_str!`,
relative paths, subprocess commands and source links beyond Cargo edges.
Firmware/media remain local or in approved corpus storage. No repository move
authorises distributing them.

## Work packages

Each checkbox is a small checked PR or a short sequence of separately verified
PRs. Do not mix extraction with hardware corrections or interface redesign.

### 1. Record the migration contract

- [ ] Refresh the evidence revision and review the shell/UI changes in the
  recorded 200-commit range, separating public API changes from internals.
- [ ] Add source `knowledge/decisions/system-family-repositories.md` and amend
  the records listed above. Approve pilot, version continuity, dependency policy
  and proposed repository name before creating its remote.
- [ ] Write the pilot's complete ownership/consumer inventory beside this plan.
  Enumerate fixture jobs, docs, scripts and non-Cargo consumers explicitly.

**Verify:** every current pilot dependency and incoming consumer has an owner;
the new decision names the broader rules it changes and why. No production
manifests, releases or repository maps change in this work package.

### 2. Establish a reproducible baseline

- [ ] In source, run the existing Dragon package/runtime/machine tests, headless
  verification, available reference comparisons, UI/MCP/script checks and the
  fleet's Dragon feature checks. Use current test commands from source/CI rather
  than inventing a new smoke test that only starts a process.
- [ ] Record exact commands, fixtures, feature sets, positive executed-case counts,
  output hashes where deterministic, source revision and lock hash alongside
  this plan. Enumerate pre-existing failures; fix blocking bugs before extraction.
- [ ] Record a current packaged native baseline and the relevant browser path.
  Confirm which checks run on each of the five existing native targets.

**Verify:** required fixtures are present, tests really execute, and chosen
screenshots/audio/state/trace or protocol assertions can detect a regression.
Record observed shell API compatibility; if routine pilot work still requires
shared interface edits, stop and reduce or defer the pilot.

### 3. Prepare the shared boundary in place

- [ ] Edit source `Cargo.toml`, the pilot's actual shared dependency manifests,
  `scripts/publishable-crates.py` and `.github/workflows/publish-crates.yml`
  only as needed to package that closure with names, versions, metadata and
  licenses intact. Do not flip `publish` for all 232 explicit members.
- [ ] Audit outgoing shared-library dependencies for family knowledge and
  rename only packages crossing a publication boundary.
- [ ] In `crates/emu198x-web/`, plan the relocation of real-machine integration
  tests before the relevant family departs. Keep all-family tests owned by the
  aggregate surface rather than importing family code into shared libraries.
- [ ] Dry-run packaging in dependency order. For a never-published dependency
  closure, distinguish archive inspection from registry-backed package build
  verification; the latter requires upstream versions to exist first.

**Verify:** format, Clippy and existing tests pass for changed crates; archives
contain required source/assets and no private media; no production shared
library points back to a family. After separately approved publication, build
an isolated consumer using registry sources with no local patches.

### 4. Prepare Dragon's repository and CI without cutting over

- [ ] Create the approved `emu198x/dragon` workspace with its explicit crate list,
  `Cargo.toml`, committed `Cargo.lock`, toolchain/lints, license, README,
  `AGENTS.md`, `RULES.md` and family knowledge. Preserve attribution and source
  history using an agreed history-preserving extraction or full-history import;
  choose the mechanism before running it and verify retained provenance.
- [ ] Copy the source at the recorded commit; avoid independent edits to both
  copies. Track every temporary clone/worktree and freeze the moved paths for
  the short cutover window, replaying any intervening commits explicitly.
- [ ] Add `.github/workflows/ci.yml`, `release-pr.yml`, `maintain-release.yml`,
  `release.yml` and `qualify-packages.yml` scoped to the family. Reuse current
  family workflow conventions; do not blindly regenerate maintained cargo-dist
  signing, producer or Homebrew steps.
- [ ] Port the applicable `scripts/source_lock.py`, `scripts/test_source_lock.py`
  and release preparation checks. Provision required checks, registry trusted
  publication, signing/notarisation and corpus access only at their owning repo.
  Keep owner enforcement and rebase-only PR merges.

**Verify:** a fresh isolated checkout builds/tests without sibling directories;
renamed package APIs and feature sets match the baseline. A real nonpublishing
release pipeline creates packages and qualifies them on all five native hosts.
Receipts bind that family's source revision and unchanged committed lockfile.
Missing package, changed lockfile and mismatched archive/executable checks fail.
Do not claim that existing receipts prove the per-executable feature graph.

### 5. Switch aggregate and public consumers

- [ ] Publish only approved Dragon libraries required by aggregate consumers.
  Update source `crates/emu198x-fleet-web/Cargo.toml` to released Dragon runtime
  packages, plus source `Cargo.lock`; verify a single compatible shell type graph.
- [ ] Update `crates/emu198x-apple/`, `apple/`, browser build scripts and
  `web-player/families.json` only where their source/package assumptions change.
  Run existing native/browser capability and save-state compatibility checks.
- [ ] Prepare site download lookup, Homebrew destination, changelog and issue
  routing updates. Inspect the actual site scripts before naming an edit set;
  family release tags no longer resolve in the suite's GitHub release list.
- [ ] Prepare `Emu198x/docs/status/` and source `docs/status/systems.toml` /
  `scripts/status/` changes to fetch or consume explicit family evidence, preserving
  revision and missing-evidence failures. Update help/fixture fleet check inputs.

**Verify:** the fleet still includes Dragon and can exercise it; selected other
families still work. Apple bridge checks pass. Browser/package names, machine
IDs, CLI/MCP/script contracts and existing save-file handling remain compatible.
Download/install checks exercise actual archives rather than a green deploy.

### 6. Cut over one family

- [ ] Confirm publication approval against the concrete checked packages. Ship
  the approved family native release, then verify hosted archives, receipts,
  checksums, installation and actual emulator output.
- [ ] Switch public routes only after those positive checks. Remove Dragon's old
  binaries from source suite discovery in the same coordinated cutover, and
  update `scripts/prepare-release.py`, suite workflows and release qualification
  expectations as needed. Other families keep the existing suite mechanism.
- [ ] Remove moved source crates only after all incoming references are converted
  and the retained source/history is verified. Preserve historical suite releases.
- [ ] Update umbrella `docs/repo-map.yaml`, applicable `docs/project-map.md` /
  `docs/path-ownership.md`, and `Emu198x/.github/AGENTS.md`; run the existing
  family-repo map checker. Record the authoritative source location in docs.

**Verify:** the old suite packages no Dragon binary, the new release does, no
system disappears from status/catalogues, and a fresh clone follows the documented
route. No path reference or release automation still expects deleted source.

### 7. Prove independent adoption before expanding

- [ ] Complete a real Dragon-only change/release without republishing other
  emulator binaries. Use the next actual bug fix or feature, not a fabricated
  behaviour change solely to exercise versioning.
- [ ] Exercise a real shared-library update in a Dragon dependency PR, or a
  nonpublishing rehearsal if no real update is ready. Demonstrate that an
  unchanged consumer retains its lock/version and that the integration build
  selects a compatible set. Do not publish a meaningless library bump as a test.
- [ ] Compare maintenance effort, build/test cost and interface churn with the
  baseline. Select the next family only after reviewing the result.

**Verify:** unrelated products retain versions and archive identities; the
updated consumer has the intended shared fix; all selected integration paths
pass. If coordination exceeds the benefit, stop rollout with one family extracted.

## Rollout after the pilot

Proposed order is a small browser/native family such as Game Boy or NES, then
Spectrum, followed by C64 and Amiga. The first two exercise common patterns;
Spectrum exercises variants, tooling and its dedicated npm surface; Commodore
adds mixed web bindings, drives and richer release checks. Reassess this order
against actual changes and baseline failures rather than scheduling a mass move.

The remaining families follow the approved ownership table in small batches,
each with the same gates. Shared components become shared because of verified
consumers, not anticipated reuse. At the end, decide whether aggregate products
need a separate repository; do not create one simply for layout symmetry.

## Failure modes and rollback

| Current risk or split risk | Required evidence/control |
|---|---|
| One suite version obscures which system changed | Family changelog/version describes its own change; unrelated archive identities stay unchanged. |
| Shared fix is never adopted | Explicit affected-consumer checklist with verified update or documented deferral. |
| Local paths hide missing registry packages | Fresh isolated checkout and registry-backed package build, without sibling paths or patches. |
| Shell types or feature sets diverge | Native and aggregate builds with real selected versions; compare resolved dependency graphs and capabilities. |
| Extracted system vanishes from checks or downloads | Positive inventory reconciliation; missing expected family/package fails. Never infer removal from absence. |
| Copying CI drops a guard | Deliberate failing cases for source locks, omitted packages and corrupted archives; real five-host qualification. |
| Two copies receive fixes | Brief path freeze, source-revision map and replayed intervening commits; only one authoritative implementation after cutover. |
| Historical knowledge or attribution is lost | Verify retained history/provenance and moved citations before source deletion. |

Before public cutover, keep the old suite authoritative and abandon or repair
the prepared consumer branch if needed. Published library versions remain
immutable; do not delete tags or overwrite packages to undo a trial.

After cutover, restore the prior consumer versions/lockfile and public routing
through checked PRs if qualification fails. Restore old source only from its
verified retained commit if suite ownership must resume. Never force-push shared
history or delete historical releases. Prefer a forward correction after a
public family release; do not reuse its version for different bytes.

Remove task-owned worktrees with `git worktree remove` after inspecting tracked,
untracked and ignored files and verifying retained commits. Stop task-owned
processes and remove disposable caches. Keep durable evidence in the owning
repository, not temporary directories.

## Completion criteria

The pilot is complete only when independent family delivery, explicit shared
dependency adoption and aggregate compatibility have all been demonstrated;
native packages retain the existing qualification guarantees; source/status/
download ownership points to the new repository; and duplicate active source
and task workspaces are removed. A new repository that builds is an intermediate
step, not completion.

For this planning task, completion means the dependency evidence and phased plan
are committed and pushed for review. No migration, registry publication, release
or remote repository creation takes place.
