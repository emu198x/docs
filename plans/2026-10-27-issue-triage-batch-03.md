# Emu198x issue triage — batch 3

Lane: engineering-frontier validation and backlog review.

## Plan

Continue the frozen creation-order queue after #211 with the next 25 entries,
#215–#260. Review current source at `2e90d5986`, latest issue scope and binding
machine/source-immutability decisions before changing metadata or code.

1. Inspect Sega/Coleco cartridge, BIOS and peripheral paths against the issues.
2. Inspect MSX, Sord and SVI media/configuration paths. Check the complete #252
   PAL validation record for possible closure, including its test/fixture limits.
3. Correct historical model-flag/automatic-writeback/format-graduation suggestions
   where current decisions contradict them. Keep distinct board implementations
   and independent transport/parser acceptance separate.
4. Verify likely completions with focused tests; record counts, ignored fixtures
   and real-software evidence separately. Apply only evidenced closures and
   concrete issue updates, then read back the results.
5. Push this batch to draft docs PR #137. Continue creation-ordered batches until
   the initial unreviewed queue is exhausted; retain one cursor per batch and
   reuse the task workspace/build cache, then clean them at completion.

## Findings in creation order

| Issue | Verified state and disposition |
|---|---|
| [#215](https://github.com/emu198x/emu198x/issues/215) | **Keep open; update baseline and size:L.** The SMS dispatch seam exists for Sega/Codemasters, not the five requested Korean families. Replace unqualified detection/fallback claims with independently sourced mapper slices and named images. |
| [#216](https://github.com/emu198x/emu198x/issues/216) | **Keep open; update to BIOS runtime integration.** `new_with_bios`, overlay and $3E control exist; runtime firmware remains empty. Real BIOS code must perform its own checks and handoff; do not invent a universal host checksum gate. |
| [#220](https://github.com/emu198x/emu198x/issues/220) | **Keep open; retain runtime/real-.gg ownership.** Chip mixing is #149. Remove the incorrect drain-time-mask recipe and require actual two-channel host output plus a separately identified real-cartridge smoke. Machine separation is #2140. |
| [#221](https://github.com/emu198x/emu198x/issues/221) | **Keep open; split protocol/presentation scope.** TH/control and Light Phaser support already exist. Named controllers and glasses need their own transactions and host contract; software-selected shutter state is not an unconditional vblank toggle. |
| [#223](https://github.com/emu198x/emu198x/issues/223) | **Keep open.** SG-1000 still owns a flat cartridge vector and 1 KiB RAM; cartridge-space writes do not provide the requested banks/RAM. The eight library tests cover that baseline, not mapper breadth. |
| [#224](https://github.com/emu198x/emu198x/issues/224) | **Keep open; re-anchor to a separate SC-3000 machine crate.** The SG-1000 catalogue has no SC-3000/PPI/matrix. The newer rule 34 supersedes a model-flag proposal. #2143 corrects false naming; it does not implement the computer. |
| [#225](https://github.com/emu198x/emu198x/issues/225) | **Keep open as #224's memory slice.** A dormant 2 KiB branch in SG-1000 would not supply SC-3000. Keep the console's map and test the new machine's sourced RAM/aliases separately. |
| [#228](https://github.com/emu198x/emu198x/issues/228) | **Keep as an expansion idea.** SF-7000 depends on a real SC-3000. Require firmware/wiring/image identity before an implementation; do not invent a .sf7 format or a Format198x graduation merely from an extension. |
| [#229](https://github.com/emu198x/emu198x/issues/229) | **Keep open; clarify MegaCart mapping.** Current Coleco code is flat. The existing community source and openMSX map the fixed lower window to the highest/last image segment. Preserve read-strobe side effects and explicit size/identity rules; this is homebrew rather than factory-cart coverage. |
| [#231](https://github.com/emu198x/emu198x/issues/231) | **Keep open; clarify all four action buttons, not four extra.** `CvController` has ordinary joystick/keypad/two buttons and no spinner. Protocol/timing must be established before sharing machinery with the other analogue devices. |
| [#232](https://github.com/emu198x/emu198x/issues/232) | **Keep open.** No trackball/quadrature state exists in the controller or runtime route. It is a separate Roller protocol/host-input surface even if some machinery is later reusable. |
| [#233](https://github.com/emu198x/emu198x/issues/233) | **Keep open; identify a bounded loader-hardening candidate.** The normal `load_media` path stores arbitrary bytes. Validate new media before mutation, preserve a current mount on rejection and verify the real header extent. Public raw insertion's API contract must not be broken silently or retrospectively invalidate saved data. No guard was implemented in this triage. |
| [#234](https://github.com/emu198x/emu198x/issues/234) | **Keep as the original idea.** The 2600 adapter is not implemented by an open-bus Coleco expansion range or the existence of another emulator core. No new architecture or scope commitment is inferred. |
| [#235](https://github.com/emu198x/emu198x/issues/235) | **Keep open; correct the evidence.** Steering/pedal representation is absent, but an open-bus memory range is not proof of the controller's decode. Source the actual transactions; do not invent a memory-mapped analogue-pot interface. |
| [#240](https://github.com/emu198x/emu198x/issues/240) | **Keep open.** MSX still has no CAS tape media route/read transport; PPI port C's live output is not a cassette implementation. Working subslots do not supply tape. |
| [#241](https://github.com/emu198x/emu198x/issues/241) | **Keep open; correct format/controller boundaries.** No disk-FDC/BIOS/media route exists. Raw sectors, geometry and FAT12 are different layers. #244's completed topology is only a prerequisite where the chosen board uses it; apply the current format-graduation rule. |
| [#242](https://github.com/emu198x/emu198x/issues/242) | **Keep open.** PPI port C reads/writes exist, but machine consumers still use the keyboard row rather than the requested click/CAPS/cassette output paths. Register storage alone is not host audio or a lamp. |
| [#244](https://github.com/emu198x/emu198x/issues/244) | **Close as completed.** Configurable expanded-primary slots, per-page secondary resolution, complemented $FFFF reads and unexpanded RAM semantics are implemented. The targeted negative/positive state distinctions are covered in the passing 47 machine/19 runtime tests. This closes topology, not disk boot. |
| [#245](https://github.com/emu198x/emu198x/issues/245) | **Keep open; update live-state/SRAM baseline.** Seven mapper types now include FM-PAC/Sound Cartridge; FM-PAC exposes SRAM. Version-10 snapshots store the live machine. Rare boards and durable reinsertion remain separate work; automatic source flush conflicts with current rules. |
| [#249](https://github.com/emu198x/emu198x/issues/249) | **Keep evidence-gated.** The M5 cartridge remains flat. The $30 64KBF expansion-RAM latch is not automatically a cart ROM-bank latch. Survey actual images/boards before introducing a mapper or hypothetical format. |
| [#250](https://github.com/emu198x/emu198x/issues/250) | **Keep open as independent tape/printer slices.** Neither path is supplied by the eleven baseline M5 tests. Each needs real guest transactions, proper output/transport and source-immutable persistence/export where applicable. |
| [#252](https://github.com/emu198x/emu198x/issues/252) | **Keep open; narrow to old saves/reference timing, size:M.** PAL boot has retained October evidence and #1725 fixed construction. Two current rate/new-save tests pass; two ROM tests are ignored. Snapshot v5 restores the saved PSG without clock normalization, leaving the documented legacy-state compatibility issue distinct from new-save correctness. |
| [#258](https://github.com/emu198x/emu198x/issues/258) | **Keep open; update to recording/export.** SVI CAS LOAD and tape-1 exist. SAVE needs recorded guest output and codec/round-trip proof; loaded sources must remain immutable. Remove the obsolete missing-LOAD and unqualified flush premise. |
| [#259](https://github.com/emu198x/emu198x/issues/259) | **Keep open; distinct SVI-318 board, size:M.** Primary service manual p. 4.45 distinguishes user RAM/VRAM and 4116/4164 parts; fitted user RAM is 16/64 KiB, not the old 16/32 claim. Current SVI-328 allocates 64 KiB. Rule 34 requires board-specific wiring in the right machine owner. |
| [#260](https://github.com/emu198x/emu198x/issues/260) | **Keep open; correct to SVI-801/FD1793.** The service manual's schematic index names SVI-801 disk control and SVI-806 80-column video. Its p. 4.36 map names FD1793 and $30–$34/$38, contradicting the old uPD765 premise. Drive/DOS/image identity and guest disk boot remain to be established. |

## Verification

All runs used the fixed main checkout, `--locked` and the reused disposable
target directory. Results:

| Command/package | Result |
|---|---|
| `cargo test --locked -p machine-msx --lib` | 47 passed; zero failures, ignores or filters. Includes complemented subslot reads, isolated selected-subslot writes/data and ordinary $FFFF RAM on unexpanded slots. |
| `cargo test --locked -p runtime-msx --lib` | 19 passed; zero failures, ignores or filters. |
| `cargo test --locked -p machine-sega-master-system -p machine-sega-sg-1000 -p machine-coleco-colecovision -p machine-sord-m5 -p machine-spectravideo-svi-328 --lib` | SMS 61, SG-1000 8, Coleco 9, M5 11 and SVI 20 passed; zero failures, ignores or filters. |
| `cargo test --locked -p machine-sord-m5 --test pal_validation` | Two passed, two explicit licensed-ROM ignores; zero failures/filters. The fixture-free tests cover ordinary rate and new-save continuation, not old-clock migration. |

The primary Spectravideo service manual was read on disk, including its page
footers rather than inferred page boundaries. The two relevant printed pages
are **4.45** (RAM/ROM, with the SVI-328 footnote) and **4.36** (I/O map).
Existing shared references already cite these facts. Coleco MegaCart mapping
was compared with the stored community specification and vendored openMSX
implementation; that comparison is not physical qualification.

No new licensed-ROM run, physical capture or production code was added. The
Sord October boot evidence is retained historical evidence, not a fresh claim
that its two ignored tests executed here.

## Batch boundary

Reviewed the next 25 entries after #211. The next issue is **#261: MTX: file loading remains unwired after .mtx/.run parsers landed** (2026-06-09T16:26:07Z).

## Applied actions

Closed #244 as completed and gave it a neutral feature title. Updated 18 issue
bodies/scopes and added evidence comments to #231, #244 and #250. Re-estimated
#215 as size:L and #252/#259 as size:M. Remote read-back verified all edited
bodies, intended states and labels. The other 24 batch issues remain open.
