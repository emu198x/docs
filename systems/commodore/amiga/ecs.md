# Amiga A500+ and A600 regional configurations

The implemented A500+ and A600 PAL/NTSC configurations have four fixed owners
over `common-commodore-amiga-ecs`. Each keeps the stock 1 MiB RAM default and
its existing profile and short alias. They still ship through `emu198x-amiga`.

| Owner | Existing profile | Native alias |
|---|---|---|
| `commodore-amiga-a500-plus-pal` | `commodore-amiga-a500-plus-ecs-pal` | `a500-plus` |
| `commodore-amiga-a500-plus-ntsc` | `commodore-amiga-a500-plus-ecs-ntsc` | `a500-plus-ntsc` |
| `commodore-amiga-a600-pal` | `commodore-amiga-a600-ecs-pal` | `a600` |
| `commodore-amiga-a600-ntsc` | `commodore-amiga-a600-ecs-ntsc` | `a600-ntsc` |

The A500+ onboard clock is decoded independently of slow RAM. A600 construction
fits Gayle; A500+ construction does not. Foreign region/Gayle restores reject
before mutation. These owners cover the implemented configurations, without
qualifying every PCB revision, chip population or add-on.

The Amiga family writes v67 snapshots and explicitly reads v66. Legacy A500+
restore corrects only the saved RTC-presence flag, retaining the already-saved
clock history. All other saved fields remain; other models require only the
version-header change. V67 states cannot remove the fitted A500+ clock. Version
65 and older remain rejected.

Sixteen immutable pre-correction cases cover all four boards, progressive and
interlaced video, and boundary/debugger half-CCK saves. Initial and final
payloads permit only the documented flag/header migration; every resumed
video packet, audio sample bit and elapsed-clock observation stays exact.
Each owner has seven direct fixture-free invariant tests.

Native captures reach the Kickstart 2.04/2.05 insert-disk screen at 650 fields.
The NTSC captures were still white at 250 fields, despite the broad
`display-active` detector. The retained actual images establish the narrower
boot observation. Workbench, IDE/PCMCIA devices, native menus and host audio
devices remain outside this qualification slice.

See [source PR #2230](https://github.com/emu198x/emu198x/pull/2230), the
[decision](https://github.com/emu198x/emu198x/blob/main/knowledge/decisions/amiga-ecs-board-owners.md)
and [plan/evidence](../../../plans/2026-11-02-amiga-ecs-board-owners.md).
Public board pages omit embeds until the published player supports exact ECS
profiles; the currently pinned player constructs A500+A501.
