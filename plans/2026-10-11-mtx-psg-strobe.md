# MTX sound latch and PSG delivery audit

Engineering-frontier continuation of source issue #267. The next requirement is
known-program PSG cadence, including the actual I/O delivery path. No additional
snapshot design has been approved; pending MC6809 and PSG designs remain separate.

1. Compare actual `Mtx::io_write/io_read`, MAME MTX sound handlers, MEMU sound
   register/callback code, and the shared MTX primary/reference material.
2. Use a finite Z80 guest to separate OUT ($06) from IN ($03), inspect the actual
   machine PSG through its existing register-image API, and retain each I/O event
   and the chip state. Include overwritten latch values and repeated strobes.
3. Compile the unchanged MAME sound-handler bodies with a recording PSG sink.
   State the scope precisely: this is handler execution, not a full MAME run or
   timing oracle. Record exact source revision and extracted-body hashes.
4. Reproduce a fault before fixing it. If the missing hardware state requires a
   new serialized latch, record the field, strobe behavior, snapshot version and
   continuation tests and ask for the required schema approval. Do not bypass it
   with an unsaved latch or by hiding state in another device's registers.
5. Continue the native-clock cadence comparison after the delivery path is
   correct. MEMU generates audio from floating-point phases at 44.1 kHz and is
   not a chip-clock edge oracle; use the already compiled full XRoar PSG for that
   part and preserve MEMU's limitations.

## Reproduction and reference boundary

The native Z80 guest executes eight I/O operations on each MTX model. All 16
observations fail against the hardware latch semantics. The first unstrobed
OUT6 ($85) changes tone 0 to period 5; the later OUT6 ($A7) wrongly changes tone 1
before IN3. Effective $A7/$12/$93 writes occur 75 T-states before their strobes.
Repeated strobes and an overwritten, never-strobed byte are included.

The manufacturer schematic (service manual Appendix 5, printed page 66/PDF page
70) shows the OUT6-clocked 74LS374 feeding the SN76489A and the separate IN3
control path. Exact MAME handler bodies compile and deliver four expected bytes
across the eight operations. MEMU writes immediately and cannot arbitrate this
hardware fact. No complete MAME or MEMU scheduler was run by this probe.

## Proposed bounded correction — awaiting approval

Recommended: add `sound_latch: u8` to the existing `Mtx` machine state beside
`psg`. Port $06 writes only update this latch. Port $03 reads first deliver the
retained byte with `psg.write(sound_latch)`, then return the current $03 value.
The latch persists after reads and repeated reads deliver it again. The existing
per-T-state PSG cadence remains unchanged. Use zero at construction, matching
MAME; physical power-on contents are unknown.

Save the latch through the existing machine serde state. Advance MTX snapshots
from version 5 to 6 and reject version 5 before decoding or mutating the runtime.
Do not add a custom side channel, unsaved latch, or new chip architecture.

The separately pending PSG phase and stereo designs also propose MTX version 6.
This approval covers only the MTX sound latch. If multiple changes are approved
and integrated together before release, coordinate one schema advance; if any
version ships first, later incompatible layouts must take the next version.
Never reuse a shipped version. Approval of one design does not approve another.

Alternative: defer the correction and leave the inaccurate immediate delivery
explicitly tracked until the related snapshot approvals are resolved. Encoding
this independent hardware byte inside a PSG register is not a valid substitute.

### Exact files and verification after approval

- `crates/machine-memotech-mtx/src/lib.rs`: latch field/construction and port
  delivery; move the retained guest probe into ordinary unit tests or a child
  test module without exposing a public diagnostic API.
- `crates/runtime-memotech-mtx/src/snapshot.rs`: version and rejected-old-version
  test; ensure failure leaves the existing runtime intact.
- Machine snapshot test: save after OUT6 and before IN3, including an overwritten
  prior value. Resume both paths; the future PSG image and audio must agree.
  Test both models, repeated IN3, latch-only writes and arbitrary upper port bits.
- Repeat native-clock cadence validation with a conforming guest after fixing
  delivery. Sweep tone periods/channels against the unchanged XRoar generator;
  use MEMU only within its host-sample observation limits.
- Run machine/runtime/PSG tests, Clippy with warnings denied, both installed-ROM
  boot checks, and inspect exact-head CI before merging.

The test/probe sources and failing evidence are retained in the adjacent folder.
Production source remains unchanged while approval is pending.
