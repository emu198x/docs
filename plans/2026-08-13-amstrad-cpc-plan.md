# Amstrad CPC — scope

**Status:** Scope for discussion, 2026-08-13. Not a commitment to an
implementation order until the prerequisites below are met and the approach is
agreed ([`RULES.md`](../../emu198x/RULES.md) rule 31).

The CPC is `tier: next` in the Code198x fleet — the same readiness band as the
BBC Micro, VIC-20 and MSX — and the only machine in that band with no core at
all. It is also the largest single gap in the Z80 fleet: 59 catalogued Z80
systems, and the CPC is the most prominent one missing.

## What already exists

Every chip but one is on the shelf, and each is proven in a shipping machine
rather than written speculatively for this:

| Component | Crate | Evidence it works |
|---|---|---|
| Z80 | `zilog-z80` | ZEXDOC/ZEXALL, Tom Harte, FUSE 1351/1356; twelve machines |
| 6845 CRTC | `motorola-6845` | BBC Micro, Commodore PET |
| AY-3-8912 | `gi-ay-3-8912` | MSX, Oric, SVI-328, Pentagon, Scorpion, TS2068 |
| 8255 PPI | `intel-8255` | Acorn Atom, MSX, SVI-328 |
| µPD765A FDC (664/6128) | `nec-upd765a` | ZX Spectrum +3 |

Missing: the **Gate Array** (40007 on the 464, 40010 on the 664/6128 — to
confirm against the service manual) and `machine-amstrad-cpc` itself.

Note for anyone who greps for it: `amstrad-ula-40077` is **not** CPC
groundwork. It is the ZX Spectrum +2A/+2B/+3 gate array — "Amstrad" there is the
manufacturer of the later Spectrums — and is used only by
`common-sinclair-zx-spectrum-amstrad-class`.

## Prerequisites, before any code

1. ~~Vendor a CPC reference emulator.~~ **Already satisfied.** An earlier
   draft of this plan said nothing under `198x/emulators/` covers the CPC. That
   is wrong: `multi-system/mame/src/mame/amstrad/` carries the full driver
   (`amstrad.cpp`, `amstrad_m.cpp`, `amstrad.h`) *and* `ams40041.cpp`, the Gate
   Array itself. [`RULES.md`](../../emu198x/RULES.md) rule 32 is met.

   This is the third time in one session a reference was called missing because
   it lives in `multi-system/` rather than a per-system directory — the same
   mistake [`z80-validation-surface.md`](../../emu198x/knowledge/decisions/z80-validation-surface.md)
   already records making about the Master System. A CPC-specialist emulator
   (**Arnold**, **ACE-DL**) would still add value and should be vendored when
   convenient, but it does not gate the work.
2. **Write `knowledge/chips/amstrad-gate-array.md`,** citing
   `198x/reference/by-system/amstrad-cpc/`. That library already holds 139 files
   including the **1990 CPC464 Plus service manual** and the **CPC464 firmware
   guide**, both of which cover the Gate Array — so the chip work is
   prose-sourced rather than deduced.

