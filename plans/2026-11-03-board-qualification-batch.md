# Board qualification continuation

Engineering-frontier accuracy work approved on 2026-11-03: #2237, #52,
#2200 and the original PET 2001 part of #355, in that order. Diagnose existing
failures before adding hardware. Use the Rust skill; keep unrelated checkouts
and the other active sessions untouched.

## Amiga #2237

1. Reproduce both PAL mixed-chip white screens with unchanged Kickstart 1.3
   using runtime-commodore-amiga/examples/fixed_ocs_boot_capture.rs. Retain
   firmware identity, native frame hash and PC/chip-state observations.
2. Compare the failing boot loop with NTSC mixed-chip, PAL rev-5 and 2.04
   controls. Consult emulators/amiga/WinUAE and the primary Amiga references
   before changing hardware. Narrow the first differing observation.
3. Write the root cause and bounded correction here before production edits.
   Expected touch points are common-commodore-amiga-ocs and the implicated
   chip crate only after evidence identifies them. No proposed schema change.
4. Require a failing focused regression, original-ROM non-monochrome boot,
   native-clock and save/restore checks, relevant affected suites and CI.

## Timex #52

Reconsult the TS2068 technical manual, shared ULA/SCLD decisions and Fuse.
Reproduce both ROM startups before modifying rendering. Distinguish documented
modes and colour/brightness evidence; pixel tests must use independent output.
Verify BASIC commands, selected timing and deterministic restore for both
owners. Identify exact files and compatibility effects before code changes.

## Sony HB-10P #2200

First establish the board RAM mirror, I/O masks and chip identities from
primary Sony documentation. openMSX is implementation precedent only. Write
focused positive/negative guest probes. Agree any v10 compatibility change
before implementing it; C-BIOS alone cannot qualify the Sony board.

## Original PET 2001 #355

First identify a concrete original board, ROM map and chiclet keyboard from
primary sources and VICE. Write its proposed owner/profile and save contract
before adding it. Existing 2001N/4032/8032 coverage must remain exact; broader
PET/IEEE/interlace work is outside this bounded addition.

## Workspaces and completion

Source: /private/tmp/198x-qualification-source, branch
fix/board-qualification-batch. Docs: /private/tmp/198x-qualification-docs,
branch docs/board-qualification-batch. Build cache:
/private/tmp/198x-qualification-target. Diagnostics:
/private/tmp/198x-qualification-evidence. Record each root cause, verification
and outstanding limit in durable docs/issues. Commit and push each completed
correction; merge only after required checks pass. Retain diagnostic evidence
and verified remote commits before removing worktrees/caches. Do not delete
unrelated work or the earlier locked investigations.

## #2237: the original capture already contains the graphic

No production hardware or runtime correction is needed. The unchanged source
reproduces RGBA SHA-256
`f28bfeb54f3397f7983077641057b561e150627267c133eaeafbd7552624d436`,
the very value previously labelled white. Both an independent stdlib
zlib/PNG-filter decoder and ImageMagick decode four colours: 21,212 black,
15,200 purple (119/119/204), 3,628 grey (187/187/187), and 402,328 white pixels.
The purple disk body occupies x=294..493, y=142..305. Native ARGB, captured RGBA
and the decoded PNG agree. The inspection viewer shows the original PNG as
white but displays a lossless re-encoding correctly. This is an inspection-path
failure; its decoder mechanism is not established. No emulator fault has been
reproduced. The original files and their hashes must remain intact.

The two strict `kick13_pal_mixed_boot` tests pass for the A500 rev-6a PAL and
A2000CR rev-6 PAL at 650 fields, checking the full original firmware hash,
full-frame identity, actual coloured pixels, native/capture/PNG agreement,
white-frame and one-byte-mutation rejection, and two exact resumed fields plus
complete state equality. A fixture-free test decodes the exact original PNG,
checks the graphic and executes both rejection controls on normal CI runs.
No dependency, CPU/chip behaviour or save-layout change is introduced.

[Evidence](2026-11-03-board-qualification-evidence/) retains the original capture,
its receipt, strict test output and the lossless inspection copy. The older
native evidence's white-screen wording is historical and disproven here.

## Timex: first demonstrated boot fault and bounded correction

The unchanged TS2068 reaches PC $0038 with F4=$01 and reads only $FF from
chunk 0. `MemoryTimex` treats every selected chunk as empty DOCK, even when
FF bit 7 selects EXROM. It also overlays low HOME ROM when FF7 is set without
a matching F4 bit. Both contradict the manufacturer TS2068 Technical Manual
sections 2.1.8.1 and 2.1.13.5 (held PDF and Docling extract). Fuse's TS2068
mapping independently maps the 8 KiB extension across every selected chunk.

