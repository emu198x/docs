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
