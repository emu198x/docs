# Remaining Amiga regional owners

Engineering-frontier continuation of #2144, starting at source
`c06321677cde6b4aea0211197eb8436ceae0a1a7`. Established fixed-owner/private
workspace pattern is approved. Classify the existing maxed A500 explicitly
as a modified-RAM configuration of its 8372A board; no new silicon is inferred
from RAM size. Agree any new RTC migration before changing production.

1. Re-consult RULES.md, machine-owner/runtime-shape/catalogue decisions,
   primary board sources and vendored precedent. A500 service manual
   PN 314981-04, PDF 14 / printed 2-9 maps 8370 to rev 5 and 8372 to rev 6a,
   distinguishes their DRAM populations and says 1 MiB chip addressing is an
   unsupported modification. Service update issue 25, PDF 43 / item 25/3-2.1
   says A2000 rev 6 ships jumpered for 1 MiB. A2000 rev-6 schematics
   PN 314135-02, PDF 4 parts list records onboard MSM6242B at U801. WinUAE
   CP_A2000 enables RTC independently of expansion RAM. Reproduce the suspected
   slow-RAM-gated decode using CPU-executed writes/readback before any fix.
2. Freeze immutable original v67 complete envelopes and continuations for all
   twelve existing OCS-shaped profiles (eight owners plus A501/A530 profiles):
   progressive/interlaced output, real half-CCK debugger cuts, held/released
   controls, media, exact video/audio/clock observations and final full state.
   A1000 cases must cover bootstrap-visible and WOM-locked phases, with original
   guest handoff rather than patched CPU/RAM. The capture helper refuses overwrite
   and checks the untouched baseline. Retain a disposable failing control.
3. If A2000 RTC decoding fails, ask for the family save-version/read policy
   before fixing it. Expected candidate: v68 writer, explicit v66/v67 readers,
   legacy A2000 RTC-presence correction only, preserving all clock history and
   other fields. Keep the existing A500+ v66 migration unchanged. Reject malformed
   new states before mutation. Reproduce and verify independently of extraction.
4. Move shared OCS-shaped wiring from `crates/machine-commodore-amiga-ocs/` to
   `crates/common-commodore-amiga-ocs/` as `OcsCore<C>`. Preserve snapshot field
   layout and installed-Agnus enum order. Proposed fixed owners are A1000,
   A500 rev 5, A500 rev 6a and A2000CR rev 6, each PAL/NTSC. Markers select
   original Agnus revision/8372A, bootstrap/WOM fitting, region, board defaults,
   onboard RTC and owner ID. Model optional RAM/add-ons independently. No new
   PCB populations, CPU timing or chip behaviour is introduced by extraction.
5. Keep the generic family runtime and existing profiles/aliases. Update
   `runtime-commodore-amiga/src/{runtime,variants,live_access,profiles,
   amiga_model,snapshot,pointer,queries}.rs`, manifests, direct callers, browser
   consumers and regression scripts. Add fixed typed aliases and dispatch arms;
   validate owner/config/raw-restore identity before mutation. Keep all diagnostic,
   trace, lifecycle, bootstrap, CPU replacement and A530 bridge surfaces. Tests
   move with common wiring and gain explicit local test markers where needed.
6. Add direct invariant tests per owner, all-profile dispatch/lifecycle/restore
   matrices and exact frozen continuation comparisons. Native A1000 bootstrap/
   Kickstart handoff and A500/A2000 firmware boot evidence remain separate from
   synthetic qualification. Check RAM, ROM immutability, clocks, silicon, controls,
   active output, restore/release and foreign-board rejection without using
   current implementation values as the only oracle.
7. Add eight owner IDs to `docs/status/systems.toml`, retire the aggregate
   machine owner, regenerate status and verify dependency/evidence attribution.
   Keep family binary unchanged. Run selected tests/Clippy/consumer builds,
   guards and exact-head CI; retain original capture history remotely.
8. Update docs/tracker and public board routes/captures. Preserve the aggregate
   URL using the site's established canonical redirect pattern. Embed a published
   player only where its constructor/profile is verified to match the board;
   omit others. Full build/route/link/prose, browser accessibility, live routes
   and image-byte checks qualify publication. Keep unimplemented PCB revisions
   and peripheral/software coverage explicit.
9. Preserve evidence/recovery durably, inspect and remove task worktrees, caches
   and processes, and measure disk with df. Serial builds use a task-specific
   target with incremental/debug info disabled. Preserve primary checkout edits,
   ongoing Pentagon/CRTC worktrees and retained Atari/PET investigation locks.

