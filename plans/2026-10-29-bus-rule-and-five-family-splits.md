# Bus-interface rule retirement and five family splits

Lane: engineering-frontier. Requested on 2026-10-29: #2178, then #2142,
#2141, #2140, #2139 and #2138. This continues the approved concrete-board
splits. Keep families together at the runtime/runner layer, use private common
wiring and concrete machine crates, and publish no registry packages.

## 1. Retire the interface-shape ban (#2178)

The issue records the retirement on 2026-10-28. Rule 6, its decision records
and the extraction template still forbid traits and callbacks, so an agent
can reject an accurate implementation solely because of its API shape.

1. Rewrite rule 6 in `RULES.md` around observable hardware signals and timing;
   retain rule 5 and the master-clock requirements. Update `AGENTS.md` and
   `CONTRIBUTING.md` so their front-door summaries agree.
2. Update `knowledge/decisions/cpu-bus-interface.md` and `no-bus-trait.md` to
   record retirement, the original accuracy purpose and the replacement.
   Update active claims in `workspace-shape.md`,
   `dma-chip-memory-interface.md`, `spectrum-intended-design.md` and the
   architecture reviews that still present the old ban as binding. Preserve
   descriptions of the existing implementation and historical review scope.
3. Update `scripts/extract-repo.py`'s generated `AGENTS.md`. Exercise the actual
   generated file in `scripts/test_extract_repo.py`: accuracy remains required,
   and a prohibition of traits/callbacks must not return. Reproduce failure
   against the old template before the fix, then run the existing suite.
4. Run documentation/fixture guards and Python checks. Commit and push a small
   linear PR. Existing extracted repositories pick up the wording when next
   touched; do not sweep or rewrite CPU/chip implementations.

## 2. BBC Model B, B+ and Master 128 (#2142)

The original issue's statement that B+ stays with B is superseded by its
triage and the binding hardware-identity decision. The current runtime has
three profiles, and version-10 snapshots.

1. Consult primary BBC/Master hardware references and the runtime/machine
   decisions. Inventory constructors, state fields, ROM sets and tests in
   `crates/machine-acorn-bbc-micro/` and `runtime-acorn-bbc-micro/`.
2. Before moving code, add synthetic live-state captures and complete native
   frame/video/audio/input continuation under `test-data/acorn/`. Cover all
   three profiles, B+/Master paged/shadow memory, WD1770 state/media, Master
   CMOS and ROM paging; verify against the original implementation first.
3. Move shared wiring, `saa5050.rs` and `rtc.rs` into
   `crates/common-acorn-bbc-micro/`. Retain the existing Model B machine owner
   and introduce concrete B+ and Master 128 owners, with construction fixed
   by board. Replace family selection in `runtime-acorn-bbc-micro/src/` with
   family-owned dispatch; no machine-to-machine dependency.
4. Preserve the version-10 serialized layout, aliases, firmware conventions,
   all existing disc tests and working later-board disc support. Model B's
   missing 8271 remains #380. Add distinct machine IDs and evidence owners in
   `docs/status/systems.toml`; preserve family shipping and browser routes.
5. Run frozen state replay, existing machine/runtime/CLI/fleet tests,
   model-matched real MOS boots and keyboard/disc regressions, strict Clippy,
   rustdoc, registry/status checks and exact-head CI. Merge and update #2142
   and only the completed #2144 rows after verifying evidence ownership.

## 3. Game Boy physical boards (#2141)

Current source: `machine-nintendo-game-boy/src/{lib,cgb,snapshot_v3}.rs` and
`runtime-nintendo-game-boy/src/`. The runtime supports seven profile names;
its current envelope is version 4 with an explicit version-3 reader.

1. Inventory DMG/MGB/CGB/AGB behaviour, boot state and SGB/SGB2 limitations
   against primary references. DMG0 is a boot-ROM revision. Do not equate a
   skipped-boot profile with complete Super Game Boy hardware; keep #326 and
   DMG OAM work #1728 visible. Determine concrete owners from implemented,
   evidenced hardware, retaining existing profile IDs and honest limitations.
2. Capture original v4 and accepted v3 saves before moving code, including
   mid-boot firmware/unmap latch, CGB double speed, HDMA, banked memory and
   palettes. Freeze complete CPU/video/audio/input/native-boundary replay.
3. Move genuine shared wiring into `common-nintendo-game-boy`, with separate
   concrete owners for the distinct boards. Keep `runtime-nintendo-game-boy`
   and its runner at family level; neither monochrome nor colour machine
   depends on another machine. Retain original envelope/state bytes and the
   explicit v3 reader; do not smuggle a schema or timing redesign into a split.
