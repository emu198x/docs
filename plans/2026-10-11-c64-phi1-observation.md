# C64 Phi1 fetch observation — issue 1713

Lane: engineering-frontier accuracy. Investigation only; no production timing
or schema change is approved here. The uniform colour-RAM guest proves the
bus source is missing, but cannot identify individual fetch slots.

1. Inspect the staged VICE `phi1timing` v2 source and hardware-provenance readme.
   It reads cartridge I/O1 `$DEAD`, so distinguish that decoder from colour RAM.
   Pin all three guest binaries and the source used to interpret their output.
2. Run the unmodified guests in native VICE on PAL/NTSC breadbin, PAL/NTSC C64C
   and old NTSC. Require a real `$D7FF` completion write and retain result,
   raw measurements and the embedded reference for every cycle.
3. Run the same binaries on the four shipping Emu198x boards using real ROMs
   and the existing CPU pin/tick interface. Retain failure evidence with a
   bounded execution limit. Do not infer timing from a successful file load.
4. Separately change only the measurement operand in a derived, identified
   guest to read colour RAM. Preserve native source files. Compare the high
   nibbles of each cycle's capture against native VICE; this separates missing
   I/O1 open-bus routing from missing Phi1 fetch data.
5. Use the measurements to specify the existing fetch-stage extension and
   its validation gates. Do not patch a nibble or shift a framebuffer to pass.
   Ask before additional pipeline/snapshot changes if the implementation
   needs them. Keep the MARIA and pending POKEY work intact.

Exact production paths under investigation:
`crates/mos-vic-ii/src/lib.rs`,
`crates/mos-vic-ii/src/sprite_fetch_chain.rs`,
`crates/machine-commodore-c64/src/machine.rs`,
`crates/machine-commodore-c64/src/memory.rs`.
Reference precedent: VICE 3.10 `viciisc/vicii-cycle.c`, `vicii-fetch.c`,
`vicii-phi1.c`, and `c64/c64mem.c`. Native captures are reference-emulator
observations; upstream hardware-identification notes are a separate provenance
claim and must not be relabelled as new hardware measurements.

## Measured result

All ten native rows match: 640 raw samples across five chip profiles and two
endpoints. The four shipping Emu198x boards complete all eight guests, but
fail 468 of 512 samples. I/O1 returns constant `$FF` (53 wrong slots per board).
Colour RAM returns constant `$2E` (all 63/65 slots wrong), retaining data from
the preceding real-ROM boot display. The low nibble remains correct.

The runner returns failure for the mismatch and restores its temporary source
fragment byte for byte. Nine parser/control checks pass, including a positive
native result and rejection of missing/duplicate rows, short data, invalid
bytes, a fabricated zero mismatch count and an unexpected process exit.
Primary provenance is recorded at
`reference/by-topic/vic-ii/2026-phi1-fetch-observations.md`. The staged corpus
commit is unresolved; individual sources and all guests are hash-pinned.
No third-party guest/source bytes are included in the public evidence: raw
measurement arrays, measurement-only binaries and original tools are retained.

## Proposed correction — approval required

Extend the existing VIC-II fetch and pending-cell stages. Keep the master
clock, CPU pin interface, BA/AEC ownership rules and framebuffer geometry.
This is a coordinated fetch-stage correction, not a replacement renderer.

1. Add an explicit retained Phi1 data byte and eight-bit refresh counter to
   `Vic`. Keep the existing matrix/sprite DMA diagnostic separate so the
   older BA/AEC evidence and public diagnostic do not silently change meaning.
   Refresh resets at the reference's frame-start event and advances on each
   refresh access. Validate its exact phase at frame wrap on every model.
2. Select the actual Phi1 source each clock before rendering: active/idle
   graphics, sprite pointer (even with DMA disabled), sprite middle byte when
   DMA owns that slot, refresh, or ordinary idle. Reuse existing model timing
   and MC/MCBASE state. Preserve distinct Phi2 matrix/sprite bytes and invalid
   ownership handling; a later Phi2 access must not overwrite the Phi1 byte.
3. Separate fetching from the visibility checks in `render_pixels`. Pass the
   fetched graphics through the existing pending cells without an extra memory
   read for rendering. Preserve the distinction between actual active fetches
   and delayed visible idle cells at the far-edge forced-badline transition.
   Any needed descriptor additions stay inside these existing stages.
4. Feed the retained Phi1 byte to colour RAM's upper nibble and unclaimed
   `$DE00–$DFFF` reads. Fitted cartridge/REU/GeoRAM/Ultimate decoders still
   answer first; preserve their existing side effects. Confirm both I/O1 and
   I/O2 fallthrough, fitted-device controls and bank changes with CPU guests.
5. Save the new retained state and advance C64 snapshots from **19 to 20**,
   rejecting version 19. The unapproved sprite-draw proposal also names 20;
   if this correction lands first, that later schema must use 21 or later.
   Never publish two incompatible layouts under version 20.

This extends an existing architectural pattern but changes the snapshot data
schema, so the project's "Breaking changes to APIs or data schemas" approval
rule applies. No production implementation of this proposal has started.

### Alternatives considered

- Reuse the current retained DMA byte and derive refresh addresses from raster
  coordinates. This avoids a new counter but conflates Phi1 observation with
  existing Phi2 diagnostics and makes frame-start/refresh phase implicit. It
  is less clear to validate and restore.
- Replace the machine's clock/bus architecture. The evidence does not require
  that larger rewrite. Existing native-clock stages can represent the missing
  accesses and their distinct observation phases.

### Required gates

- All original and colour-RAM Phi1 rows exact on four shipping boards; old
  NTSC covered at chip level. The colour-derived guest's original full-byte
  classifier is expected to fail: compare raw native bytes instead.
- Preserve the independent 2,176-read uniform colour-RAM check from issue 1713,
  and require the source-byte negative control to change observed output.
- Cycle/address/data traces for all five chips, four banks, refresh rollover
  and frame wrap, active and idle graphics, every sprite's enabled/disabled
  slots, plus mid-line bank/pointer/ECM changes. Use unique source patterns to
  expose selection/phase errors; a uniform-byte guest cannot qualify these.
- CPU reads during ordinary and forced badlines, and after matrix/sprite Phi2
  accesses, must observe the correct Phi1 byte. Preserve all existing BA/AEC
  lead-time and invalid-access regressions and all five strict colour-fetch
  tests required by `c64-ba-aec-handover.md`.
- Save/replay across refresh, sprite halves, graphics and frame wrap; old
  snapshot rejection before mutation. Recheck every strict VIC-II fixture,
  ordinary chip/machine/runtime suites and Clippy. Explain any changed images.
- Run the full compatibility catalogue when its external media volume is
  available; record this as an unmet gate while that volume is absent.
