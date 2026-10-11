# Score the missing Game Boy Blargg corpora

The harness now runs the OAM aggregate and all eight singles, and observes the
interrupt-time ROM's visible console. OAM passes singles 1, 3 and 6 and fails
2, 4, 5, 7 and 8; the aggregate returns failure status 2. Normal-speed interrupt
measurements pass. The full interrupt ROM fails on DMG because its second pair
requires CGB speed switching.

This is engineering-frontier verification for source issue #319, not an OAM
hardware fix. The OAM correction is tracked in [#1728](https://github.com/emu198x/emu198x/issues/1728);
CGB remains [#324](https://github.com/emu198x/emu198x/issues/324).

## Agreed scope and implementation

The bounded plan was to execute and score both missing corpora, fix any proven
reporting fault, preserve the original ROMs, run negative controls and existing
Blargg gates, record the result ledger, and file specific accuracy follow-ups.
No dependency, public API, architecture or save-state change was needed.

Source commit `be281cdc426a9337e320e624d9332262cbac3f18` changes:

- `crates/runtime-nintendo-game-boy/tests/phase2_verification.rs`: preserve final
  RAM text; prefer signed RAM status over serial text; score all nine OAM ROMs;
  read the interrupt ROM's visible, scrolled ASCII console; separate its
  normal-speed measurement gate from its full CGB-dependent verdict.
- `test-data/game-boy-blargg-oam-interrupt.md`: corpus identity, commands,
  complete result ledger and limits.

The local-only knowledge overview at the primary source checkout,
`knowledge/systems/nintendo-game-boy/overview.md`, also records the new results.
The durable published copy is the test-data ledger. The primary observation
record lives in the umbrella reference library at
`reference/by-topic/cpu-sm83/2026-blargg-oam-interrupt-observations.md`.

## Reproduced reporting fault

Before the harness correction, `run_until_blargg_verdict` returned only titles
such as `2-causes`. A direct read of the same terminal cartridge RAM contained
the actual `LD DE,$FE00 : INC DE` failure. The initial probe log retains both
views. The corrected harness preserves the terminal report and does not let a
serial pass string override a signed pending/failure RAM status.

The interrupt ROM has no observed serial or cartridge-RAM report. Its original
source declares CGB required and expects measurements at normal and double
speed. The live visible tile map is its verdict channel; the harness observes
that map without guest patches or injected state. Its normal-speed zero/13
M-cycle pair includes interrupt dispatch, vector JP and RET; it is not a
claim of thirteen-cycle dispatch alone.

## Live outcomes

The [evidence directory](2026-10-11-game-boy-blargg-oam-interrupt-evidence/)
contains 25 retained files plus a SHA-256 manifest. All ten external ROMs were
compared byte-for-byte with `retrio/gb-test-roms` revision
`c240dd7d700e5c0b00a7bbba52b53e4ee67b5f15`. No ROMs, third-party source or
compiled reference binaries are bundled.

| OAM case | Runtime advance | Status | Diagnostic |
| --- | ---: | ---: | --- |
| aggregate | 561 | 2 | 01:ok 02:02 03:ok 04:03 05:02 06:ok 07:01 08:02 |
| 1 | 26 | 0 | Passed |
| 2 | 31 | 2 | LD DE,$FE00 : INC DE |
| 3 | 77 | 0 | Passed |
| 4 | 37 | 3 | INC DE at first corruption |
| 5 | 32 | 2 | Should corrupt at beginning of first scanline |
| 6 | 64 | 0 | Passed |
| 7 | 255 | 1 | 00000000; Failed |
| 8 | 44 | 2 | INC/DEC rp pattern is wrong |

Each runtime advance is 17,556 M-cycles. These counts are not directly
comparable with reference `GB_run_frame` calls or boot time.

`interrupt_time` reaches its console verdict after 29 runtime advances:
normal-speed rows `00 00 00`, `00 08 0D`; later rows repeat those values,
followed by checksum `7F8F4AAF` and `Failed`. Its normal-speed gate passes;
its full-ROM gate deliberately fails, anchored to #324.

Unmodified SameBoy `208ba4afabffab9edde416f2dbb8ae459e34adb8` passes the
aggregate OAM test (all eight internal subtests) and standalone tests 1–6 and
8 on DMG-B. Standalone 7 does not reach a signed terminal report within 3,600
frame calls and displays corrupted console content. This is an unresolved
reference-run limitation, not a pass. SameBoy DMG-B exactly matches the
interrupt measurements and failure; CGB-E reports speed 01 for the final pair
and passes. These are reference-software observations, not hardware captures.

The original small `reference_blargg.c` host in the evidence directory uses
Core APIs only. Build an unchanged SameBoy source archive in temporary storage:

```sh
make lib bootroms CONF=release -j4
```

From the directory containing that archive as `SameBoy/`:

```sh
clang -O2 -I SameBoy reference_blargg.c SameBoy/build/lib/libsameboy.a -lm -o reference_blargg
./reference_blargg dmg SameBoy/build/bin/BootROMs/dmg_boot.bin /path/to/oam_bug/oam_bug.gb
./reference_blargg dmg SameBoy/build/bin/BootROMs/dmg_boot.bin /path/to/interrupt_time/interrupt_time.gb
./reference_blargg cgb SameBoy/build/bin/BootROMs/cgb_boot.bin /path/to/interrupt_time/interrupt_time.gb
```

## Verification

- 47 ordinary runtime tests pass. Two new protocol tests reject pending or
  invalid-signature reports, misleading serial text, incomplete measurement
  sets and incorrect interrupt counts.
- Existing eleven Blargg CPU instruction singles, instruction timing, and
  memory timing v1/v2 pass through the corrected report collector.
- Explicit OAM, normal-speed interrupt, and full interrupt runs return exit
  codes **101, 0, 101**. The two red results remain accuracy failures. Their
  ignore reasons use `KNOWN DIVERGENCE` / `KNOWN LIMITATION` with issue anchors;
  they are not recategorised as passes.
- Missing-root and missing-ROM negative runs return 101. Every retained gate
  log was checked for exactly one executed test; a mistyped test-name trial
  that executed zero tests was rejected and rerun with the correct name.
- Clippy with warnings denied, workspace formatting, fixture-guard checks,
  ignore-reason checks and doc-link checks pass. The three Python checkers
  include their own positive/negative self-tests.
- Evidence checks require all nine distinct OAM paths, three positive OAM
  verdicts, and terminal guest reports. The reference standalone-7 absence is
  explicitly excluded from the positive pass set.

The next hardware task is the signal-driven OAM correction in #1728. The
existing source paths do not model corruption from INC/DEC register-pair
operations; they update registers and schedule an internal cycle. Reference
precedent supplies a corresponding corruption event. This explains the first
failure but does not establish all required patterns or exact timing. A
pipeline/schema proposal, if needed, must be agreed separately.
