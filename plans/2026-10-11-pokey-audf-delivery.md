# Qualify POKEY AUDF delivery at pending borrows

Engineering-frontier continuation of the POKEY faults exposed during MARIA
integration. The additional staged design is proposed separately; this slice
changes no production clock, API or snapshot contract.

1. Reuse the pinned connected borrow/output harness and its complete checks.
   Extract the unchanged four AUDF write cases and SetAUDFP1 method into a
   bounded wrapper. Reject other registers and unsupported paths.
2. Exercise all four unlinked channels, both base clocks and the two channels
   that accept the direct clock. Write each divider boundary 0/1/15/255 over
   every old boundary value, one/two/three clocks before the first pending
   borrow. Check that an AUDF write preserves the pending event, selects the
   correct subsequent reload, and reaches the renderer and IRQ observers.
   These 480 cases avoid coincident CPU-write/event ordering.
3. Reject deliberate removal or extension of the delivery delay. Check complete
   nonempty case inventory, exact timed events and output. Retain source hashes
   and observations; extracted implementation remains in local scratch.
4. Write primary observations to `reference/by-system/atari-8bit/`, then results
   here. Run synthetic verifier guards, Ruff and C++ warnings-as-errors. Do not
   extend these results to linked reloads, STIMER, control writes or power-up.

Exact files: adjacent `2026-10-11-pokey-audf-delivery/` capture/driver/tests and
bounded evidence, plus the primary note. This qualifies an input boundary for
the proposed stages; it does not implement those stages before approval.

## Results

All **480 reference cases** pass, with **1,920 borrow events**, **1,344 IRQ
assertion calls** and **1,920 output transitions**. The pending borrow stays
at its original deadline. Writes two or three clocks before it affect the
next reload; a write one clock before it affects the following reload instead.
Unchanged-value controls preserve the old schedule. Both early and late
delivery mutations are rejected at their respective boundary.

The public current-chip probe fails **24 of 96 cases**. Both regional
frequencies, four old dividers, four new dividers and three lead times are
covered. Every changed value written one clock before the IRQ affects its
next reload too early; the other 72 cases pass. The test warms up through two
actual IRQs and checks the three post-write IRQs, avoiding assumptions about
STIMER's initial delivery phase. Its failure is:

```text
assertion `left == right` failed: AUDF writes must retain the in-flight reload
  left: 24
 right: 0
```

The cause is the immediate AUDF register value being read by the next timer
reload without a retained delivery stage. Source `91bb2ffe` is the fast-period
correction, merged as `03372dda`; that settled-period fix does not establish
register timing. The temporary integration test exits 101 and is removed
after capture, leaving the source worktree unchanged. The failing diagnostic
is retained here, not installed as a production test.

Nine capture-guard tests pass. They reject empty, missing or duplicate
inventories, incorrect write/event/output times, absent IRQs and premature
reloads. All three new reference executables compile with warnings denied.
Ruff, Rust formatting and diff checks pass. The prerequisite connected-borrow
capture reruns and passes all four variants during reproduction.

The primary observations are in
`reference/by-system/atari-8bit/pokey-audf-delivery.md`; source hashes are in
`summary.json`. The original implementation is distributed through
[Altirra's author](https://www.virtualdub.org/altirra.html). This is a reference
implementation comparison, not independent hardware measurement. It does not
qualify linked reloads, coincident CPU writes, STIMER/control/reset delivery or
power-up. Issue 192 remains open and the additional stage/schema proposal
remains pending approval.

## Reproduction

```sh
PYTHONDONTWRITEBYTECODE=1 python3 \
  plans/2026-10-11-pokey-audf-delivery/capture.py \
  ../../emulators/atari/altirra /path/to/local-output
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-pokey-audf-delivery -v
```

`baseline.txt` contains complete observed data, not reference source. The
temporary generated C++ remains in the specified local-output directory.
For the current-chip diagnostic, copy `probe.rs` to an otherwise absent
`crates/atari-pokey/tests/audf_delivery_probe.rs` in an isolated checkout, then
run:

```sh
cargo test -p atari-pokey --test audf_delivery_probe -- --nocapture
```

The expected current acceptance status is **failure**, Cargo exit 101. Remove
only that newly installed test file afterward. `chip-red.log` retains all 96
observations and the failed assertion.
