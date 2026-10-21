# Plan: independent releases from system-family repositories

**Date:** 2026-10-21

**Status:** Planning only. Repository boundaries are agreed except the provisional Sega split; migration and publication are not authorised by this plan.

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
Repository slugs, the pilot and the rollout order below are recommendations for
review. Sega's grouping remains provisional.

## Agreed intent and proposed details

Agreed in the planning discussion:

- One repository per system family; no repository per variant.
- Independent family versions and releases.
- Shared fixes reach families through explicit dependency updates and validation.
- The shell is normally unchanged by system work; significant shared changes
  remain possible.
- Crates that are or could be used by other systems become separately published
  libraries. A second current consumer is not a prerequisite.
- All format implementations migrate to Format198x, including formats currently
  used by only one emulator.
- ZX80 and ZX81 have separate repositories. Atari 8-bit computer models stay
  together as variants are added. The other listed boundaries are agreed, with
  separate Sega repositories the current preference rather than a final decision.
- SG-1000 and SC-3000 belong together in the SG-1000-family repository. This
  boundary is agreed; separation from Master System and Game Gear remains
  provisional. SC-3000 support is future scope, not an implemented fleet feature.
- Reusable peripheral machines, including Commodore disk drives, are independently
  published shared libraries rather than implementation details of one host.
- Published libraries declare compatible dependency ranges; applications select
  exact resolved versions through committed lockfiles and reviewed updates.
- Reuse the existing per-runtime save-state versioning. Review possible counter
  resets per system; a reset is not automatic when a repository is extracted.

Proposed implementation:

- Retain the flagship as the shared workspace, without renaming it during the pilot.
- Keep machine wiring, family runtimes, binaries, tests and family knowledge with
  their family. Publish reusable CPUs, chips, peripherals and host infrastructure
  independently from the shared workspace, even with one current consumer.
- Move all format parsing, encoding and format models to Format198x. Reuse codecs
  already there; separate emulator state/playback adapters from those codecs.
- Classify every crate for existing or plausible reuse before family extraction.
  Family implementation details can remain unpublished and share their family's
  version; library publication is not restricted to the pilot's dependency closure.
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
| Source `knowledge/decisions/savestate-live-machine-serde.md` | Preserve the existing live-machine serialization and per-runtime version envelopes. Record the audit and any separately agreed, unambiguous counter-reset policy without claiming all decoders already enforce identical checks. |
| Umbrella `decisions/project-skeleton-standard.md` | Record the independent-release reason for extraction and correct its stale claim that Emu198x already releases machines independently. This is not a split for symmetry. |
| Umbrella `decisions/formats-graduate-to-their-own-projects.md` and Format198x agent context | Add the explicit Emu198x migration scope: every format implementation moves to Format198x without waiting for a second consumer. Keep byte codecs separate from emulator behaviour. |
| Source `knowledge/decisions/the-guards-apply-to-the-only-committer.md` | Preserve required checks for owners. Explain that this split addresses release ownership, rather than missed failures; use the newer rebase-only merge policy. |

The new Emu198x-specific decision belongs in source
`knowledge/decisions/system-family-repositories.md`. Cross-project repo-map and
skeleton changes belong at the umbrella. Keep the master plan here in the docs
repository; link to it from the decision.

Draft addition to the new decision, reflecting the agreed ownership rule:

> Publish an Emu198x crate independently when it is used, or could be used, by
> another system. Current consumer count does not decide eligibility. Assess
> the component's hardware or host role and document a plausible reuse case;
> do not require an invented consumer or a new abstraction. This replaces the
> plan's former current-consumer-only criterion. All Emu198x format implementations
> move to Format198x, overriding the existing graduation rule's second-consumer
> prerequisite for this migration because file formats are independently useful
> contracts. Machine timing, controller state and playback remain emulator
> concerns and consume the Format198x codecs.

This is a draft for the binding records, not an amendment applied by this plan.

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
The table covers every current fleet feature. Boundaries are agreed except the
marked Sega rows; slugs remain proposed. The table does not claim that all models
of a family are implemented.

| Proposed repository under `emu198x/` | Current fleet feature(s) |
|---|---|
| `sinclair-zx-spectrum` | `sinclair-zx-spectrum`, including existing Spectrum variants and clones |
| `commodore-amiga` | `commodore-amiga`, with OCS, ECS and A1200 implementations together |
| `commodore-c64` | `commodore-c64`; consumes independently published drive machines and IEC libraries |
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
| `atari-8bit` | `atari-800xl` now; other Atari 8-bit computer variants join this repository as implemented |
| `commodore-pet` | `commodore-pet` |
| `commodore-vic-20` | `commodore-vic-20` |
| `coleco-colecovision` | `coleco-colecovision` |
| `jupiter-ace` | `jupiter-ace` |
| `mattel-aquarius` | `mattel-aquarius` |
| `memotech-mtx` | `memotech-mtx` |
| `msx` | `msx` |
| `oric` | `oric-atmos` |
| `sega-sg-1000` (SG-1000/SC-3000 together; wider Sega split provisional) | `sega-sg-1000` now; SC-3000 joins this repository when implemented |
| `sega-master-system` (provisional separate repository) | `sega-master-system` |
| `sega-game-gear` (provisional separate repository) | `sega-game-gear` |
| `sinclair-zx80` | `sinclair-zx80` |
| `sinclair-zx81` | `sinclair-zx81` |
| `sord-m5` | `sord-m5` |
| `spectravideo-svi` | `spectravideo-svi-328` |
| `tatung-einstein` | `tatung-einstein` |