**Firmware is staged.** `~/.emu198x/roms/amstrad-cpc/` now holds `cpc464.rom`,
`cpc664.rom`, `cpc6128.rom` (each the 16 KB OS concatenated with its 16 KB
BASIC, per MAME's layout) and `cpcados.rom`. All four are **byte-verified
against MAME's own SHA1s**, which also confirms the concatenation order. The
TOSEC set splits OS and BASIC across `Operating Systems/` and `Applications/`,
which is why they need joining. The Plus OS and BASIC images are staged
unmodified and unjoined: MAME's Plus ROM regions are empty
(`ROMREGION_ERASEFF`) because it sources Plus firmware through the cartridge
slot, so there is no canonical 32 KB layout to check a concatenation against.

## What the Gate Array actually has to do

Four jobs, and they are why it needs its own crate rather than living in the
machine:

- **Video** — mode 0/1/2 (and the undocumented 3), pen/ink selection from a
  27-colour palette, border.
- **ROM/RAM paging** — lower and upper ROM enable, and the 6128's expansion RAM
  banking.
- **`/WAIT` generation** — the defining CPC timing behaviour. The Gate Array
  stops the Z80 so that instruction timings quantise to multiples of 4 T-states.
- **Interrupt generation** — it counts CRTC HSYNCs and raises `/INT` on a fixed
  scanline period (52, to confirm), rather than the VBlank-driven interrupt most
  of the fleet uses.

**The timing job is already expressible.** `Z80::wait` is a modelled public pin
and the core's state machine honours it (`if self.wait { stay in this state }`),
so the quantisation needs no new CPU mechanism — the Gate Array drives a pin
before the tick, exactly as `irq` is driven. This was established while checking
whether wait-state machines threatened the cadence work in
[`z80-machines-should-share-a-cadence-driver.md`](../../emu198x/knowledge/decisions/z80-machines-should-share-a-cadence-driver.md).

**The interrupt source is independently valuable.** The cross-machine interrupt
review that
[`z80-validation-surface.md`](../../emu198x/knowledge/decisions/z80-validation-surface.md)
was opened for needs a machine whose `/INT` comes from somewhere other than a
beam-tied ULA. A Gate Array counting HSYNCs is exactly that, and it would settle
the #887 sampling question on evidence rather than on the Spectrum alone.

## Sequencing

Each step ends green, in the spirit of one commit's worth of work:

1. Vendor the reference emulator; write its INDEX. *(prerequisite)*
2. `knowledge/chips/amstrad-gate-array.md` from the reference library.
3. `amstrad-gate-array` crate: video modes and palette first, with unit tests
   against known pen/ink encodings. No machine yet.
4. Add ROM/RAM paging to the crate.
5. `machine-amstrad-cpc` (464 first — no FDC, simplest memory map): Z80 + Gate
   Array + 6845 + AY + PPI wired, booting to the BASIC prompt.
6. **`cpu_rate.rs` gate from day one**, per the Z80 CPU-rate campaign — with the
   CPC's own expected figure, since `/WAIT` quantisation means a `NOP` does not
   cost the bare 4 T-states here. Getting that number from the reference
   emulator rather than deriving it is the point.
7. `/WAIT` quantisation and the HSYNC interrupt, validated against the reference.
8. 664/6128: FDC via `nec-upd765a`, expansion RAM banking.

## Questions, answered against the reference

**CRTC type: implement type 0, fixed at construction.** `motorola-6845` models
no variant at all today — a plain 6845 with 18 registers. Three independent
references agree on type 0 for the classic machines: MAME fits `HD6845S` and
explicitly *removed* runtime type selection (`amstrad.cpp:76`: "the (runtime)
selection of CRTC type has been removed"); **Arnold** compiles for `HD6845S` by
default (`src/cpc/crtc.c:32`) and enumerates the same taxonomy at `crtc.c:25`;
**Caprice32**'s CRTC header reads "Hitachi HD6845S CRT Controller (CRTC Type 0)
emulation" (`src/crtc.cpp:19`). Arnold additionally carries per-type register
**read/write mask tables** — `HD6845S_ReadMaskTable`, `HD6845R_ReadMaskTable`
and a `UM6845R_StatusRegister` flag — which are the concrete artefact to port if
a variant seam is ever needed. Both are vendored at
`198x/emulators/amstrad-cpc/`; see its `INDEX.md`.
Its type map, left in a comment block at `amstrad.cpp:315-321`, is: type 0 =
UM6845 / HD6845S, type 1 = UM6845R, type 2 = MC6845, type 3 = AMS40489, type 4 =
Pre-ASIC. The first-order behavioural difference is documented at
`amstrad_m.cpp:1769-1797` and is small — which `b1 b0` port combinations are
readable, with only type 1 exposing a status register. So: type-0 semantics, per
machine, and a variant seam added only when a specific title demands it. The one
concrete change `motorola-6845` needs is its register *read* path matching type
0.

**Which model first: the 464, and the question is nearly moot.** MAME's
`cpc464`, `cpc664` and `cpc6128` all call `amstrad_base(config)` and then differ
*only* in RAM size, FDC presence, and which expansion cards are listed —
`cpc6128` is literally `amstrad_base` plus `UPD765A` plus 128K. Building the 464
first does not strand the 6128, because the shared base is most of the work and
`nec-upd765a` is already proven on the Spectrum +3.

**Shared driver: yes, from the start.** Same evidence — one common base plus
trivial per-model deltas is exactly what MAME encodes, and its parent field says
so outright (`cpc664` and `cpc6128` both have parent `cpc464`). Building the
three on a shared driver avoids repeating the copy-paste the Z80 cadence
campaign spent a day undoing.

## The Plus is a separate family, not another model

MAME's `cpcplus(config)` does **not** call `amstrad_base()` — it rebuilds the
machine — and `cpc464p` / `cpc6128p` carry parent `0`, their own root, where
`cpc664` and `cpc6128` descend from `cpc464`. That is the reference stating
structurally that the Plus is a different machine.

What the ASIC adds, from `asic_t` in `amstrad.h` and the notes in
`amstrad_m.cpp`:

- **4096-colour palette** (12-bit) — `PALETTE(config, m_palette, ..., 4096)`
  against the classic machines' 32-entry table.
- **16 hardware sprites**, 16×16, with basic zooming, 15 colours each
  (`amstrad_m.cpp:1312`).
- **Programmable raster interrupt** on any scanline, replacing the classic Gate
  Array's fixed HSYNC counter.
- **Three DMA sound channels** — prescaler, repeat, address, loop count and
  pause per channel — driving the AY autonomously.
- **Hardware split screen** and **horizontal soft scroll**.
- An **unlock sequence**: the Plus features stay invisible until a magic
  sequence is written, which is how the machine stays CPC-compatible.
- **AMS40489** CRTC (type 3) with an integrated PPI (`ams40489_ppi`).

The **GX4000** is the same hardware as a cartridge console; MAME shares the ROM
definition outright (`#define rom_gx4000 rom_cpc6128p`).

Both are now catalogued in Code198x as `amstrad-cpc-plus` and `gx4000`,
`tier: planned`. Treat them as a later phase with their own machine crate — a
compatible Z80 front end on a substantially different video and audio machine,
not a fourth entry in the classic line.
