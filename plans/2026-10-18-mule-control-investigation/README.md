# Findings

Source baseline: `6cc5d5f9e7fe6507a079f237bc44da0dc95fe25c`. Engineering-frontier validation, no chip or timing changes.

## C64: confirmed PRG-import defect

Both shared `type_string` and explicit Key press/release events execute `PRINT 123` correctly with genuine firmware before media is loaded. The general keyboard path is functional.

The 24,554-byte M.U.L.E. PRG imports at $0801 and has a SYS 2088 launcher. Its unpacker reads $AE/$AF. Direct import leaves that pair at $0000, and RUN ultimately returns to a cleared READY screen. Vendored VICE 3.10 sets that pair to the exclusive payload end in `src/c64/c64memsc.c::mem_set_basic_text`, called by its PRG injection path.

The narrow correction in `format-commodore-c64-prg` preserves the exclusive payload end independently of BASIC relinking. Retesting the same unmodified media reads $67E9 and reaches the animated M.U.L.E. title. Two synthetic tests fail before the fix and pass afterwards; all eight package tests, strict package Clippy and workspace formatting checks pass. No claim of a completed game or verified auction follows from this title-screen observation. The later F5 probes occurred during title animation and do not establish an input failure.

A normal-disk-load comparison was bounded at 1,800 frames and was still loading when sampled ($AE/$AF = $3EC0); it is inconclusive. The confirmed comparison is the vendored VICE import implementation plus the actual before/after launch.

## Atari: separate unresolved startup/display failure

Setup controls work. With zero human players selected, Start reaches the landing message; released-input captures then lose the game display (black by 1,800 frames after Start, blue strip over black by 3,000). The framebuffer changes, so this does not prove that the CPU stopped. The no-input demo reproduces the capture failure without a human-control requirement.

Tracked at https://github.com/emu198x/emu198x/issues/1838 . Disk/SIO behavior, image integrity and original 400/800 versus XL compatibility need a reference comparison. None is an established cause.

## Reproduction material

Scripts use shared headless JSON steps; screenshot paths are local basenames. Supply lawfully obtained firmware and matching media separately. Exact media hashes are recorded without collection paths; commercial bytes and screenshots are not included here. C64 uses PAL breadbin with genuine KERNAL/BASIC/chargen. Atari uses default NTSC 800XL, original OS Rev 2 (1983), BASIC disabled.