ZX80 and ZX81 are separate product lines for repository ownership; variants
within each remain together. Atari's 8-bit computer repository is deliberately
broader than the currently implemented 800XL. Atari consoles retain their
separate listed repositories.

SG-1000 and SC-3000 share the SG-1000-family repository, including their model
variants. The source knowledge record
`knowledge/systems/sega-sg-1000/overview.md` and its upward reference citations
distinguish their RAM and I/O circuitry as well as the keyboard. Shared ownership
does not imply identical hardware or claim that SC-3000 is already implemented.

The current preference is separate SG-1000/SC-3000, Master System and Game Gear
repositories. Confirm that wider grouping before their extraction. Their shared
`runtime-sega-master-system-class`, video and sound components are candidates
for independent publication, so separate repositories need not duplicate common
code. Give each shared crate one owner and released dependencies. A common
manufacturer or CPU alone does not require a combined repository.

Before extraction, classify every crate as an independently published Emu198x
library, a Format198x format implementation, a family implementation detail, or
an aggregate consumer. Record existing users and plausible reuse separately.
A CPU or peripheral is not family-private merely because only one current
machine uses it. Reuse does not require parameterising away real hardware
differences or redesigning the implementation. Existing published libraries
keep their identities and versions.

The [library and format ownership schedule](2026-10-21-system-family-repositories/library-and-format-ownership.md)
sets the publication criteria, maps all 32 remaining format-named crates, and
identifies adapter work. No family repository retains an independent format
parser/encoder. Codecs already in Format198x are reused rather than duplicated.
Controller-state conversion and machine timing live in emulator adapters, with
names and ownership that make that role clear.

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

Publishable libraries have independent API versions; unpublished internals can
use the family workspace version. Family runtimes are publication candidates
for existing aggregate consumers and other plausible hosts. The integration
workspace selects released versions; it does not force families to release
together. Its own release describes that selected combination.

Published libraries normally declare compatible SemVer ranges. Applications and
aggregate consumers commit their resolved `Cargo.lock` and build with `--locked`.
Adoption is an explicit, reviewed dependency/lockfile update, including compatible
patches and all transitive changes. Do not put exact requirements into every
published runtime: otherwise compatible dependencies can conflict when several
families are linked into one host. Any necessary exact requirement needs its own
documented compatibility reason. Preserve the producer lock receipts.

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

### Existing save-state schemas and possible counter resets

Save-state versions already exist independently of product/package versions.
The binding source decision `knowledge/decisions/savestate-live-machine-serde.md`
defines live-machine serialization and runtime envelopes. Reuse that design;
repository extraction does not call for a new save-state system.

A source spot check at `63efdfba1f0c7394ebec5189b2b0cccc64aac292` found:

| Runtime | Source file under `crates/` | Snapshot version |
|---|---|---|
| Dragon | `runtime-dragon/src/runtime.rs` | 1 |
| NES | `runtime-nintendo-nes/src/snapshot.rs` | 1 |
| Game Boy | `runtime-nintendo-game-boy/src/snapshot.rs` | 2 |
| Spectrum | `runtime-sinclair-zx-spectrum/src/snapshot.rs` | 10 |
| C64 | `runtime-commodore-c64/src/snapshot.rs` | 19 |
| Amiga | `runtime-commodore-amiga/src/snapshot.rs` | 63 |

This is a later observation than the dependency inventory, not a refresh of its
baseline or a full compatibility audit. Source, not this table, owns current
values. Spectrum, C64 and Amiga inspect the version before full payload decode;
the inspected Dragon and NES paths decode the envelope first. Do not claim
uniform decoder behaviour merely because each has a counter.

For every family, record its current schema identity, released readers/writers,
known prior identities, representative saved states and intended compatibility
policy. Unchanged serialized layout keeps its identity through extraction.
UI-only releases and dependency updates with unchanged serialized state do not
require a schema bump. A shared chip's serialized layout or continuation changes
can require a family schema change even if its Rust API is compatible.

Counter resets may be appropriate for particular systems, subject to that audit
and an explicit family decision. Do not reuse a number for a different layout
in the same accepted namespace: a reader must distinguish old and new identities
before interpreting incompatible payloads. If a restart is chosen, agree an
enforced format-generation discriminator or other unambiguous separation, and
define whether legacy states are converted or rejected. A repository name or
release note alone does not distinguish file bytes. Keep existing states intact;
test rejection without mutating the running machine or replacing the saved file.

This plan changes no counters and selects no systems for a reset.

## Pilot recommendation: Dragon

