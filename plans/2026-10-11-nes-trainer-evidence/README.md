# Trainer loading evidence

`complete-results.json` retains all 512 guest-read bytes from each of 56 cases
for the baseline Emu198x, the full Mesen core, and corrected Emu198x. The cases
cross seven existing RAM-backed mappers, two headers, battery on/off and trainer
present/absent. `verify.py` requires that exact nonempty matrix, checks every
byte, and rebuilds each ROM hash from `build_roms.py`.

Run `python3 verify.py`. It proves that the recorded captures have the stated
results; it does not launch either emulator. `guest.rs` and `reference_guest.cpp`
are the executable hosts for recapture. Both require the guest's completion
marker; incomplete execution fails. `build_roms.py` creates original synthetic
cartridges. No external ROMs or emulator binaries are committed.

Baseline parser and guest regressions are red (`parser-red.log`, `guest-red.log`).
The correction passes (`green.log`). The separate static RAM probe has 28 bad
trainer cases and 28 passing no-trainer controls (`baseline.csv`).

Mesen matches 54/56 cases. Its two MMC5 battery/trainer failures are explicitly
preserved as exceptions, also reproduced with freshly empty home directories.
Adjacent source loads trainers before an MMC5 battery routine overwrites RAM
from a zero-initialized vector even if no file was read. Treat this as a source
explanation consistent with the capture, not a traced binary-level proof.

The Mesen binary SHA-256 is
`281ed37fcd1421eef1c5e60e06f1ede360ee89ee214a9c2a0c7c128376395c68`.
It was not rebuilt for this probe. Adjacent source revision:
`fabc9a62174f8734a113df6d244f5539ef6b8fcf`.
FCEUX source revision `a4dafb63f8415ed4d151178c28ab5160e1619839`, `src/ines.cpp`,
provides a second implementation precedent; FCEUX was not executed.

The committed regression extends the capture guest with ordinary RAM writes
and snapshot restoration. The capture guest only reads the initial contents.
The correction initializes the mapper's already allocated RAM; RAM-less
compatibility overlays, NES 2.0 RAM sizing and sidecar-save precedence are outside
this bounded change. It does not advance the save-state version.
