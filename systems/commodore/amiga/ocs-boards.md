# A1000, A500 and A2000 regional boards

Eight fixed owners cover the implemented A1000, A500 rev 5, A500 rev 6a and
A2000CR rev 6 configurations, each PAL and NTSC. Shared wiring belongs to
`common-commodore-amiga-ocs`; each machine crate fixes its board and region.
The family still ships as `emu198x-amiga`.

| Board | Stock chip RAM | Existing profiles | Hardware distinction |
|---|---:|---|---|
| A1000 PAL/NTSC | 256 KiB | A1000 OCS PAL/NTSC | Bootstrap ROM, writable control store and lock latch; original A1000 Agnus |
| A500 rev 5 PAL/NTSC | 512 KiB | Stock A500, A501 and GVP A530 in each region | Early original Agnus; optional expansion clock/RAM |
| A500 rev 6a PAL/NTSC | 512 KiB | Existing “maxed” A500 in each region | 8372A Fat Agnus with OCS Denise; the maxed RAM layout is modified hardware |
| A2000CR rev 6 PAL/NTSC | 1 MiB | A2000 OCS PAL/NTSC | 8372A, OCS Denise and onboard MSM6242B RTC |

A501 and GVP A530 are add-on profiles of the existing early-A500 implementation.
Firmware revisions and optional RAM do not select another motherboard. The
maxed profile retains 1 MiB chip, 512 KiB slow and 8 MiB fast RAM; the raw
rev-6a owner defaults to factory 512 KiB chip RAM. It must not be described as
a factory 1 MiB A500.

All eighteen family profile IDs and short aliases remain. New machine IDs
name the eight owners; save envelopes retain their original model identity.
The shared dispatcher preserves trace, query, media, input and debug surfaces.
The public browser player is still the published A500 PAL+A501 configuration;
it does not validate the other boards.

## Hardware authority and limits

Commodore's A500 service manual PN 314981-04, PDF 14 / printed 2-9, distinguishes
rev-5 and rev-6a Agnus and DRAM populations. Its 1 MiB chip-RAM description is
an unsupported modification. A2000 rev-6 schematics PN 314135-02 (August 1989),
PDF 4 / printed parts 1, identify PAL/NTSC boards, 8372, 8362 Denise, Buster
U800 and MSM6242B U801. Service update issue 25, item 25/3-2.1, PDF 43, records
the rev-6 factory 1 MiB jumper configuration.

Primary sources live in `reference/by-system/commodore-amiga/` under
`a500-service-manual-pn-314981-04-oct-1990-text`,
`a2000-system-schematics-rev-6-pn-314135-02-1989-08`,
`amiga-an-update-for-the-service-technician` and `a1000-service-manual`.
WinUAE supplies implementation precedent, rather than primary prose authority.

These owners do not qualify every PCB or chip population. Earlier German
A2000A and PCB 312720-01 boards remain separate, unimplemented identities.
Buster/Zorro backplane accuracy, broader software and peripheral compatibility
are not established by moving the existing wiring into fixed owners.

## Save fidelity and deterministic evidence

The A2000's onboard clock is accessible without slow RAM. An owned CPU guest
writes seconds=5 and reads it back in both regions; both A501 positive controls
and unexpanded A500 absence controls distinguish fitted from absent hardware.

The family writes v68 and explicitly reads v66/v67. Only the old A2000
RTC-presence flag is corrected for those readers. The existing A500+ v66
correction remains. Clock history and every other saved field survive.
Malformed current saves reject before mutation. Versions 65 and older reject.

Raw snapshots carry the fixed owner's Rust type, without adding a serialized
field. A family envelope checks the saved model independently: expanded A500
and A2000 chip payloads can otherwise be indistinguishable. A raw snapshot
from another owner cannot be passed directly to a machine of a different type.

The original engine at `c06321677cde6b4aea0211197eb8436ceae0a1a7` produced
56 frozen v67 cases before either the RTC correction or extraction. They cover
all twelve remaining profiles, progressive/interlaced fields, real debugger
half-CCK cuts, held/released controls and both A1000 bootstrap/WOM phases.
The corpus verifies exact native picture, audio, clocks and complete initial/
final saves, allowing only the approved header and clock-presence migration.
ZIP compresses 177 original files from 1.27 GB to 2.75 MB; every decompressed
identity is checked. Direct-test firmware must equal those archived originals.

Each owner also has seven direct invariants for identity, chips, stock RAM,
guest execution, native field periods, memory wiring, active/inactive output,
controls and precise continuation. Synthetic guests establish those bounded
properties; original-firmware boot captures are separate evidence.

## Original firmware

A1000 PAL and NTSC reach the Kickstart 1.2 insert-disk screen with stock
256 KiB chip RAM after the original disk loads through the native bootstrap.
WOM handoff occurs at fields 1388/1655; the disk is then ejected. Both
2600-field captures retain the original handoff rather than patching CPU/RAM.

A500 rev-5 PAL/NTSC reach the 1.3 insert-disk screen at 650 fields. Rev-6a
PAL/NTSC and A2000CR rev-6 PAL/NTSC reach the 2.04 r37.175 screen at 650 fields.
The rev-6a captures explicitly fit factory 512 KiB, rather than its legacy
maxed runtime preset.

Kickstart 1.3 remains a known gap on the PAL 8372A/OCS Denise configurations:
both remain white at the same bound. The untouched pre-extraction engine
reproduces the same complete framebuffer hashes. NTSC 1.3 and regional 2.04
are positive controls. The cause remains under investigation; successful 2.04
captures do not qualify 1.3. See the [native receipts and scope](../../../plans/2026-11-02-amiga-remaining-board-owners/native-evidence.md)
and [source PR #2236](https://github.com/emu198x/emu198x/pull/2236).
