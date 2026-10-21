# Library publication and format ownership schedule

**Status:** Planning. No crates move or publish as part of this document.

This supplements the [family repository plan](../2026-10-21-system-family-repositories.md).
Library crates publish to crates.io by default, including system-specific
libraries. Existing **or potential** cross-system reuse determines shared
source ownership, not publication eligibility. Formats move to Format198x
regardless of current consumer count.

## Independently published Emu198x libraries

Publish reusable crates individually from the shared Emu198x workspace; this
does not require a repository per library. Family repositories consume released
versions. Each publication needs a package version, API documentation, tests,
reviewed package contents and release notes. Shared libraries release
independently; tightly coupled family libraries can publish together using
their family's version and changelog.

| Component | Publication criterion and intended owner |
|---|---|
| CPU cores and instruction-family support | Independently published Emu198x libraries. A single implemented machine is not a reason to bury a general CPU core in that family. |
| Chips and peripherals | Publish by default. Existing or potential cross-system hardware use places them in the shared workspace, including components with one current consumer. Model the actual part; no invented generic interface is required. |
| Complete peripheral machines | Independently published Emu198x libraries where reusable. Keep the 1541/1571/1581 drive machines and IEC/GCR support in the shared workspace; host families consume their released versions. |
| Shell, UI, native video, browser host, app icon, test support | Publish the reusable host/tooling surfaces independently. Keep real-machine integration tests outside the shared production dependency graph. |
| Common tape, cassette, bus and family helpers | Publish library crates by default. Review responsibility for ownership: reusable interpretation/hardware behaviour stays shared; byte layouts/codecs go to Format198x; machine wiring stays with its family. |
| Machines and runtimes | Publish libraries by default, with ownership in the family. No second consumer or alternate-host proposal is required. Coupled family packages may publish on one release cadence. |
| Native executables and aggregate applications | Preserve product releases and publish library entry points by default. Review command-line binaries for crates.io installation where useful; do not assume every platform packaging wrapper belongs on the registry. |

Publication exceptions must describe the concrete reason: for example, a local
corpus provisioning harness that cannot operate as a standalone package, or a
temporary packaging-only crate with no distributable implementation. These are
examples to evaluate, not blanket exemptions for helpers, tests or family code.
Private/media inputs, missing metadata, naming work and unpublished dependencies
are readiness blockers to resolve, not permission to forget the default.

For each exception, record its owner, reason and when it should be reconsidered.
Do not publish empty placeholders or add generic interfaces to make a package
appear reusable. Publish the existing useful implementation with an honest API
and pre-1.0 compatibility policy.

For every crate in `dependencies.tsv`, the implementation inventory must record:
owner, publication target or explicit exception, existing consumers, plausible
reuse, package name/version, dependency closure, packaging blockers, relevant
tests and migration batch. Assess the responsibility, not just the name or the
number of current incoming edges. A reuse case explains shared ownership;
absence of one does not block publication of a family library. Do not claim an
unimplemented consumer exists.

For the Dragon pilot, the 6809 CPU, 6821 PIA, 6883 SAM, 6847 VDG and 6551 ACIA
are reusable hardware libraries and stay in the shared workspace for independent
publication. They do not move into Dragon simply because several currently have
only one local consumer. Preserve published identities where they already exist;
add `emu198x-` to newly published package names without dropping category words.

The reusable machine rule includes a peripheral's complete emulation, not just
its chips. `machine-commodore-1541`, `machine-commodore-1571` and
`machine-commodore-1581`, with the applicable `common-commodore-iec`,
`common-commodore-iec-drive` and `common-commodore-drive-gcr` dependencies, remain
shared publication candidates. Their disk byte codecs move to Format198x.
The C64 repository integrates drives through released dependencies; it does not
own their implementations merely because it is their current host.

Published libraries normally use compatible dependency ranges; committed
application lockfiles select the exact shipped combination. Validate peripheral
state inside the owning family's save-state envelope when adopting a new drive
or chip version: API compatibility alone does not establish serialized-state
compatibility.

