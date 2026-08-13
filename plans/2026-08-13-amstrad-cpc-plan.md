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

1. **Vendor a CPC reference emulator.** [`RULES.md`](../../emu198x/RULES.md)
   rule 32 makes this a prerequisite, not a cross-check. Nothing under
   `198x/emulators/` covers the CPC, and `multi-system/` does not either —
   unlike the MSX case, where the INDEX pointed at `ares`/`mame` all along.
   Candidates: **Arnold**, **ACE-DL**, or **MAME**'s `amstrad.cpp`. Record the
   choice in `198x/emulators/amstrad-cpc/INDEX.md` before touching code.
2. **Write `knowledge/chips/amstrad-gate-array.md`,** citing
   `198x/reference/by-system/amstrad-cpc/`. That library already holds 139 files
   including the **1990 CPC464 Plus service manual** and the **CPC464 firmware
   guide**, both of which cover the Gate Array — so the chip work is
   prose-sourced rather than deduced.

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

## Open questions

- **CRTC type.** Real CPCs shipped several 6845 variants (types 0–4) whose
  differing behaviour real software depends on. Does `motorola-6845` model a
  type, and which? This is a known CPC compatibility minefield and should be
  decided before step 5, not discovered during it.
- **Which model first.** The 464 is the simplest target and the best-documented;
  the 6128 is the one most learners will picture. Proposed: 464 first, 6128 as
  step 8.
- **Does the CPC want its own `common-amstrad-cpc` driver**, or is it a single
  machine? If the 464/664/6128 split mirrors the Spectrum family's, a shared
  driver from the start would avoid the copy-paste the Z80 cadence campaign
  spent a day undoing.
