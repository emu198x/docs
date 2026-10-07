# Correct AGA wide bitplane address selection

The corrected superhires guest produces duplicate words in FS-UAE when its
bitplane begins at address 0x30252. Emu198x reads consecutive words instead.
FS-UAE `custom.cpp::fetch32_bpl/fetch64` explains the discrepancy: address bits
1/2 and FMODE select/repeat word lanes within aligned memory fetches.

Keep this change limited to bitplane DMA memory sampling. Preserve grants,
pointer advancement, the one-CCK pending stage, serializer/output phases and
snapshot schema. Sprite DMA is a separate follow-up.

1. Record the exact software observations and source-selection tables in
   `198x/reference/by-system/commodore-amiga/2026-neutral-video-output-phase-observations.md`.
   Check the registered reference code and any available primary specification.
2. Add a failing granted-fetch regression to
   `crates/common-commodore-amiga/src/denise.rs`: all four FMODE modes, all even
   address offsets within an eight-byte block, distinct words, exact pending
   data and unchanged pointer increments. Confirm it fails before the fix.
3. Correct only that file's bitplane read loop. Verify the pending stage keeps
   the actual fetched values across save/restore and later memory writes.
4. Complete source-controlled resolution-sized guest diagnostics under
   `test-data/commodore/amiga/superhires-playfield/`; compare isolated and A5A5
   patterns with three adjacent full-resolution FS-UAE fields. Run common
   chipset and runtime DMA/scroll/transport tests, strict scoped Clippy, and
   available boot goldens. Rebuild the native app for guest captures.
5. Update the existing full-superhires decision and affected changelogs with
   results and limits. Preserve ROM/config/source/output hashes in the local
   validation manifest. No commits or external publication requested.

Completed 2026-10-05. The pre-fix regression fails at FMODE=1, pointer offset 2.
After correction, 129 common unit tests and 56 selected runtime/golden harness
tests pass; two fixed-origin serial tests also pass. Strict Clippy and Python
Ruff pass. The native release app is rebuilt, and eight guest probes agree with
all 24 reference sample rows. The same comparator rejects four pre-fix probes.
The diagnostic builder reproduces identical guest bytes and rejects an invalid
word before creating output. Validation records and input/output hashes:
`/private/tmp/emu198x-superhires-playfield/verification.json`.
