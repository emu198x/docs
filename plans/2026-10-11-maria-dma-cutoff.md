# MARIA DMA cutoff before machine ownership wiring

Qualify and implement the bounded end-of-line stop required by the approved
native pipeline. The current native fetch engine runs until a terminating
header; a long list can cross the next request and retain HALT indefinitely.
The old machine helper's 512-byte cap is not a timing model. Issue #196
explicitly requires the per-mode cutoff and bus-release behaviour.

1. Capture the full-clock reference with repeated populated objects long
   enough to reach line transfer/cutoff. Vary short/long direct and both
   indirect widths, object width, ending/continuing zones, CPU fast/slow phase
   and region. Record actual reads, HALT, drive enable and final offset/zone
   transitions. Check the complete capture inventory and retain raw traces.
2. Reproduce the overrun in the native Rust path. Extend the existing saved
   DMA stages with the measured stop sampling and outstanding-latch behaviour;
   preserve byte completion and any late line-RAM writes. Do not substitute
   an aggregate cycle budget. Keep changes inside the unreleased v6/direct
   snapshot layouts and compare interrupted continuation.
3. Qualify DMA enable/disable/restart at CPU-accessible boundaries. A CPU
   cannot issue an arbitrary register write while MARIA owns the bus. Keep
   any internal-input probes distinct from legal CPU bus sequences. Record
   any remaining control propagation needed by machine integration.
4. Run all existing DMA/fetch/clock/playback vectors, affected packages,
   Asteroids, Clippy and formatting. Include a deliberate cutoff timing fault
   to prove the new gate rejects incorrect release. Preserve evidence before
   connecting the machine caller.

Primary source: Atari software guide Display and DMA Timing sections. Reference
precedent: qualified Atari7800_MiSTer revision
`29aaacbbed127c670972c8a0a950ca82dc87e5df`; compare MAME's bounded line rendering
without treating its aggregate budget as an edge-level oracle. No vendored
reference edits or dependencies. Physical NMI, CPU ownership and POKEY gates
remain open on draft PR #1704.

## Cutoff result

Source commit `23d2135e` stops an overlong display list through the existing
shutdown stages. The first regression consumed another header at tick 16300
where the independent trace next drove the descriptor address at tick 16303:

```text
assertion `left == right` failed: case 1 2 1 0 0, event 380
  left: "16300 R 1c78 00"
 right: "16303 A 1803"
```

Line transfer starts a five-native-tick pending cutoff. Byte latches already
issued may complete through transfer plus four ticks. HPOS uses the direct
output strobe and is suppressed on that last edge. Address setup may still
complete at plus five; later fetches are cancelled. Continuing zones release
address drive at plus nine, and ending zones read the next descriptor at
plus 14/18/22, releasing drive at plus 21. CPU phase still determines the
HALT-pad and Sally handoff. Normal terminators keep their own shutdown path.

The pending cutoff is saved in the already-approved, unreleased runtime-v6
and direct `MARIA\x01` layouts. No further version change is introduced.
Sixty saves surrounding transfer/cutoff resume for 1,024 ticks each, checking
bus ownership, reads, both banks and the whole saved state against the live
continuation. Dropping the cutoff field deliberately fails this test.

The full-clock capture contains 896 cases: 256 repeated 128-object lists,
plus 640 lists ending around the cutoff boundary. It covers all four fetch
forms, four widths, ending/continuing zones, fast/slow CPU accesses and both
regions; the long-list rows also cover heights 3 and 16. All cases match:

- 1,000,386 byte consumptions and 1,021,050 bus-address transitions;
- 14,336 HALT edges and 28,672 ownership transitions;
- 7,168 final zone states and 7,168 pairs of 160-cell line-RAM banks.

The bank comparison preserves writes coincident with and after transfer;
they enter the newly cleared construction bank. Six cases retain complete
events for readable failures. The remaining gate checks per-stream counts
and FNV-1a signatures with a complete case inventory. A deliberate one-tick
early cutoff fails at the pending address transition, proving the timing
gate can reject a wrong implementation.

Validation: 110 affected-package tests, the separate 200-frame Asteroids
smoke, Clippy with warnings denied, formatting and capture-script Ruff.
The 768 earlier DMA schedules, 108 clock vectors, fetch and playback gates
remain in the package run. Asteroids still exercises the legacy machine
caller; it does not establish native machine integration.

## Reproduction

Use the qualified reference preparation described in
[`2026-10-10-maria-clock-handoff.md`](2026-10-10-maria-clock-handoff.md).
Compile the own `cutoff_tb.sv` against the untouched reference top-level and
qualified scratch modules; no reference RTL is distributed with this work.
The generator checks compilation before running, rejects missing/unknown
events and validates every expected HALT cycle and both line banks.

From the docs repository:

```sh
python3 plans/2026-10-11-maria-dma-cutoff/capture_cutoff.py \
  ../../emulators/atari/Atari7800_MiSTer/rtl/Maria \
  /private/tmp/maria-clock-handoff/qualified \
  /private/tmp/maria-dma-cutoff/full \
  /private/tmp/maria-dma-cutoff/full/vectors.txt
```

The script writes full raw vectors plus `cutoff-matrix.txt` and
`cutoff-vectors.txt` beside them. Committed source fixtures have SHA-256:

- Matrix: `cb1dbe8430661cb5dece2a9f5fed5c9ebb27c007c83fe952553831d0a9da4348`
- Detailed: `0875b78fdbc9d0d9ec7e755d5ff4356bdf975b8c2a76361532c3eeeda5efd0cc`

Source checks:

```sh
cargo test -p atari-maria -p machine-atari-7800 \
  -p runtime-atari-7800 -p emu198x-atari-7800
cargo test -p machine-atari-7800 --test cart_boot -- --ignored --nocapture
cargo clippy -p atari-maria -p machine-atari-7800 \
  -p runtime-atari-7800 -p emu198x-atari-7800 --all-targets -- -D warnings
cargo fmt --all --check
```

Logs and the two deliberate-fault outputs are in
`/private/tmp/maria-dma-cutoff/`. The raw measurements are implementation
precedent, not production-chip captures. Their provenance and limits are
also recorded in the umbrella primary-source timing evidence note.

## Next boundary

Keep this commit limited to raster cutoff. Step 3, DMA disable/restart and
register propagation at legal CPU boundaries, is the next independent gate.
The current native path gates requests on CTRL, but CTRL delivery and pending
requests still need qualification. Holey-object termination, native machine
ownership, physical NMI timing and POKEY remain open; PR #1704 stays draft.
