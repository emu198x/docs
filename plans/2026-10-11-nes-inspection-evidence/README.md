# NES inspection mirroring evidence

Five source regressions compare the existing screen inspector with actual 6502
PPUDATA reads. The baseline has four failing regressions and one passing vertical
control (`red.log`). The corrected inspector passes all five (`final-guest.log`).
Each mode checks every byte of the logical $2000-$27FF region. The transition
regression runs vertical, horizontal, lower, upper, then vertical on one machine.

`generate.rs` contains the same original guest generator as the regression,
without the test runner; it emits four mapper-1 iNES cartridges. Its final guest
explicitly initializes the host handshake bytes before use. `red.log` predates
that fixture initialization; the mismatch occurs in inspection, after all guest
reads have passed their independent expected-byte assertions.

`reference_guest.cpp` runs these cartridges in the full Mesen core, waits for the
completion marker, then reads all 2048 result bytes at CPU $6000-$67FF. Every
mode matches the expected page wiring; both captures are identical.

The prebuilt Mesen core was not rebuilt for this probe. Its exact binary hash is
in `mesen-results.json`. Adjacent reference source is Mesen2 commit
`fabc9a62174f8734a113df6d244f5539ef6b8fcf`; this does not establish the binary's
source revision. No external ROM or emulator binary is included here.

To recheck captures and rebuild the original ROMs: `python3 verify.py`.
To rerun the reference, compile with the Mesen2 root and Core include folders,
link the prebuilt core, then call `reference_guest <scratch-home> <rom>` from a
directory containing `MesenCore.dylib` (its current install name).

This evidence establishes the inspection mismatch. It does not claim full MMC1
hardware validation, an entire scrolling screen capture, or four-screen RAM support.
