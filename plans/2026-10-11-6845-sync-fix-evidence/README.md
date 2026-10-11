# Full 6845 sync intervals

Source change: `411092c1de02f286ac55086db505268651818739`,
[PR #1736](https://github.com/emu198x/emu198x/pull/1736).
Baseline: `10892b445182cc5d8106cff7cd142f9a64d4cf10`.

| Check | Before | After |
|---|---|---|
| Original public-pin probe, 64 rows | 62 failures | 64 passes |
| Horizontal sweep, 128 combinations | 120 failures | All pass |
| Vertical sweep, 512 combinations | 404 failures | All pass |
| Unchanged MAME width stages, 62 legal cases | Reference passes | Production agrees |

The production tests live in `crates/motorola-6845/tests/sync_outputs.rs`.
They write the public ports and count complete pulses at the public pins.
Width one must produce a pulse; a missing pulse cannot pass through an empty
comparison. The original probe is retained in the sibling
[baseline directory](../2026-10-11-6845-sync-evidence/README.md).

Horizontal cases cover all width encodings on both variants at character
positions 0, 30, 60 and 63 in a 64-clock line. Vertical cases cover both parts,
all encodings, 1/8-raster rows, adjustment lengths 0/1/3/31, and sync at row 1
or the final row 20. Thus pulses can cross a character-row boundary, vertical
adjustment, and frame restart. An additional test compares uninterrupted
execution with repeated save/restore during active pulses.

The fix advances existing pulse counters before starting new pulses. Vertical
counting also precedes adjustment/restart early returns. No new state or
snapshot layout is involved. The two replaced private-helper tests did not
measure full public-output intervals; one encoded the short-pulse error.

## Reference boundaries

`reference.py` extracts unchanged bodies from the hash-identified MAME
`src/devices/video/mc6845.cpp`: `hsync_on` and the active-VSYNC width block inside
`handle_line_timer`. The original harness supplies an integer-clock timer and
starts each pulse at counter zero. It checks 30 nonzero H widths and 32 V width
encodings. This is a pulse-stage comparison, not a full MAME raster or boot.

MAME counts vertical intervals before row/frame processing. Its horizontal-zero
rule conflicts with the original Motorola datasheet, so those two rows are
excluded from the reference comparison. Production retains its two zero-H
controls. Primary width specifications are Motorola 1977 PDF p. 12 and Hitachi
1987 U70-A printed p. 148 / PDF p. 159.

To rebuild the reference locally:

```sh
python3 reference.py /path/to/mame/src/devices/video/mc6845.cpp /tmp/6845-reference
python3 verify.py
```

The verifier requires complete case coverage, recalculates widths, compares
production pulses to reference observations and rejects three deliberately
corrupted/incomplete captures. `manifest.json` records provenance and hashes.
Generated vendor source and binaries remain outside this repository.

## Machine checks

The chip suite passes 24 tests. `machines-tests.txt` records 120 passes across
BBC Micro, PET, CPC and the CPC Gate Array, with 30 fixture ignores.
`firmware-tests.txt` records 16 of those fixture checks explicitly executed in
release mode: BBC boot/display, CPC boot/banner, CPC interrupt/grid diagnostics
and PET boot. The other fixture tests were not claimed as executed. In
particular, the CPC boot check observes both the running Gate Array interrupt
counter and real banner pixels/text. `clippy.txt` records affected-package
Clippy with warnings denied. Formatting and whitespace checks pass.

R7 = 0, live width changes, half-line interlace, skew and other register
semantics are outside these assertions. Passing the diagnostic grid tests does
not establish complete CPC CPU/Gate Array timing accuracy.

Terminal logs omit trailing blank lines; their recorded test output is otherwise unchanged.

## Merged CI evidence

[CI run 38174568373](https://github.com/emu198x/emu198x/actions/runs/38174568373)
completed successfully on the reviewed source head. Its retained ledger records
24 chip passes and 120 affected machine/Gate Array passes, with 30 reasoned
fixture ignores. Workspace totals are 7,804 passes, zero failures, 687 ignored
and 96 skipped for missing fixtures. These omitted tests are not validated by
the green run. Source PR #1736 is merged; the merged tree matches the locally
tested tree exactly and is an ancestor of main.
