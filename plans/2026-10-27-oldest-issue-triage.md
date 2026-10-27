# Oldest Emu198x issue triage

## Plan

Review open issues across the Emu198x organisation by creation date, oldest
first. Compare each issue with the current source and its latest scope comments.
Close completed work only with positive implementation and test evidence. Keep
hardware investigations, architecture choices and snapshot-schema changes out
of a quick-fix pass.

1. Fetch the ordered issue queue and review the first 25 entries, #35–#102.
2. Verify likely completions with focused tests and follow their output into
   the machine's audio mix. Record omissions and ignored tests explicitly.
3. After the dependency work lands, close evidenced completions and comment
   where the old scope materially differs from the current source.
4. Commit and push this evidence. Remove task-owned worktrees and build caches
   after checking that their commits are retained remotely.

## Review basis

Source: `emu198x/emu198x` commit
`b4edf0bfcf9cfcb51be8efb80c08c9a676c0fdff`, based on main `020cc3acb`.
The extra commit changes evidence-table rendering, not emulator behaviour.
The organisation-wide query returned 248 open issues on 2026-10-27; its first
25 all belong to the flagship repository.

This is a dated review, not the current status authority. Issue state and the
source repository's status records remain authoritative.

## Ordered findings

| Issue | Finding | Action |
|---|---|---|
| [#35](https://github.com/emu198x/emu198x/issues/35) | ECS programmable counters, blanking, sync-window selectors and horizontal display-window state now exist. The original “only DDF”/“coarse” description cannot serve as an acceptance test. Precise sync/genlock behaviour still needs a bounded source-backed audit. | Keep open; clarify the changed baseline rather than invent a DIW-driven DMA stop. |
| [#43](https://github.com/emu198x/emu198x/issues/43) | Gayle exposes PCMCIA diagnostics and registers, but reports no attached backend or common/attribute/I/O backing. | Keep open; implementing a card and machine integration is substantial. |
| [#46](https://github.com/emu198x/emu198x/issues/46) | Beta Write Sector still immediately reports write protection. Persistence and guest SAVE remain larger than a buffer-copy change. | Keep open; retain the detailed existing acceptance criteria. |
| [#47](https://github.com/emu198x/emu198x/issues/47) | The clone runtime implementations still lack the requested validated TRD media route. | Keep open; controller, firmware and restore ownership require integration work. |
| [#49](https://github.com/emu198x/emu198x/issues/49) | The runtime still has TAP/TZX loading rather than CSW/PZX/SCL routes. | Keep the parent open for its three scoped children. |
| [#52](https://github.com/emu198x/emu198x/issues/52) | Timex rendering and timing exist, but the shared hi-res path still uses zero for clear pixels. The expanded issue also requires separate real-ROM boot/editor proof. | Keep open; no hardware correction without the documented comparison. |
| [#53](https://github.com/emu198x/emu198x/issues/53) | The BASIC loader still enters and waits for the 48K `K` prompt and uses its fixed program address. | Keep open for native 128K editor handling; not completed by tape autoload. |
| [#55](https://github.com/emu198x/emu198x/issues/55) | The peripheral hook does not supply the requested ZX Printer device, timed raster and export path. | Keep open; the expanded hardware/output scope is not a small port stub. |
| [#56](https://github.com/emu198x/emu198x/issues/56) | No ULAplus device/port/rendering path establishes the requested behaviour. Mid-frame colour retention requires the design already called out in the issue. | Keep open; do not bypass the indexed-framebuffer decision. |
| [#57](https://github.com/emu198x/emu198x/issues/57) | Joystick support is separate from the still-missing Interface 2 cartridge media route. | Keep open for cartridge mapping/lifecycle; retain the prior joystick verification. |
| [#60](https://github.com/emu198x/emu198x/issues/60) | No Spectranet/W5100 device path establishes support. | Keep open; offline hardware and host transport need agreed boundaries. |
| [#61](https://github.com/emu198x/emu198x/issues/61) | No IF1 network-line implementation establishes ZX Net. | Keep open; prior scope and dependency clarification remain relevant. |
| [#78](https://github.com/emu198x/emu198x/issues/78) | Cartridge mapper dispatch still lacks MMC2/MMC4. | Keep open; small boards are still new hardware implementations requiring evidence. |
| [#79](https://github.com/emu198x/emu198x/issues/79) | Mapper 66 is still absent from cartridge dispatch. | Keep open; bus-conflict behaviour and a ROM-level check remain prerequisites. |
| [#80](https://github.com/emu198x/emu198x/issues/80) | `Region::Pal` now selects PAL clock divisors, scanlines, APU tables and odd-frame behaviour. The region enum still has no Dendy variant. | Keep open, distinguish implemented PAL from remaining Dendy and selection-path verification. |
| [#81](https://github.com/emu198x/emu198x/issues/81) | The issue already records merged ROM-size and trainer corrections while retaining its metadata/board-policy gaps. | Keep open; those bounded fixes do not complete NES 2.0. |
| [#86](https://github.com/emu198x/emu198x/issues/86) | Mapper 69 has PRG/CHR/RAM banking, IRQ counter and AY-backed 5B audio, clocked into the machine mix. Banking, IRQ, pitch and mix tests pass. | Ready to close the implementation request with explicit test limits. |
| [#87](https://github.com/emu198x/emu198x/issues/87) | Mapper 19 has banking, IRQ, wave RAM and channel scheduling, but explicitly averages enabled channels instead of emitting the multiplexed output requested by the issue. | Keep open; narrow attention to that remaining output approximation. |
| [#88](https://github.com/emu198x/emu198x/issues/88) | Mapper 85 uses the VRC7 variant of the YM2413 core, both board wirings and the VRC IRQ. A keyed FM note reaches the machine mix. | Ready to close the implementation request with explicit test limits. |
| [#90](https://github.com/emu198x/emu198x/issues/90) | Cartridge loading still exposes iNES/NES 2.0 rather than a UNIF parser/board mapping. | Keep open; this is a format plus board-identification feature. |
| [#91](https://github.com/emu198x/emu198x/issues/91) | Existing controller serial paths do not implement the requested Power Pad, Arkanoid paddle and R.O.B. set. | Keep open; each device needs its own protocol and input path. |
| [#92](https://github.com/emu198x/emu198x/issues/92) | The parent explicitly remains a mapper/hardware-test ledger, including unresolved MMC5 findings. | Keep open; closing two implementation children does not complete the ledger. |
| [#100](https://github.com/emu198x/emu198x/issues/100) | Paula still documents instantaneous serial completion. Storing SERPER does not establish baud timing or a host transport. | Keep open; clocked serial plus transport is substantial. |
| [#101](https://github.com/emu198x/emu198x/issues/101) | POTGO clears counters and exposes digital pins; `set_pot_data` injects values. No timed RC scan follows from those methods. | Keep open; do not treat button support as analog paddle emulation. |
| [#102](https://github.com/emu198x/emu198x/issues/102) | Gayle still has no attached IDE drive backend. HDF/RDB boot and source-immutable writes need the existing broader integration. | Keep open; older donor write-back language is not permission to overwrite sources. |

## Executed evidence

All commands used `--locked` and a separate disposable target directory.

| Command | Result |
|---|---|
| `cargo test --locked -p nintendo-nes-cartridge --lib` | 47 passed; zero failures, ignores or filters. Includes the three FME7 tests, three VRC7 tests and five Namco 163 tests. |
| `cargo test --locked -p machine-nintendo-nes --test expansion_audio` | Four passed; zero failures, ignores or filters. Sunsoft 5B, Namco 163, VRC6 and VRC7 reach the machine mix. |
| `cargo test --locked -p emu198x-yamaha-ym2413 --lib` | 11 passed; zero failures, ignores or filters. Includes VRC7 variant behaviour and deterministic snapshot continuation. |
| `cargo test --locked -p emu198x-commodore-agnus-ecs -p emu198x-commodore-gayle -p emu198x-peripheral-sinclair-zx-spectrum-beta-disk -p machine-nintendo-nes --lib` | Respectively 78, 11, 5 and 24 passed. Four NES tests remain ignored. No failures. |

The cartridge tests assert actual bank contents, IRQ transitions and generated
waveform changes. The machine tests require the playing waveform’s peak-to-peak swing to
exceed the silent control by more than 0.01. They can fail without the mapped device/output;
the existence of a module is not the evidence.

These are synthetic tests. We did not run Gimmick!, Lagrange Point, a complete
licensed-ROM matrix or a physical waveform comparison. Closing #86/#88 would
settle their missing-implementation claims, not certify every title or analogue
characteristic. #87 remains open because its requested multiplexed output is
explicitly approximated even though its current tests pass.
