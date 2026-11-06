# Emu198x issue triage — batch 2

Lane: engineering-frontier validation and backlog review.

## Plan

Review the next 25 issues after the first batch's #102 cursor, in creation
order: #103–#211. The organisation-wide queue, rather than issue number alone,
defines the order. Read bodies and scope comments against a fixed main checkout.

1. Inspect Amiga boot, media, expansion and platform paths for #103–#118.
   Verify possible duplicate IPF/media trackers before changing issue state.
2. Inspect the CPU/audio/video accuracy tasks #130–#211. Reuse their retained
   probes and primary-reference decisions; do not equate implementation with
   hardware qualification or repeat an already-recorded audit without new data.
3. Run focused existing tests where they can establish a completion or bounded
   gap. Record exact counts, ignored tests and fixture limits. New dependencies,
   architecture or snapshot-schema changes require their existing approval path.
4. Add concrete evidence, scope corrections and cross-links to affected issues.
   Close only positively verified completions or exact duplicates, retaining
   actionable acceptance criteria in the surviving issue.
5. Append findings and the next creation-order cursor here, push to the existing
   draft docs PR #137, and clean task worktrees, caches and processes after
   verifying remote retention.

## Review basis

Source revision: `2e90d5986286f637380ea287bca9e7363df3be7b` (`emu198x/emu198x` main).

## Findings in creation order

