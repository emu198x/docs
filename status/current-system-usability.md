# System usability and evidence

Check the surface you need: native window, capture, script, MCP, or booting a
particular firmware and program. The June 2026 matrix formerly at this path is
historical; its blanket claim that extended systems are headless is no longer
valid. Git retains that dated matrix.

Use these source-repository records:

- [Shipping systems and evidence ownership](https://github.com/emu198x/emu198x/blob/main/docs/status/current-system-usability.md)
  is generated from the crate graph. It identifies shipping crates and their
  own/shared tests; it does not prove that firmware boots or native input works.
- [Native UI and machine-catalogue audit](https://github.com/emu198x/emu198x/blob/main/docs/status/native-ui-catalogue-audit.md)
  records implemented launch and selection paths, checked configurations, and
  explicit limits. For example, VIC-20 has native selection and PAL/NTSC boot
  captures; native menu click-through and audio-device output remain unverified
  by that audit slice.
- [Outstanding work](https://github.com/emu198x/emu198x/blob/main/docs/status/outstanding-work.md)
  routes to the system issue queues. Closed issues are not execution evidence.
- [CI runs](https://github.com/emu198x/emu198x/actions/workflows/ci.yml)
  publish revision-specific `status-evidence` artifacts. Read what ran and which
  external-input checks were skipped before using a green run as evidence.

For a launch, use the selected shipping binary's `--help` and its source/runtime
profile at the revision being tested. For a boot or accuracy claim, retain the
firmware/media identities, configuration, command, and observed result. A window
implementation, generated crate list, or old screenshot does not establish every
machine's current usability. There is no freshly verified all-system usability
matrix at this path.


## CPC464, CPC664 and CPC6128

The three implemented CPC configurations have separate machine crates and
registry entries, with shared hardware and regression code in
`common-amstrad-cpc`. Their family runtime, profile/firmware IDs and v4 save
bytes remain compatible. Each owner has seven direct fixture-free tests;
original complete saves also verify the first three resumed native fields,
audio, clocks and final state. Reset after restore now retains the restored
firmware, tape, expansion ROMs and modified discs.

Local external-firmware tests verify the CPC464 boot banner and text, and
catalogue/run from disc on the CPC664 and CPC6128. Separate headless captures
show each model's own BASIC prompt. These checks do not qualify all CRTC/Gate
Array revisions, regional boards or manufacturer-ID links: the implementation
retains its HD6845S and generic Gate Array baseline. Native launch accepts
`--model`; the CPC adapter still has no Machine-menu selector. The pinned public browser player
currently includes only CPC464; the other board pages omit a player until
their exact profiles are published. Host audio-device output and native menu
interaction remain unverified in this slice.

See [source PR #2216](https://github.com/emu198x/emu198x/pull/2216), the
[ownership decision](https://github.com/emu198x/emu198x/blob/main/knowledge/decisions/cpc-fixed-board-owners.md)
and the [plan](../plans/2026-10-31-cpc-board-owners.md). CI evidence distinguishes
the three owners from the shared family regression suite.

## Atari ST

The implemented 520ST and 1040ST PAL/NTSC configurations now have four fixed
machine owners over `common-atari-st`. Each owner has seven direct tests.
The family runtime retains its profile IDs and exact version-1 save bytes;
eight original colour/monochrome fixtures compare the first three continued
native fields, audio, clock deltas and final state. Restore checks the saved
model, oscillator, physical RAM banks and framebuffer geometry before replacing
the selected machine.

EmuTOS 1.3 tests cover colour and monochrome desktops, Line-A/VDI mouse
behaviour, floppy DMA boot and the family runtime. Separate 600-field captures
verify all four selected configurations. These names describe implemented RAM
bank and clock configurations, not every ST/STF/STFM board revision or optional
hardware fitting. Monitor selection remains a peripheral choice. Version-1
saves still require host-supplied TOS and do not encode its content identity.
Native menu interaction and host audio-device output remain unverified here.

The public pages have model-specific captures. The pinned browser player has no
Atari ST family, so those pages omit an embedded player. See
[source PR #2217](https://github.com/emu198x/emu198x/pull/2217), the
[ownership decision](https://github.com/emu198x/emu198x/blob/main/knowledge/decisions/atari-st-fixed-board-owners.md)
and the [plan](../plans/2026-10-31-atari-st-board-owners.md).

## C64 and C128

Four implemented breadbin/C64C PAL/NTSC configurations and two C128 regions
have fixed machine owners, each with seven exclusive direct tests. Shared
engines and their original regressions remain common evidence. The existing
generic family runtime, profile and firmware IDs, aliases and version-22
save bytes remain compatible. Six complete original saves verify the first
three resumed native fields, audio sample bits, clocks and final state;
restored and direct resets agree. Foreign board/chip payloads are rejected
before replacing live machine state. C64 restore keeps the receiving machine’s
live Ultimate host interface and rejects malformed memory before changing chips.

Real ROMs reach BASIC on all six configurations in separate 200-field captures.
C128 runtime tests additionally verify typed BASIC on both regions, PAL
80-column boot and PAL mid-boot restore. Separate 704×270 captures also
verify 80-column READY on both regions. The public pages select all four exact
C64 variants from the pinned player; C128 pages omit an embed because its core
is absent from that package. Legacy family URLs redirect to their PAL defaults.

These owners identify implemented chip/clock configurations, not every PCB,
early NTSC VIC, CIA date code or C128D fitting. C128 still lacks C64 mode,
2 MHz execution, tape, IEC drives and cartridges. Native menu interaction and
host audio-device output remain unverified here. See
[source PR #2218](https://github.com/emu198x/emu198x/pull/2218), the
[ownership decision](https://github.com/emu198x/emu198x/blob/main/knowledge/decisions/commodore-fixed-board-owners.md)
and the [verification receipt](../plans/2026-10-31-commodore-regional-board-owners/verification.json).


## PET 2001N/3032, 4032 and 8032

Three fixed owners replace the former CRTC/BASIC-2 hybrid. The discrete 32K
2001N/3032 uses BASIC 2; the 50 Hz 4032 and 8032 use matching BASIC-4 editors
and graphics/business keyboards. Existing 40/80 profile IDs remain assigned to
the CRTC boards, with a new explicit discrete profile. Each owner has seven
direct tests. Shared state/video/input regressions remain common evidence.

All three original firmware sets reach READY and execute typed arithmetic.
Complete screen RAM and active monochrome pixels match VICE after that command.
Native frame clocks are 16,640 / 20,000 / 19,992 for these exact editors; the
8032 displays all 250 active text lines. Version-5 saves include pending PRGs,
undelivered audio and the complete board/video phase. Version 4 is rejected
before decoding under the approved exact-restore policy.

Second PIA, IEEE-488/cassette and full 6545/interlace remain incomplete. Native
menu interaction and host audio-device output remain unverified. The pinned
browser package predates this correction, so the new pages omit its hybrid
PET player. See the [current PET contract](../systems/commodore/pet.md),
[source PR #2219](https://github.com/emu198x/emu198x/pull/2219) and
[comparison evidence](../plans/2026-10-31-pet-board-owners/README.md).


## Super NES NTSC and PAL

The implemented NTSC and PAL configurations have separate machine owners over
`common-nintendo-snes`, each with seven exclusive direct tests. One family
runtime retains all three profile IDs; Super Famicom remains an NTSC profile.
These owners do not qualify every PCB/chip revision, CIC behaviour or regional
front-panel electrical differences.

Version-2 saves retain optional IPL firmware even without a cartridge. Loaded
v1 saves keep an exact reader; blank v1 saves are rejected because their omitted
firmware cannot be recovered. Restore validates board, memory and firmware
consistency before installation. Restored hard resets retain IPL and cartridge
SRAM; empty restores clear old cartridge caches, and region changes retain SRAM.
Six immutable original v1 saves compare three resumed native fields, audio bits,
clocks and final state across progressive/interlaced output and all profiles.
Separate v2 checks cover blank/loaded states with built-in and supplied firmware.

The available validation uses project-written cartridges. No original SNES
software was found in the configured local library for this slice; historical
software qualification, native menu interaction and host audio-device output
remain unverified. The pinned browser package has no SNES module, so both
regional pages omit a player and have no new boot capture.

See [source PR #2221](https://github.com/emu198x/emu198x/pull/2221), the
[ownership decision](https://github.com/emu198x/emu198x/blob/main/knowledge/decisions/snes-fixed-regional-owners.md)
and the [plan](../plans/2026-10-31-snes-regional-board-owners.md).


## Remaining board-identity audit

The 48K Oric-1 and Atmos profiles both use 64 KiB of physical DRAM, with ROM
normally selected over the upper 16 KiB. Their old 48-versus-64 descriptions
were wrong. The manufacturer separately identifies a 16K Oric-1 PCB and warns
that PCB and electrical circuit revisions differ; the current profiles do not
qualify all of those populations.

Atari's 5200 service manual identifies CA018087 four-port, CA020108 four-port
universal and CA021374 two-port universal boards with explicit IC/port changes.
The shipping runtime is NTSC-only. The machine API's experimental PAL timing
option does not identify a manufactured PAL board, nor does this audit prove
that no PAL prototype ever existed. The three documented boards still need
individual implementation/qualification.

SG-1000 NTSC, PAL and early TMS9918 SG-1000 II now have three fixed owners
over common wiring, with seven direct tests each and one family runtime.
The SG-1000 II profile is limited to the early TMS9918 configuration. Later
TMS9118/custom-VDP populations remain unqualified. The console's hold button
is real and its current NMI input is exercised by project-written software;
SC-3000 keyboard/PPI support is absent. Complete original v5 continuations are
retained for all three profiles. The PAL audio/time disagreement in
[#2223](https://github.com/emu198x/emu198x/issues/2223) is corrected with independent
nominal CPU/PSG and VDP oscillators. V6 writes, exact v5 NTSC/early-II readers
and explicit v5 PAL rejection follow the approved policy. Native-host pacing
and display metadata use the corrected clocks. The original v5 files remain
immutable; corrected PAL v6 continuation is checked separately. All three
profiles have fresh synthetic backdrop captures, while the pinned browser
family is withheld until its PAL clock correction is published.

See [source PR #2222](https://github.com/emu198x/emu198x/pull/2222), the
[primary audit](https://github.com/stevehill1981/198x/pull/291) and the
[plan](../plans/2026-11-01-sg1000-and-board-identity-audit.md). The Oric/5200 scope corrections do not complete their remaining board work;
the three implemented SG configurations are split without claiming all PCB populations.


## A1200 PAL and NTSC

The two implemented regional configurations have fixed owners over common AGA
wiring. Existing profiles and v66 save fields remain. Each owner has seven
direct tests; eight original save specimens check exact continuation, including
first-field picture, all emitted audio and complete final saves. A fixed shared
resampler kernel removes the host-math difference in pending audio history.
Both regional native captures show the Kickstart 3.1 insert-disk screen.
This does not qualify Workbench, every PCB revision, native menus or host audio
devices. The public player remains A500+A501-only, so A1200 pages omit embeds.

See the [A1200 scope and evidence](../systems/commodore/amiga/a1200.md) and
[source PR #2226](https://github.com/emu198x/emu198x/pull/2226). The aggregate
Amiga entry remains for the still-grouped OCS/ECS implementations.