## Format migration inventory

Emu198x baseline: `530f66d06d9b0faa8bfcc03efc87d7d236db1403`.
Format198x baseline inspected: `7436ad36a7df872ac2a9655edb01f1e7c3d95fa9`.

All 32 `crates/format-*/Cargo.toml` files on disk match the 32 format-named
packages in the dependency inventory, including the implicitly reached VIC-20
CRT crate. The Format198x checkout has 15 existing crate manifests at this
baseline. Check registry publication separately; a local manifest is not proof
of a published version.

Proposed destination package names below preserve the source's distinguishing
suffix unless an existing codec already owns the grammar. Review naming against
the actual format before first publication, especially names without a machine
or manufacturer. A row need not result in a new crate if its byte grammar is
already owned by another Format198x library.

| Source crate under Emu198x `crates/` | Format198x destination / migration work |
|---|---|
| `format-acorn-atom-atm` | `format198x-acorn-atom-atm`; separate serde/state coupling. |
| `format-acorn-uef` | `format198x-acorn-uef`; separate byte/chunk model from cassette playback, state serialisation and gzip handling. |
| `format-amstrad-cpc-cdt` | Reuse existing `format198x-tzx`; CPC clock scaling is emulator playback, not a second codec. |
| `format-amstrad-dsk` | Reuse existing `format198x-amstrad-cpc-dsk`; this crate is already a controller-state adapter. Retire its format identity after consumers use the codec and an emulator adapter. |
| `format-atari-8bit-atr` | `format198x-atari-8bit-atr`; separate state serialisation and emulator test-helper coupling. |
| `format-commodore-c64-crt` | `format198x-commodore-c64-crt`. |
| `format-commodore-c64-d64` | `format198x-commodore-c64-d64`. |
| `format-commodore-c64-d71` | `format198x-commodore-c64-d71`. |
| `format-commodore-c64-d81` | `format198x-commodore-c64-d81`. |
| `format-commodore-c64-g64` | `format198x-commodore-c64-g64`. |
| `format-commodore-c64-p00` | `format198x-commodore-c64-p00`. |
| `format-commodore-c64-prg` | `format198x-commodore-c64-prg`. |
| `format-commodore-c64-t64` | `format198x-commodore-c64-t64`. |
| `format-commodore-c64-tap` | `format198x-commodore-c64-tap`; separate state serialisation from the file model. |
| `format-commodore-vic-20-crt` | `format198x-commodore-vic-20-crt`; include this implicit member explicitly in the migration. |
| `format-dragon-bin` | `format198x-dragon-bin`; separate state serialisation. Pilot dependency. |
| `format-dragon-cas` | `format198x-dragon-cas`; separate state serialisation. Pilot dependency. |
| `format-dragon-disk` | `format198x-dragon-disk`; owns VDK bytes, not drive/controller state. Pilot dependency. |
| `format-dragon-pak` | `format198x-dragon-pak`; separate state serialisation. Pilot dependency. |
| `format-jupiter-ace-ace` | `format198x-jupiter-ace-ace`. |
| `format-memotech-mtx` | `format198x-memotech-mtx`; confirm the represented container in the package description. |
| `format-nintendo-game-boy-cartridge` | `format198x-nintendo-game-boy-cartridge`; separate ROM/header metadata from live MBC/Cartridge types. |
| `format-nintendo-nes-ines` | `format198x-nintendo-nes-ines`; separate serde/save-state representations. |
| `format-sinclair-zx-spectrum-rzx` | `format198x-sinclair-zx-spectrum-rzx`; isolate byte/event layout, compression and runtime replay responsibilities. |
| `format-sinclair-zx-spectrum-sna` | `format198x-sinclair-zx-spectrum-sna`; migrate shared snapshot file models first. |
| `format-sinclair-zx-spectrum-snapshot` | Format198x-owned common snapshot file model, provisionally `format198x-sinclair-zx-spectrum-snapshot`; no shell/runtime dependency. |
| `format-sinclair-zx-spectrum-szx` | `format198x-sinclair-zx-spectrum-szx`; migrate snapshot models and resolve compressed-block ownership. |
| `format-sinclair-zx-spectrum-tzx` | Reuse existing `format198x-tzx`; move machine-facing playback into emulator ownership. |
| `format-sinclair-zx-spectrum-z80` | `format198x-sinclair-zx-spectrum-z80`; migrate shared snapshot file models first. |
| `format-sinclair-zx80-o` | `format198x-sinclair-zx80-o`. |
| `format-sinclair-zx81-p` | `format198x-sinclair-zx81-p`; remove emulator test-helper coupling from standalone codec tests. |
| `format-tzx` | Reuse existing `format198x-tzx`; current crate interprets blocks into tape spans. Keep reusable playback in a published emulator library, without retaining a duplicate format parser. |

