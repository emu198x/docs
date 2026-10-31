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