First fix only `common-timex-2068/src/memory.rs`: combine F4 chunk selection
with FF7 for CPU reads, mirror the existing EXROM over selected 8 KiB windows,
ignore writes to selected external windows, and override `read_screen` so ULA
fetches continue seeing HOME RAM. Keep existing register fields and save
layout; their saved bits already identify both selections. No DOCK cartridge
implementation or speculative contention change. Add independent truth-table
checks for all 256 selectors, both sources, all chunk edges, readonly external
mapping, hidden HOME RAM and independent screen fetches. Reproduce red first,
then boot the original ROM again and diagnose any remaining failure separately.
Video/brightness and timing metadata remain later parts of #52; no new golden
is accepted until boot and typed BASIC are independently established.

Temporary read-only source clones for later video work:
/private/tmp/198x-qualification-scld and /private/tmp/198x-qualification-ula.
Both still carry retired rule-6 wording; #2178 requires correcting that
wording when those repositories are changed. The current parent decision
retiring the interface-shape ban takes precedence over that stale text.

### Approved Timex v18 contract

Steve chose **write v18 and reject Timex v17** on 2026-11-03. All three Timex
profiles (TC2048, TC2068, TS2068) use v18 for the completed paging/video
correction; other Spectrum-family profiles continue writing/reading v17.
Reject older Timex versions before positional decoding and before mutation.
The byte-identical v17 fixtures stay unchanged as historical evidence of the
old decoder/shifter; do not replace them with new goldens. Current v18 tests
must compare uninterrupted and restored full video/audio/clocks/state, and
must exercise actual board-mismatch rejection with current v18 payloads.
The approved test-only sha2 dependency in runtime-sinclair-zx-spectrum verifies
complete original firmware inputs and the retained historical fixtures.

Affected files: runtime-sinclair-zx-spectrum/src/snapshot.rs,
tests/timex_board_baseline.rs, tests/timex_board_identity.rs, the new strict
original-ROM tests and a binding decision recording this scoped override of
the v17 output guarantee. No non-Timex reader/version change is intended.

