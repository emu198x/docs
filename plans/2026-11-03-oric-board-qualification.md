# Oric physical-owner qualification

The complete original BN0130 schematic is identified as circuit issue 7,
C/N63, dated 24-2-84. Its R26 connection is legible: 2.2 kohm between IC22
pin 8 and 0 V. Both original image halves are verified and archived privately;
[the primary audit](https://github.com/stevehill1981/198x/pull/297) records
provenance and the nonmonotonic earlier revision-date inscriptions.

This narrows the electrical population without identifying a physical PCB
issue. The manufacturer's manual explicitly separates those two revision
axes. Oric-1/Atmos product names and BASIC ROMs cannot supply the missing
physical identity.

| Evidence | Established | Still needed before fixed owners |
|---|---|---|
| Manufacturer assembly lists | BN0130 for both implemented 48K products; BN0135 for the unimplemented 16K machine | Match a physical PCB layout/issue to its fitted circuit state |
| Original complete schematic | Circuit issue 7, C/N63; concrete R26 connection for that drawing | Earlier layouts and complete change-state mapping; resolve C39/C35 from a facsimile or corroborated board |
| Amplifier note | LM386 and LM390 alternatives have different component/link fittings | Identify the chosen population rather than treating a product name as its amplifier |
| Current emulator | ROM-model selection, 64 KiB physical RAM, direct reset and a documented Oricutron-derived ULA power-on default | Establish which circuit/PCB fitting the initialization and relevant observable paths reproduce |

The present engine does not record PCB issue, change-note fitting or amplifier
population. Its default power-on mode is explicitly implementation precedent,
not a measured revision-specific reset state. Existing boot output alone
cannot qualify all those boards. No new Oric owner or machine count is claimed.

Next qualification needs a readable physical PCB issue marking and layout,
a fitted-component inventory tied to that board, and the corresponding
schematic/change notes. Then freeze its current digital continuation, define
its exact owner, and test the identified reset/cassette/expansion differences.
Do not create an "Oric-1 board" and an "Atmos board" solely from ROM names.