4. Move each board's tests with it. Add identity and wrong-board restore
   rejection with atomic receiver state. Preserve screenshot ROM/boot hashes,
   boot gates, OAM, speed/HDMA and audio/input regressions. Validate registry
   ownership and all exact-head CI before completing the issue.

## 4. Game Gear and Master System boards (#2140)

Current source: `machine-sega-master-system/`,
`runtime-sega-master-system-class/`, the SMS and Game Gear runtimes/runners.
The shared runtime envelope is version 10.

1. Source-check the existing `SmsVariant` boards, regions, VDP revisions,
   Japanese FM wiring and Game Gear differences. Capture existing per-profile
   v10 saves and full continuation, including mapper, SRAM, stereo, FM and
   viewport state. RAM/cartridge options stay add-ons.
2. Extract shared cartridge/FM/VDP/CPU glue to a common owner and bind each
   evidenced existing board in its own machine crate. Game Gear gets its own
   owner and tests; SMS machine crates do not contain a Game Gear selector.
   Preserve existing two runners and family/runtime selection.
3. Add a pinned real Sonic cartridge title/attract regression (the issue's
   referenced Rev 0 identity must be verified in full), alongside synthetic
   fixture-free tests. Keep stereo #149/#220 and compatibility #1932 qualified.
4. Verify original saves, all existing tests, real-cartridge execution,
   Clippy/rustdoc and per-board CI evidence before closing #2140.

## 5. MSX generation and maker boards (#2139)

Current source: `machine-msx/src/{lib,sound,note_tests}.rs`,
`runtime-msx/src/{profiles,runtime,snapshot,input,queries}.rs`; snapshots v10.

1. Read primary model/slot references and enumerate existing real-board
   layouts. Generic C-BIOS presets need explicit identities rather than being
   silently presented as manufacturer boards.
2. Freeze v10 state/continuation per existing layout before extracting. Cover
   primary/secondary slots, cartridge ports/mappers, V9938 state, SUB-ROM,
   clock, memory mapper and media/controllers wherever currently implemented.
3. Extract common slot/PPI/PSG/cartridge glue and give each evidenced board
   a concrete machine owner, retaining the family runtime/runner. Move MSX2
   C-BIOS tests and each model's tests with their owners. Preserve #244's
   topology regression coverage and all firmware/profile IDs.
4. Re-run identified Sony HB-F1 firmware to BASIC 2.0 and every available
   matched model firmware, plus C-BIOS and synthetic gates. Preserve state
   layout and review exact-head CI/registry evidence before closing #2139.

## 6. Dragon and CoCo boards (#2138)

Current source: `machine-dragon-32/src/{lib,disk_serde}.rs` and
`runtime-dragon/src/{runtime,profiles,media_serde}.rs`; runtime snapshots v2.

1. Source-check Dragon 32 PAL, Dragon 64 PAL, CoCo 1 NTSC and CoCo 2 NTSC
   differences. Capture accepted v2 envelopes and full continuation before
   moving code; include Dragon 64 banking/ACIA, CoCo RAM sense, keyboard,
   palette/video phase, interrupts, tape and existing disc/media state.
2. Extract common 6809/SAM/VDG/PIA glue, retaining true family-specific
   hardware in distinct machine owners. Keep shared runtime/runner selection
   and profile aliases. Do not reopen the resolved binary-split question.
3. Preserve all existing diagnostics, mapped media and cold-reset behaviour.
   Re-run CoCo 1 Color BASIC 1.2 and CoCo 2 1.3 with Extended Color BASIC 1.1,
   keyboard PRINT regressions and existing Dragon firmware/disc checks.
   Keep #2134/#2135 connected to their actual completed behaviour.
4. Run focused and fleet tests, strict Clippy/rustdoc, original-save replay,
   registry/status generation and exact-head CI; then update #2138/#2144.

## Execution discipline

Complete one independently verified change/commit at a time. Write each
family's concrete file/board/test inventory into this plan before its code
moves. Existing behaviour and save bytes are the baseline; source findings
that require new hardware, schema or architectural choices need a separate
explicit design. Do not claim unsupported hardware because a profile name
exists. Keep accuracy defects visible and separate from mechanical splits.

Use linear task branches from current main and rebase-only merges. No merge
commits, force pushes, test bypasses or registry publishing. Reuse owned build
caches, bound diagnostics, and avoid editing code while a broad test/doc build
is using it. Confirm exact-head CI success and actual per-board tests, retain
commits on verified remote/main refs, and remove all owned worktrees/caches
and processes before reporting completion. Preserve primary branches, the
unrelated ZIP plan and other agents' locked worktrees.

### BBC concrete inventory, before extraction