| Issue | Verified state and disposition |
|---|---|
| [#103](https://github.com/emu198x/emu198x/issues/103) | **Keep open; narrow to A500+ full-ECS/KS 2.04 boot proof.** The six committed golden rows cover A1000/A500/A1200, not that configuration. A firmware named in an injected hblank test is not normal boot evidence. Generic firmware identity/compatibility remains #829. |
| [#104](https://github.com/emu198x/emu198x/issues/104) | **Keep open.** `Adf::from_bytes` validates ordinary DD/HD sector images; `AdfDiskImage` remains the only drive image implementation. Extended ADF needs raw track structure and a verified media route, not relaxed size checks. Related to the track boundary in #1284, but a separate container. |
| [#105](https://github.com/emu198x/emu198x/issues/105) | **Consolidate as duplicate of #1284.** That newer issue supplies the native-Rust IPF scope, licensing boundary, track/timing/weak-region requirements and real-corpus acceptance. #1192 is closed and covered only honest format identification. IPF support is not completed. |
| [#106](https://github.com/emu198x/emu198x/issues/106) | **Keep open.** The runtime passes bytes to the raw ADF validator; no DMS/ADZ decoder route was found in shell/runtime loading. Gzip-wrapped ADF and Disk Masher decoding are independent slices, not evidence that either boots. |
| [#107](https://github.com/emu198x/emu198x/issues/107) | **Keep open.** `common-commodore-amiga::rtc` is explicitly MSM6242-style. The Ricoh banked clock is not supplied by that register map. The RP/RF naming is covered by the existing primary-library manual; do not rename it by guesswork. |
| [#108](https://github.com/emu198x/emu198x/issues/108) | **Keep open.** All three machine stacks store `Option<AutoconfigBoard>`; the board supports fast RAM, not a multi-device chain. Seventeen passing board tests do not implement multiple boards. Keep the reusable fabric relationship to #832. |
| [#109](https://github.com/emu198x/emu198x/issues/109) | **Keep open; correct the hardware premise.** Parallel data is CIA-A PRB/DDRB, with CIA-A PC/FLAG and CIA-B PRA handshake/status. CIA-B PRB is floppy control. Verified against HRM Appendix F pp. 339–340 and the existing I/O reference. A host peripheral/driver path is still required. |
| [#110](https://github.com/emu198x/emu198x/issues/110) | **Keep open.** The ECS runtime still explicitly reserves A3000 for later Ramsey/Fat Gary and CPU-board integration. A 68030 helper or accelerator profile is not an A3000 motherboard. Preserve #830/#831/#832 prerequisites. |
| [#111](https://github.com/emu198x/emu198x/issues/111) | **Keep open.** AGA currently constructs the A1200 stack; A4000 is reserved catalogue shape rather than a board with 68040/Ramsey/Buster/IDE integration. Preserve the programme relationships rather than introducing an A1200 alias. |
| [#113](https://github.com/emu198x/emu198x/issues/113) | **Keep open.** `Cpu68030` wraps `Cpu68020` and installs CACR/CDIS behaviour. It owns no live MMU field or PMMU decode/translation pipeline; standalone `mmu.rs` helpers do not establish CPU bus integration. |
| [#115](https://github.com/emu198x/emu198x/issues/115) | **Keep open.** CDTV appears as reserved/future catalogue context, not a CD drive/controller and machine path. Neither ordinary floppy support nor OCS composition supplies it. |
| [#116](https://github.com/emu198x/emu198x/issues/116) | **Keep open; remove the stale AGA prerequisite wording.** A1200 AGA exists, but CD32/Akiko/CD/controller/input/firmware integration remains future work in the runtime. There is no evidence of a complete CD32 machine. |
| [#117](https://github.com/emu198x/emu198x/issues/117) | **Keep as the expansion-breadth ledger.** Its latest comment already links the bounded #832–#835 workstreams. No PCMCIA/RTG feature follows merely from CPU pin-level compatibility. No duplicate implementation ticket is needed. |
| [#118](https://github.com/emu198x/emu198x/issues/118) | **Keep as software-qualification ledger.** Six committed golden rows cover a subset of boot/software paths. They are emulator-produced regression baselines, not a complete independent software matrix. Preserve the #828–#830 evidence and fixture requirements. |
| [#130](https://github.com/emu198x/emu198x/issues/130) | **Keep open.** The locked published 6809 source retains `IllegalOpcode`/diagnostic halt and unimplemented cases. The issue already records the merged inherent-alias fixes and the remaining bus-stage/schema proposal. Do not replace all undefined behaviour with NOP or mistake final values for bus accuracy. |
| [#132](https://github.com/emu198x/emu198x/issues/132) | **Keep open; replace missing-feature claims with remaining qualification.** Current CPU/machine code supplies conditional second-byte handling, KEY1 switching, held-button HALT and STOP wake. The 49-pass library run does not cover the full IME/interrupt/joypad/bus/timing matrix; 14 tests remain ignored. |
| [#149](https://github.com/emu198x/emu198x/issues/149) | **Keep open; change size:S to size:M.** Exact locked SN76489 source still duplicates mono in `take_buffer_stereo`. The unchanged probe reproduces 768/1,024 failures and lost pre-write routing. Native accumulation, host stereo and six save-version boundaries exceed the small-mask-change estimate. Existing explicit schema approval remains required. |
| [#158](https://github.com/emu198x/emu198x/issues/158) | **Keep open.** RG6 decoding still chooses digital foreground/background. Nineteen ordinary VDG tests pass, but neither those pixels nor a guessed two-colour lookup supplies the requested phase-dependent composite artifacts. |
| [#166](https://github.com/emu198x/emu198x/issues/166) | **Keep open.** R8 field/raster handling exists; VSYNC still advances at line wrap. The BBC separately applies cursor skew, so chip-level work must preserve that boundary. Twenty-one passing CRTC tests do not establish half-line sync or timed HD6845S skew. |
| [#191](https://github.com/emu198x/emu198x/issues/191) | **Keep open.** The unchanged public pot probe freshly fails 48/64 cases, with all 16 completed-scan controls passing. The issue's retained-charge and clock-transition design requirements still apply; reducing a divider alone is insufficient. |
| [#192](https://github.com/emu198x/emu198x/issues/192) | **Keep open; fix the stale #1705 cross-reference.** Active-filter/timer-delivery qualification remains, but partial accumulator/filter persistence was fixed by merged #1704. The fields are serialized and focused machine continuation tests pass. The timed-stage proposal still explicitly requires additional approval despite its documentation PR being merged. |
| [#193](https://github.com/emu198x/emu198x/issues/193) | **Keep open; focus on runtime mixing.** Fresh guest-to-host replay fails all 32 POKEY-active cases, with 32 silent/TIA controls and all 64 inventories intact. Every runtime leaves a POKEY queue. Native MARIA and POKEY restore work are now merged; neither implements the missing host mix. |
| [#196](https://github.com/emu198x/emu198x/issues/196) | **Keep open for external DMA-ROM qualification.** Native DMA stages are present and covered by the 65-test MARIA run. The requested provenance-recorded timing cartridge/hardware observations were not supplied or executed in this pass. Implementation comparisons cannot close that remaining scope. |
| [#197](https://github.com/emu198x/emu198x/issues/197) | **Keep open for physical revision-matched NMI qualification.** The current sampled-stage test checks 300 vectors representing 32,832 circuit cases and 16,416 pulses. That is positive digital evidence, not a new physical HALT/PCLK/NMI capture. The issue already distinguishes those claims correctly. |
| [#211](https://github.com/emu198x/emu198x/issues/211) | **Keep open.** The locked SN76489 source includes merged tone/TI-zero/TI-slaving corrections, but retains the independent-noise-counter fault. The saved noise-clock proposal explicitly awaits schema agreement. Do not replay completed tone work as a new fix or conceal the remaining phase/output disagreements. |

## Execution evidence

All source tests used `--locked` and a disposable target directory.

| Run | Observed result |
|---|---|
| `cargo test --locked -p machine-nintendo-game-boy --lib` | 49 passed, 14 ignored, zero failures/filters. |
| `cargo test --locked -p emu198x-atari-maria -p emu198x-atari-pokey -p emu198x-motorola-6845 -p emu198x-motorola-vdg-6847 -p emu198x-peripheral-commodore-amiga-floppy -p emu198x-commodore-amiga-autoconfig --lib` | MARIA 65, POKEY 39, AutoConfig 17, CRTC 21, VDG 19 and floppy 41 passed; zero failures/ignores/filters. |
| `cargo test --locked -p machine-atari-7800 --lib pokey_` | Five passed, zero failures/ignores, 41 intentionally filtered. Includes direct and native-phase future-audio restoration. |
| Existing SN76489 stereo probe | Exit 101: `panning does not select the enabled outputs`; 768 failures across 1,024 complete mask/channel cases, 512 failures per side. |
| Existing POKEY pot probe | Exit 101: `pot scans must expose live counts and honour their clock source`; inventory `[16,16,16,16]`, failures `[16,16,16,0]`. |
| Existing 7800 host-audio probe | Exit 101: `cartridge POKEY must contribute to host audio`; 64 cases, 32 failures, all 64 queues undrained. |

The three red probes are reproduced defects, not successful feature tests or
compilation failures. The driver required exit 101 **and the intended assertion
text**. Complete case inventories and nonempty/finite audio controls were also
checked. [Raw observations and source hashes](2026-10-27-issue-triage-batch-02/summary.json)
are retained beside this plan.

The probes were copied unchanged from their existing dated evidence directories.
A disposable Cargo package mapped old import aliases `ti-sn76489` and
`atari-pokey` to the current package names; machine/runtime/shell dependencies
pointed at this checkout. Stereo is a binary; the pot and host probes are Rust
test targets. Every resolved dependency version/source/checksum was compared
with the source checkout's lockfile before execution. Published SN76489,
LR35902 and 6809 sources were also checked against their locked crate SHA-256
values before inspection. No fresh registry version was substituted.

The current 7800 host probe observes 2,095 NTSC TIA samples at its reported
31,400 Hz and 3,202 queued POKEY samples; PAL gives 2,493 at 31,113 Hz and 3,846
queued POKEY samples. These values supersede neither physical measurements nor
the retained historical run; they describe this source revision.

No licensed firmware/media, physical capture, full external-ROM matrix or new
chip timing was exercised here. The six golden-row inventory was inspected,
not rerun. No production code or schema changed.

## Batch boundary

This batch covers the next 25 creation-ordered issues after #102. The next
unreviewed issue is **#215, SMS: Korean mapper variants unsupported**
(created 2026-06-09 16:24:37 UTC). Batch 1 remains recorded in
[the preceding review](2026-10-27-oldest-issue-triage.md).

## Applied actions

Closed #105 as not planned with the existing duplicate label and an explicit
link to open implementation issue #1284; this is consolidation, not completion.
Updated bodies/scopes for #103, #109, #116, #132, #192 and #193. Added evidence
comments to #104, #105, #106, #149 and #191. Changed #149 from size:S to size:M.
All other issues in this batch remain open. Remote read-back verified the
states, edited bodies and labels.
