# 1571 lost attention request

The early Timer 1 load control changes when ATN reaches the drive ROM. It
exposes a separate board-decoding fault: reading alternate port A ($180F)
incorrectly acknowledges the request. Correcting that read preserves the
same edge and recovers exactly the working run's 3,114 job writes and 138
motor/head events. The early timer remains deliberately wrong, so its final
frame/audio hashes differ from the production goldens. They are retained as
a diagnostic result, not a catalogue pass.

Run `python3 verify.py` here to check the retained traces. The checks require
nonempty sequences, compare the full job and mechanics sequences, and check
the exact ATN/read/vector/handler/flag events. The two `*-red.log.gz` files
show the machine-level regressions fail before the board correction;
`alternate-green.log.gz` contains the complete 145-test pass.

`instrumentation-attention.patch` applies to source commit `8ef8394c`.
Build its catalogue binary in release mode, then run the normal and early
controls. `instrumentation-alternate.patch` applies to the same base and
includes the port-read correction plus a narrow per-cycle observation
window. These patches are diagnostic only; production PR 1696 contains
only the two machine corrections and their tests.

For all three diagnostic captures:

```sh
EMU198X_CATALOGUE_MEDIA_ROOT=/private/tmp/c64-catalogue-mirror/catalogue-c64/media \
EMU198X_CATALOGUE_FIRMWARE_ROOT=/private/tmp/c64-catalogue-mirror/catalogue-c64/roms \
  catalogue capture --entry bruce-lee-1571 \
  --manifest crates/emu198x-catalogue/manifest/c64.toml
```

Set `VIA_T1_EARLY_NEGATIVE_CONTROL=1` for the `early-*` runs, and omit it
for `corrected-attention`. Capture exits 0 even when it reports a hash
mismatch: read the retained `.out` files; exit status alone is not a pass.
`identities.json` pins source trees, patches' base, trace and binary hashes.
Firmware/media identities are the same as the adjacent C64 integration
plan; no private payloads are included here.

`run-production.py` runs a clean production binary over all three catalogue
shards, preserves each command and exit status, and fails if any shard
fails. Production catalogue results are recorded separately from the
intentionally wrong-timer experiment.