All parsing/encoding and file-owned models belong to Format198x. The schedule
does not exempt the four adapter crates from migration: verify that the existing
Format198x codec owns their entire file grammar, migrate any missing byte-level
behaviour there, then relocate or rename the remaining emulator-only glue.
Changing a crate's name without completing that audit is not graduation.

### Dependency constraints to resolve

Format198x's current standalone, dependency-free convention is binding. Current
Emu198x format crates use serde, thiserror, flate2, emulator helpers and live
hardware types in various combinations. Do not transplant these dependency
graphs unchanged or weaken the convention silently.

- Use standalone byte models and errors in Format198x. Keep serde save-state
  representations and conversions in the consuming emulator so existing states
  do not become unreadable as a side effect of moving file models.
- Move live FDC and MBC behaviour out of format code. The codec reports file
  metadata; a consumer decides how to construct its emulated hardware from it.
- Preserve compressed-file and compressed-block support. For UEF, RZX and SZX,
  design the compression boundary before migration. Present the options against
  Format198x's dependency rule; obtain approval for any new dependency or scoped
  rule change. Do not drop support or build a new compression engine merely to
  force a nominally dependency-free move.
- Snapshot file models belong in Format198x; shared support may need an explicit
  same-project dependency exception or a revised crate boundary. Resolve that
  choice before publication rather than duplicating the types.
- Existing TZX and DSK decisions already separate codecs from timing/controller
  adapters. Preserve those boundaries. Reusable playback may publish from
  Emu198x even when only one machine currently calls it.

## Migration batches and verification

1. Review the global library ownership inventory and draft the graduation-rule
   amendment. Start the pilot's format dependencies and reusable hardware first.
2. Move simple, self-contained format codecs in small batches; preserve history,
   specifications, design decisions, citations and fixture provenance. Use the
   established Format198x independent-release workflow and package metadata.
3. Resolve controller, mapper, playback, snapshot and compression boundaries in
   focused follow-up batches. Do not combine them into an emulator rewrite.
4. Publish reviewed codec versions, convert all consumers and test registry-backed
   builds before removing old implementations. A format leaving suite lockstep
   starts at 0.1.0 under the graduation decision; an already published Format198x
   crate continues its existing version. Product versions do not reset.
5. Reconcile every source row positively against its destination implementation,
   published version, converted consumers and passing checks. Require zero
   unmigrated format implementations before declaring the full migration done.

For each codec, run existing format tests and appropriate valid/malformed-image
checks, round trips where encoding exists, and an independent reader or real
machine/runtime check where available. Compare consumers' load/export behaviour,
save-state compatibility and tape/disk timing with the original baseline.
Verify that ordinary Cargo builds work without sibling paths, that archives
contain the required source and no private media, and that the declared
dependency policy holds in the actual packaged manifest.

No migration completion claim follows from a new package name or a successful
upload alone. Library availability and the consuming emulator's behaviour both
need evidence.