Keep Model B's `machine-acorn-bbc-micro` owner; add
`machine-acorn-bbc-micro-b-plus` and `machine-acorn-bbc-master-128` over
`common-acorn-bbc-micro`. The common state preserves the exact original
`BbcMicro` field order/attrs. Fixed board descriptors provide CPU construction,
model, extra-RAM length and sideways-RAM mask. Restore validates those fixed
properties and reinstates the nonserialized CPU variant, including 65C12.

Move `src/rtc.rs`, `src/saa5050.rs` and private wiring tests to the common
owner. Keep Model B BIOS/tape tests in its machine crate; move
`tests/bplus_disc.rs` and `tests/master_disc.rs` to their concrete owners.
Give each board synthetic boot/control tests and identity/cadence tests.
Stateless DFS image helpers remain common rather than selecting a board.

`runtime-acorn-bbc-micro/src/machine.rs` owns three-way static dispatch and
transparent state serialization. Its other concern modules keep their current
roles. Add model/board consistency rejection in `snapshot.rs` before receiver
mutation. Update workspace/lock/app manifests and the existing current test
commands; retain version 10, profile IDs, routes and actual clock/video logic.
Add B+ and Master machine IDs and their own tracker labels/milestones, then
regenerate status pages. Frozen inputs/outputs live under
`test-data/acorn/bbc-micro/split-v10/`; check the initial and continued whole
state bytes as well as every pixel/sample and native-frame timestamp.

The 1987 New Advanced User Guide and BBC/Master reference distinguish the
B+'s paging/shadow/1770 from the Master's 65C12/ACCCON/CMOS/banked memory.
Vendored b-em supplies implementation precedent. Local Model B ROMs are
present; locate and identify matching B+/Master sets before the real-disc
checks, without committing manufacturer firmware. Source inventory does not
authorise inventing additional BBC models or changing board timing.

### Game Boy inventory, before extraction

`common-nintendo-game-boy` already exists. Extend that owner with the original
state/wiring implementation and its CGB and v3-reader modules; do not create a
second common crate. Keep the old state fields, attrs and execution methods
intact. A statically bound board wrapper owns construction and delegates to
that common state engine. Existing chip/format dependencies move with the
code; no new registry package is needed.

Concrete owners: retain `machine-nintendo-game-boy` for DMG (DMG0 and later
boot-ROM revisions remain profiles); add Pocket, Super Game Boy, Super Game
Boy 2, Game Boy Color and Game Boy Advance owners. The AGB machine ID names
the physical board (`nintendo-game-boy-advance`); its profile, status and crate
documentation must explicitly limit current execution to CGB compatibility.
Do not invent a second physical board identity for a different execution mode
when native GBA support arrives.
SGB/SGB2 currently provide only Game Boy execution with skipped-boot states.
Retain that limitation explicitly, with boot-ROM/SNES protocol/host timing
work still in #326 under the previously agreed scope. On 2026-10-29, we explicitly confirmed preserving the current behaviour
and keeping full SGB hardware work in #326; additional behaviour needs its own
hardware design.

The old machine payload has no physical-board tag. The v3/v4 envelope's
existing profile ID is the authoritative board identity on restore. Decode
into the exact common state first, validate profile/firmware and monochrome
versus colour consistency, then bind it to the matching concrete board.
Do not infer DMG versus Pocket/SGB/AGB identity from mutable boot register
values or pretend an old payload encodes information it lacks. Do not add a
serialized enum tag or change envelope versions for this extraction.

Retain the family runtime/runner and all seven profile IDs. Update the stale
catalogue prose that says CGB is the same machine or that monochrome boot-ROM
execution has not landed. Add separate, honest machine IDs/evidence owners
and board-appropriate labels/milestones. Constructor boot profiles may select
ROM revisions of one fixed board, never another board; reject those requests.

Capture v4 whole-state, every emitted native-frame pixel/palette and all audio
sample bits for each existing profile. Include active timers, joypad, OAM DMA
and CGB banking/HDMA/speed state, plus mid-boot cases for firmware-capable
models. Preserve the existing genuine v3 fixtures and independent DMG/CGB
continuations. Move common private tests with their code; move cgb-acid2 to
its concrete board, retaining its pinned input/reference and negative control.
Give every concrete owner fixture-free boot/control and identity tests, and
preserve boot/logo, screenshot/hash, OAM, native-frame, audio and input gates.

### Sega inventory, before extraction

`machine-sega-master-system/src/lib.rs` holds seven serialized `SmsVariant`
values, but the family catalogue has nine physical profiles: late export
Master System NTSC/PAL, early 315-5124 Master System NTSC/PAL, Japanese
Master System, Master System II NTSC/PAL, Mark III and Game Gear. The II
profiles currently select the late export execution engine because removed
ports/buttons are not modelled. Preserve that execution mapping while giving
those physical boards distinct owners; do not claim the missing ports are
already emulated. Keep every existing profile ID and both runners.