Amiga qualification merged in source [#2262](https://github.com/emu198x/emu198x/pull/2262)
as `a7536e6d7400d5aad51b4f9cecdf7456c5bca3cb`; #2237 is closed. All required
checks and all four shards passed on reviewed head
`8d2adfd679d6979e879af9bad399a98ebd713c69`, CI run 41626779886. The retained
`amiga-ci.json` records the exact-head conclusions. The final local suite
passed all three tests, with no failed or ignored tests in the explicit run.

### Shared SCLD video and timing correction

The manufacturer manual Table 3.2.2-1 and §5.2.3 define mode 6 as alternating
**eight-pixel columns** from the primary/secondary files, complementary
ink/paper, bright/flash fixed at zero, and border fixed to paper. The engine
currently alternates individual bits and hardcodes clear pixels to black.
Fuse independently assembles `(data << 8) + data2` for its 16-pixel output,
but sets bright in its colour conversion. For this bounded correction use
the explicit manufacturer bright=0 statement; document the reference-emulator
discrepancy and leave analogue brightness calibration unclaimed.

In sinclair-zx-spectrum-ula, add a read-only `UlaEngine::config` accessor
(no serialized field), correct the documented mode-6 serial ordering, paper
and border, and increment the frame routing version for this rendering change.
Tests cover all eight inks, both bit values, contiguous 8+8 output, complete
512-pixel ordering, all documented mode addresses, timed mode/colour changes,
and unchanged ordinary Spectrum output. Reserved modes 3/4/5/7 retain their
existing unqualified bit decoding; do not claim them as documented modes.
Preserve every causal shifter/latch in saves; no new mutable field is needed.

In timex-scld, derive frame-timing metadata from the selected immutable timing
configuration, expose the existing TS2068 timing constants for the family
wiring to reuse, and correct the stale mode documentation. Test PAL and NTSC
metadata against full counter periods and restore-config selection. Publish
normal stable patch releases through each repository's established release
workflow after CI/review; the main source uses the published versions, with
local Cargo patches only for pre-publication testing. Main integration verifies
v18 phase continuations for all three Timex profiles and retains the existing
non-Timex v17 fidelity suite. Correct stale rule-6 guidance in the extracted
repositories as required by #2178; no interface-shape ban is reintroduced.

### Timex verification and releases

ULA fix [#7](https://github.com/emu198x/sinclair-zx-spectrum-ula/pull/7)
and release #8, plus SCLD fix
[#3](https://github.com/emu198x/timex-scld/pull/3) and release #4, passed
required checks and were rebase-merged. Both packages are published as 0.2.1;
Cargo downloaded the registry packages and the main lock contains their
registry checksums. Source integration is
[#2263](https://github.com/emu198x/emu198x/pull/2263).

The broad affected suite passed 416 test functions with 68 ignored fixture,
diagnostic or known-divergence functions in its default run. Explicit strict
runs passed both original-ROM runtime tests and both TS2068 machine banner/
golden tests. Registry-only tests passed the all-profile 176-case video
continuation matrix, the thirteen-profile version matrix, exhaustive F4/FF
selection, owner rejection and native frame metadata checks. Clippy and
formatting pass. The manufacturer-defined pixel tests failed against the old
ULA; the memory truth table failed against the old paging. Original Timex v17
specimens remain byte-identical. The old stripe golden is retained alongside
native TC2068/TS2068 boot and BASIC captures, firmware identities, logs and
exact-head chip CI ledgers in the qualification evidence directory.

## Sony bounded implementation design

Primary audit: umbrella PR #298, original Sony HB-10P/HB-10B AE/UK manual,
PU-37 schematic 5-11/12/13 and Yamaha S3527 datasheet pages 4 and 8.
The original local MAME `hb10p.zip` contains `10pbios.ic12`, 32 KiB,
SHA-1 `5e7c8eab238712d1e18b0219c0f4d4dae180420d`, matching the independent
openMSX HB-10P manifest. SHA-256 is
`88eff516d7d706b8a4e5a512697444bd5a851e403c82006bcbfc537be3c47976`.
No manufacturer ROM is committed.

1. Add guest-executed red tests in machine-sony-hb-10p/tests/board_decode.rs:
   slot-3 and slot-0 C000/FFFF share bytes in both directions; slot-0 BFFF
   and slot-1/2 remain independent; A2 aliases PPI/PSG and VDP block addresses,
   with adjacent-block negative controls.
2. machine-sony-hb-10p/src/lib.rs adds the slot-0 C000–FFFF RamRegion to the
   existing same-address backing store. common-msx/src/board.rs gains a default
   discrete decoder choice on MsxBoard; only this owner selects S3527 decoding.
   common-msx/src/lib.rs stores that immutable choice outside serde and
   reattaches it through construction/from_state, preserving all live fields.
   Decode supported PPI/PSG/VDP aliases before dispatch while trace records
   keep the original guest port. Do not globally widen other boards' ports.
3. Proposed compatibility choice: Sony writes/requires v11 and rejects v10
   before decoding or mutation; other eight named MSX profiles retain v10.
   Preserve all frozen v10 specimens. Add current v11 round-trip, foreign-board,
   rejection, reset and exact native-video/audio/clock continuation tests.
   This changes execution and topology, so approval precedes production edits.
4. Add strict identified-ROM boot/BASIC/native-output tests in runtime-msx;
   request the existing workspace sha2 as test-only dependency before adding.
   Re-run common-msx, the Sony owner and all runtime-msx suites/Clippy/fmt.
5. Report fitted T6950 and integrated S3527 SSG accurately. This bounded decode
   fix does not establish analogue calibration, a complete T6950 personality,
   printer peripherals or all integrated-SSG differences. Record any concrete
   remaining defect separately rather than treating generic PAL or C-BIOS as
   manufacturer qualification.

### Timex downstream catalogue gate

CI #2263 caught spectrum.toml still declaring frame routing 5 after published
ULA 0.2.1 advances it to 6. Do not bypass the guard or advance that declaration
without evidence. Build the normal optimized catalogue binary, freeze its
identity and the original manifest, and capture all 103 entries with original
firmware/media (preflight: all inputs present). Run at most three captures
concurrently, bounded to 300 seconds each and 90 minutes for the wave. Retain
per-entry output hashes, logs and captures, and require the set of completed
IDs to equal the complete nonempty manifest. Compare both frame and audio
hashes with the existing expectations. If any differs, diagnose it before
changing an oracle. Only after successful captures update the routing
metadata and rerun the exact failed catalogue gate; all fixture-free CI remains
required. The first optimized Manic Miner capture took 38.56 seconds and
matched both existing hashes.

Sony compatibility approved: write/reject at version 11 for HB-10P, reject
its version 10 before decoding, and retain version 10 for other named boards.