Dragon has a compact family entry point and is consumed by the fleet player.
It tests both independent native delivery and downstream runtime adoption.
It is a candidate, not a declaration that its current accuracy gates pass.

Family repository move candidates, each under source `crates/`:

- `emu198x-dragon`, `runtime-dragon`, `machine-dragon-32`.

Publish `motorola-6809`, `motorola-pia-6821`, `motorola-sam-6883` and
`mos-acia-6551` independently from the shared Emu198x workspace, with the required
`emu198x-` prefix. Their only current direct manifest consumer is
`machine-dragon-32`, but their hardware role makes them reusable components.
`motorola-vdg-6847` is already shared with Acorn Atom and is published there too.
All four Dragon format implementations move to Format198x; the family consumes
their published versions. Publish the shell/UI/native-video/app-icon and
test-helper dependency closure before switching Dragon to registry inputs.
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
- [ ] Classify all 233 recorded crates, including plausible reuse and all 32
  format-named crates, using the ownership schedule. Document any adapter split
  and publication prerequisites; do not limit the review to Dragon's closure.
- [ ] Include complete peripheral machines in the shared publication inventory:
  `machine-commodore-1541`, `machine-commodore-1571`, `machine-commodore-1581`,
  `common-commodore-iec`, `common-commodore-iec-drive` and
  `common-commodore-drive-gcr`. Review their actual dependency closures.
- [ ] Audit existing save-state identities and released reader/writer behaviour
  per family. Record any proposed reset and its byte-level distinction before
  changing a counter; otherwise retain the existing identity.

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
- [ ] Retain representative states from the shipped baseline and verify restore
  and subsequent execution after extraction. Exercise incompatible-state
  rejection; where a reset is proposed, prove old/new identities cannot collide.

**Verify:** required fixtures are present, tests really execute, and chosen
screenshots/audio/state/trace or protocol assertions can detect a regression.
Record observed shell API compatibility; if routine pilot work still requires
shared interface edits, stop and reduce or defer the pilot.

### 3. Publish reusable components and migrate formats in stages

- [ ] Edit source `Cargo.toml`, reusable component manifests,
  `scripts/publishable-crates.py` and `.github/workflows/publish-crates.yml`
  in small publication batches with names, independent versions, metadata and
  licenses intact. Existing or plausible reuse determines scope; do not flip
  `publish` for every crate indiscriminately.
- [ ] Migrate all format implementations to `Format198x/format198x/crates/`,
  with their history, specifications, decisions and tests. Update its workspace
  and `release-plz.toml` as applicable. Follow the ownership schedule: reuse
  existing codecs and separate playback/controller glue before migration.
- [ ] Switch Emu198x consumers to each released Format198x crate before deleting
  its old implementation. Carry no format implementation into a family repo.
  Complete Dragon's format and hardware dependencies before its cutover;
  schedule the other formats in explicit batches until none remain unmigrated.
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
an isolated consumer using registry sources with no local patches. Every format
row has a verified Format198x implementation and converted consumer; adapter
renaming alone cannot mark migration complete. Preserve save-state layout and
machine timing while removing format-layer dependencies on emulator state.

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
pass. The lockfile records adopted versions without unnecessary exact constraints
in published libraries, and save-state outcomes match the family's declared
compatibility policy. If coordination exceeds the benefit, stop rollout with one
family extracted.

## Rollout after the pilot

Proposed order is a small browser/native family such as Game Boy or NES, then
Spectrum, followed by C64 and Amiga. The first two exercise common patterns;
Spectrum exercises variants, tooling and its dedicated npm surface; Commodore
adds mixed web bindings, drives and richer release checks. Reassess this order
against actual changes and baseline failures rather than scheduling a mass move.

The remaining families follow the approved ownership table in small batches,
each with the same gates. Components with existing or plausible cross-system
use are published independently before their consuming families move. Complete
the full format migration schedule rather than treating the pilot as its scope.
At the end, decide whether aggregate products
need a separate repository; do not create one simply for layout symmetry.

## Failure modes and rollback

| Current risk or split risk | Required evidence/control |
|---|---|
| One suite version obscures which system changed | Family changelog/version describes its own change; unrelated archive identities stay unchanged. |
| Shared fix is never adopted | Explicit affected-consumer checklist with verified update or documented deferral. |
| Local paths hide missing registry packages | Fresh isolated checkout and registry-backed package build, without sibling paths or patches. |
| Shell types or feature sets diverge | Native and aggregate builds with real selected versions; compare resolved dependency graphs and capabilities. |
| A reset reuses a legacy save-state number for different bytes | Retain existing identities or enforce a distinct generation/namespace before incompatible decoding; test legacy restore or explicit rejection. |
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

The full migration also requires every crate to have a reviewed ownership
classification, every reusable publication candidate to have an independent
release or an explicit unresolved blocker, and all format implementations to
reside in Format198x. An unresolved blocker is unfinished work, not a reason
to quietly reclassify a reusable crate as family-private.

For this planning task, completion means the dependency evidence and phased plan
are committed and pushed for review. No migration, registry publication, release
or remote repository creation takes place.
