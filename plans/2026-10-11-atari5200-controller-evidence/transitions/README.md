# Scheduled POKEY scan transitions

All **1,748 cases pass** using unchanged Altirra SKCTL write logic, keyboard
scan event, /114 phase helper, event scheduling, matrix closure and Break IRQ
method. The small scheduler implements the event API and advances to each
requested deadline. Audio, serial and analogue side paths are no-ops; no
claim is made about those subsystems or a complete reference-machine boot.
The original source and each extracted block are hashed in `provenance.json`.

- 24 startup cases: four SKCTL values at six absolute origins, including the
  32-bit timestamp wrap. A direct $00->$02/$03 write schedules the first scan
  edge 81 CPU clocks later; Shift and Break sample at offsets 16 and 48 scan
  periods from that edge. The key-1 adjacent pair is accepted after 31 periods
  with debounce disabled.
- 1,368 enable cases: $00->$01 starts the divider without scanning, followed
  by $01->$02 at every delay 0-227, across the same six origins. The scan joins
  the existing /114 phase. An enable at the exact previous divider edge waits
  for the next edge.
- 228 disable cases: every phase 0-113, using either $02->$00 or $02->$01.
  Disabling resets scan address/state and releases key-down, but preserves the
  last KBCODE, pending IRQ and Shift sample. While disabled, releasing the
  external inputs does not clear that Shift sample. Re-enabling via $00
  restarts the divider; via $01 it retains phase. Shift clears at its next
  sampling position, not on the enabling write.
- 128 selection cases: move from a held controller to released inputs and
  back at all 64 scan positions with SKCTL 2/3. The mux changes the returns;
  it does not immediately update the sampled status. Break retriggers after
  it has sampled the released state and later samples a new press.

`capture.csv.gz` contains every case. Positive execution counts (`edges`) and
computed boundary checks make absent events fail. Run `build.py` in a scratch
copy of this directory with the original vendored source available. It writes
the assembled reference code, executable and CSV alongside itself. The
production machine's CPU-write/POKEY-tick ordering and save continuation are
still separate acceptance gates; a scheduler shim does not prove them.

`negative-controls.py` recompiles three deliberate faults. All fail:

| Fault | Failing cases |
|---|---:|
| First edge delayed to 82 clocks | 1,608 |
| Enabling always restarts an 81-clock delay | 1,469 |
| Releasing key-down also clears retained Shift | 292 |

No vendor source or production code is changed. The numeric expectations
combine the published scan slots with event times returned by the reference
write/scheduler path; they do not establish switch propagation delays.