The named donor archives are checked before substantive new helper code; no
archived CPU/chip code is ported. Existing ECS/A1200 owned fixture generators
are the preferred local precedent.


## Approved prerequisite

On 2026-11-02, v68 output with explicit v66/v67 readers was approved. Correct
only the legacy A2000 RTC-presence flag; retain its saved clock history and
every other field. Keep the existing A500+ v66 migration. CPU-executed
register writes/readback fail for both stock A2000 regions: `(15, false)`
instead of `(5, true)`. The same guest passes both A501 positive controls
and both unexpanded A500 absence controls. No production source has changed.

The remaining-owner decision must explicitly supersede chipset-only dispatch
in `amiga-machine-catalogue.md` sections 1/2 and the corresponding Amiga
paragraph in `runtime-internal-shape.md`, as earlier fixed owners already
require. Keep the generic runtime, chipset classification and accelerator
separation. This records the approved machine-owner rule rather than silently
leaving a contradictory older catalogue rule binding.


## Original corpus frozen

All 56 untouched v67 cases captured/replayed exactly. The ZIP reader validates
all 177 member identities in memory; archive size is 2,752,799 bytes versus
1,273,988,733 raw bytes. The test-only existing workspace ZIP dependency was
approved; no registry package was added. Full restored initial/final saves
remain byte-exact. Independently constructed guests compare every native packet;
their cold RTC seed comes from host time and is deliberately not confused with
a restored saved history. A disposable bad observation (141648 -> 141776 clocks)
fails the native comparison despite valid ZIP/member hashes. Formatting and
selected strict Clippy pass. No production Rust source changed before capture.


## RTC correction verified before extraction

All four CPU-guest tests now pass. Six focused suites pass 76 tests with no
failures/ignores, including every frozen original continuation and 65 snapshot
regressions. Original A2000 v67 files and explicitly header-translated v66
payloads retain every other byte; malformed v68 clock removal rejects atomically.
Existing A500+ malformed-v67 rejection remains and also covers v68. Strict
all-target Clippy for the unchanged-shape OCS/runtime crates passes.

The extraction will tie raw snapshot ownership to the same Rust marker as its
core, with that marker skipped by serde. Expanded A500/8372A and A2000 payloads
can otherwise contain indistinguishable chip state; do not pretend that content
alone encodes the motherboard. Runtime envelopes retain their existing model
identity and reject foreign profiles. No serialized ownership field is added.

Local A1000 inputs were found: `~/.emu198x/roms/commodore-amiga/a1000-bootstrap.rom`
and the original TOSEC Kickstart 1.2 r33.180 A1000 ZIP in the library's
`Commodore/Amiga/Kickstart-Disks/` directory. They remain immutable local inputs.

## Fixed-owner extraction verification

The eight owners each pass seven direct hardware invariants (56 tests total).
The existing original-continuation and snapshot suites pass 80 tests, including
all 56 original OCS cases, all ECS/A1200 specimens and 65 detailed snapshot
regressions. No replacement goldens were recorded. The registry check passes
104 machines across 34 shipping crates. Direct-test firmware copies must match
the independently archived originals byte for byte.

Internal disk exhaustion interrupted further checks. The attempted external
cache transfer was stopped after identifying its two task-owned processes;
the partial external copy and the disposable 464 MB local cache were removed.
`df` confirmed roughly 460 MB reclaimed. Serial verification rebuilt only the
task target at `/private/tmp/198x-ocs-target`. Remove it after completion.
Source and evidence stay in their owning Git repositories.

## Native qualification and existing gap

All eight regional configurations have visually inspected original-firmware
insert-disk captures. A1000 stock 256 KiB reaches the real disk/WOM handoff
at fields 1388 PAL / 1655 NTSC and the 1.2 screen at 2600 fields. Rev-5
A500 uses 1.3; stock 512 KiB rev-6a and 1 MiB A2000CR use 2.04 at 650 fields.
PAL mixed-chip 1.3 stays white. The unchanged original engine independently
reproduces exactly that framebuffer, with tracked production clean. Receipts,
negative images, hashes and the old helper are retained in the artifact folder.

The temporary original worktree is `Emu198x/.worktrees/ocs-original`, detached
at the verified evidence tag. Its only unique file is the preserved capture
helper; its build target is `/private/tmp/198x-ocs-original-target`. Remove both
after the evidence commit is verified remotely. The original source PR is
#2236. CI found two native-video examples under `tools/` still using the removed
aggregate alias; they are being converted to the same fixed rev-5 PAL owner.
