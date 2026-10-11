# 6845 register-write evidence

The original public-port probe fails **1,852 of 2,560 cases** before the
correction and passes every case afterward. Its source is `probe.rs`; compressed
CSV captures retain every passing control and failure. `verify.py` recalculates
the expected results, checks the complete input domain and rejects three
deliberately damaged captures.

| Case | Coverage | Before |
|---|---|---|
| R12 high-address readback | S, all 256 byte values | 192 failures |
| R14 high-address readback | Both variants, all byte values | 384 failures |
| R15 writable control | Both variants, all byte values | Pass |
| R16/R17 write protection | Both variants, all byte values | 1,020 failures |
| R6 unused-bit aliases | Both variants, all 128 pairs | 256 failures |

R6 comparisons sample display enable on every character clock for two full
frames. Setting only its unused bit 7 must not change the visible-row count or
the signal trace. The other cases observe actual data-port readback.

Production regressions additionally cover every byte for all 16 writable
registers on both variants, preserving nonzero light-pen values supplied by a
snapshot, rejecting writes to unimplemented register addresses, and loading old
snapshot bytes before applying corrected guest writes. All four new tests fail
before correction. The old readback unit test also needed its setup corrected:
it seeded R16/R17 using software writes that the hardware cannot perform.

## Sources and reference execution

The manufacturer tables are Motorola MC6845 (1977), PDF page 11, Table 2, and
Hitachi U70-A (1987), printed page 147 / PDF page 158. Provenance records:

- `reference/by-topic/crtc-6845/1977-motorola-mc6845-crtc.source.json`
- `reference/by-topic/crtc-6845/1987-hitachi-peripheral-data-book.source.json`

`reference.py` extracts the unchanged R0–R17 cases from MAME's
`mc6845_device::register_w`, with a hash check on the source. Its original wrapper
tests 1,536 cases across R6, R12, R14–R17; all pass. Light-pen reference values
are seeded as `$2A59`, proving preservation rather than assuming zero. Generated
vendor source and executables remain local.

MAME's internal storage for R3/R8 covers a wider chip family; the production
part-specific masks for these two registers follow the manufacturer tables.
This harness establishes the shared write masks and protection, not complete
CRTC raster behaviour.

```sh
python3 reference.py /path/to/mame/src/devices/video/mc6845.cpp /tmp/6845-register-reference
python3 verify.py
```

## Correction and limits

The existing variant logic supplies a write mask for R0–R15 and rejects software
writes elsewhere. Readback selection is unchanged. The correction adds no
fields and does not reject existing snapshots; masks apply on guest writes.
This does not implement the missing light-pen strobe/capture path, full
interlace or skew.

Validation records contain 28 chip passes, 120 affected machine/Gate Array
passes and 16 separately executed firmware-backed passes. The machine run's
30 fixture ignores remain explicit; 16 are exercised in the firmware run.
Affected-package Clippy, formatting and whitespace checks pass. Terminal logs
omit trailing blank lines; their test output is otherwise unchanged.
