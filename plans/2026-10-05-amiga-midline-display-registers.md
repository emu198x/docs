# Discover Amiga mid-line display register errors

1. Read current register/output stages, binding decisions and registered UAE
   handlers. Inspect existing guests and archived tooling before writing code.
2. Add an exploratory builder at
   `test-data/commodore/amiga/midline-display-registers/tools/build.py` using
   the existing SPHX bootloader/ready layout. Exercise a no-op control,
   both directions of resolution changes, FMODE changes and BPLCON4 XOR.
   Allocate enough patterned DMA data for the fastest mode, align the pointer,
   and restore registers before each tested line. Verify deterministic builds.
3. Capture the unchanged native emulator and the recorded full-resolution
   reference fork. Keep three adjacent reference fields, actual origins and
   all RGB samples. Run the existing full-raster comparator unchanged; preserve
   failures and locate their exact beam/sample boundaries.
4. Separate baseline errors, write propagation, fetch scheduling and serializer
   state with source inspection and targeted runtime/chip experiments. Do not
   alter expected pixels or fit an alignment. Record proven issues in the
   primary observations and codebase knowledge with producer/input hashes.
5. If a correction is small and evidence settles the timing, add a failing
   regression before fixing it. Any new persisted pipeline/design change needs
   an agreed design first. Otherwise finish with reproducible discoveries and
   precise unresolved scope, rather than an unvalidated timing change.

This is engineering-frontier accuracy work. No dependencies, admitted corpus,
public APIs, snapshot formats or registered reference snapshots are changed.


Discovery completed: three datasets, 24 deterministic guest builds, 72 complete
common-raster comparisons. The no-op and 16→32-bit fetch controls pass all
variants. Four resolution transitions, 32→64-bit fetch with distinct words,
and palette XOR fail reproducibly. The pointer-reset isolation removes every
later-line mismatch, and the XOR edge is exactly ten 35 ns samples early.
Source inspection establishes separate delayed Agnus/Denise BPLCON0 paths and
visible XOR state missing from the immediate native writes. FMODE slot/copy
state needs further isolation. No emulator changes were made: the correction
requires an agreed persisted-register-stage design rather than an unreviewed
global delay. Primary observations, knowledge limits, source-controlled builder
and strict comparator instructions are recorded. Evidence and hashes:
`/private/tmp/emu198x-midline-display/verification.json`.
