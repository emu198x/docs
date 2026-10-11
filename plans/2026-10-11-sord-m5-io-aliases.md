# Restore the Sord M5's upper I/O aliases

Lane: engineering-frontier accuracy, addressing issue #251's source and knowledge gaps.

## Evidence and bounded design

BASIC-G Appendix H, printed page 279, lists the canonical CTC, video,
sound, seven keyboard-row and joystick ports. The manufacturer M5C-01
schematic shows GA015 taking A4-A7 but no A3, A2, A1 or A0. The CTC
selects its channel with A1/A0; the VDP mode input takes A0. This supports
mirroring each device over a sixteen-port block. MAME's `m5_io` applies
exactly those mirrors (`0x0c`, `0x0e`, `0x0f`).

The current machine instead masks with `0xF8`, making CTC $08-$0F,
VDP $18-$1F and sound $28-$2F inaccessible. Keyboard reads already
implement their A3 mirror. No pipeline, timing, API or snapshot change
is needed: use the complete existing device blocks in the decoder.

## Steps and verification

1. Capture primary-source provenance and a reviewed summary under
   `reference/by-system/sord-m5/`. Preserve the scan hash and provenance;
   distinguish the manual's canonical ports from schematic-derived aliases.
2. Add `crates/machine-sord-m5/tests/io_aliases.rs`. Original ROM-slot
   guests execute real Z80 IN/OUT instructions. Exercise all CTC aliases,
   all VDP data/control aliases and sound aliases in PAL and NTSC.
   Include working canonical controls, keyboard/joystick independence,
   and unmapped reads. Record failing results before changing production.
3. Correct the read/write masks in `crates/machine-sord-m5/src/lib.rs`.
   Replace the stale keyboard and I/O module documentation; describe the
   existing cadence and remove unsupported firmware-handler addresses.
4. Add current `knowledge/systems/sord-m5/overview.md`, citing the primary
   library, and catalogue it in `knowledge/index.md` / `log.md`. Capture
   these ignored notes through the umbrella's private-knowledge manifest.
5. Run machine/runtime tests, all-target Clippy and formatting. Publish
   evidence and source PRs; require exact-head CI and merge verification.
   Close #251 only after its source, knowledge and documentation requests
   are actually fulfilled. Keep unrelated hardware gaps explicit.

## Reference execution limit

MAME's installed stock M5 configuration requires an unavailable FD-5 ROM.
Do not substitute a manufactured ROM or claim full-machine reference
execution. The manufacturer scan and MAME source are the decode evidence;
original guests prove the observed Emu198x defect and correction.

## Status

Primary pages are inspected and captured as reviewed notes/provenance in private
umbrella commit `8915745c` (local, not pushed). The codebase-tied overview lives
at `knowledge/systems/sord-m5/overview.md`, following the current wiki schema's
per-system-directory convention. The private recovery manifest captures it;
its index/log entries are saved without including unrelated working-note edits.

The decoder correction is implemented. Before it, the original guest suite
reports four failures and one passing keyboard/unmapped control. CTC has 96
incorrect reads out of 128; VDP data/control has 96 incorrect cases out of 128;
sound has 16 incorrect port captures out of 32. The status poll fails at $19:
an unmapped $FF falsely appears asserted after 69 T-states, versus 44,062 for
the canonical port. The strengthened test checks equal completion timing.
All five regressions pass with the corrected mask.

Machine/runtime suites pass 38 tests with six fixture-gated tests ignored.
All six were separately run with installed original firmware/cartridges and
pass: BASIC-I reaches Ready; Dig Dug advances; the PAL gameplay check records
1,000 channel-3 interrupts in 1,000 frames and 310 distinct sprite tables.
All-target Clippy and formatting pass. Source exact-head CI and merge are verified.

See [the evidence bundle](2026-10-11-sord-m5-io-evidence/README.md).


Exact tested source head: `45109551ea0c6d8d345fa49e365ac2b447833a12`, based
on the merged trainer correction `ce91eb0d`. The machine/runtime tests and
all-target Clippy were rerun after that rebase. Firmware results precede the
rebase, which changed only the unrelated NES trainer paths.


## Verified merge

[Source PR #1734](https://github.com/emu198x/emu198x/pull/1734) merged as
`dae7a52d708fb8fd47cca69cb7e66037e88d0927`. Its tree exactly matches tested
head `45109551ea0c6d8d345fa49e365ac2b447833a12` and is an ancestor of
`origin/main`. [CI run 38168854358](https://github.com/emu198x/emu198x/actions/runs/38168854358)
passed all required gates. The execution ledger records machine 21 passes
and six reasoned ignores; runtime 17 passes; zero skipped, failed or
unexplained ignored tests. The six local firmware executions supplement
that CI evidence.