Retain `machine-sega-master-system` for the late export NTSC owner; introduce
`machine-sega-master-system-pal`, `-japan`, `-1-ntsc`, `-1-pal`, `-2-ntsc`,
`-2-pal`, `machine-sega-mark-iii` and `machine-sega-game-gear`. Move original
wiring, cartridge and FM modules to `common-sega-master-system`. Its raw state
keeps the original field order and serialized enum order; no new enum variants
are inserted into old save payloads. Static concrete wrappers bind construction
to a board. A family enum in `runtime-sega-master-system-class/src/machine.rs`
selects those owners from the existing model IDs; the raw-state variant must
match that model's existing execution mapping before a restore mutates state.
The envelope model identifies II versus the late export board, which the old
raw engine enum cannot distinguish by itself. Keep envelope version 10.

Freeze each of the nine profiles before moving code, with original whole
states and complete continued frames/audio/time. Include mapper SRAM and
control state, Game Gear stereo/Start/viewport, Japanese FM and early/later
VDP revisions. Move the existing synthetic boot/control tests to every owner,
keep private tests beside the common wiring, and add fixed-construction and
atomic wrong-board restore checks. `runtime-sega-master-system-class` keeps
its current snapshot/input/query concerns and both family runtime consumers.
Update workspace/lock manifests and machine/evidence IDs, then regenerate and
check status pages. No machine depends on another machine.

Source anchors are `reference/by-system/sega-master-system/sms-reference.md`,
the Mark III software reference and the compendium, with Genesis Plus GX's
`core/system.c`, `core/io_ctrl.c`, `core/cart_hw/sms_cart.c` and MAME's
`src/mame/sega/sms.cpp` as implementation precedent. This extraction changes
ownership, not clocks, VDP access timing, FM synthesis or compatibility mode.
Locate the existing Sonic Rev 0 dump and verify the complete identity before
its real title/attract test. Keep #149/#220/#1932 separate from split completion.

### Dragon/CoCo inventory, before extraction

The existing family has four profiles, backed by five serialized memory-decode
states: Dragon 32, Dragon 64 compatible/native modes, CoCo 1 and CoCo 2. The
Dragon 64 modes belong to one physical board. Preserve that runtime transition;
never turn the mode into another machine. Retain `machine-dragon-32`; add
`machine-dragon-64`, `machine-tandy-coco-1` and `machine-tandy-coco-2`, over
`common-dragon`. Their fixed construction selects the existing board decode
and PAL/NTSC wiring. No constructor in a concrete owner selects another board
or changes television standard. Shared keyboard/debug/media types remain in
the common layer, not borrowed from Dragon 32.

Move the original `machine-dragon-32/src/lib.rs` engine and `disk_serde.rs`
without changing state fields, clock/VDG/SAM/PIA/ACIA behaviour or media encoding.
Keep private hardware tests beside that common state; each fixed owner gets
synthetic boot/control, identity and partial-step/native-boundary evidence.
The family dispatcher lives in `runtime-dragon/src/machine.rs`; all existing
runtime concern placement stays intact. This explicitly respects
`runtime-internal-shape.md`'s exclusion of Dragon from unrelated normalization.

The version-2 envelope is currently in `runtime-dragon/src/runtime.rs`, not a
separate snapshot module. Decode its original owning machine payload into
common state, validate envelope/profile and embedded board/video standard,
then bind the physical owner before changing any live receiver state. Encode
through an equivalent borrowing machine field if needed, preserving every
serialized field, order and media attribute. Retain `media_serde.rs`, model
IDs, firmware routes, live mounted media and the one family runner.

Before extraction freeze all four profiles and a Dragon 64 native-mode case:
whole envelope/state and full continued frame/audio/time, including SAM phase,
PIA interrupt/keyboard/joystick state, Dragon 64 ACIA and available tape/disc
state. Preserve current restore/reset and serial regressions. Source anchors
are `reference/by-system/dragon-32/1983-inside-the-dragon.md`,
`dragon32-reference.md`, and the CoCo technical/service references in
`reference/by-system/tandy-coco/`; XRoar and MAME are implementation precedent.

After extraction, rerun matched Dragon firmware and both CoCo ROM sets:
Color BASIC 1.2/1.3 plus Extended Color BASIC 1.1 must reach `OK` and execute
a typed `PRINT`. Preserve #2134's ROM-directory selection and #2135's keyboard
symbols rather than treating family tests as proof of either CoCo board.
Register four physical IDs and evidence owners, preserving the existing
family shipping surface. Inspect each owner's own CI tests before completing
#2138 and its #2144 rows.
