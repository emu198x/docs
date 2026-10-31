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
before replacing live machine state.

Real ROMs reach BASIC on all six configurations in separate 200-field captures.
C128 runtime tests additionally verify typed BASIC on both regions, PAL
80-column boot and PAL mid-boot restore. The public pages select all four exact
C64 variants from the pinned player; C128 pages omit an embed because its core
is absent from that package. Legacy family URLs redirect to their PAL defaults.

These owners identify implemented chip/clock configurations, not every PCB,
early NTSC VIC, CIA date code or C128D fitting. C128 still lacks C64 mode,
2 MHz execution, tape, IEC drives and cartridges. Native menu interaction and
host audio-device output remain unverified here. See
[source PR #2218](https://github.com/emu198x/emu198x/pull/2218), the
[ownership decision](https://github.com/emu198x/emu198x/blob/main/knowledge/decisions/commodore-fixed-board-owners.md)
and the [verification receipt](../plans/2026-10-31-commodore-regional-board-owners/verification.json).
