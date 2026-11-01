# SG-1000 owners and remaining board-identity audit

Engineering-frontier continuation of #2144. Broad fixed-owner/private-workspace
split approval persists. Steve approved the PAL correction and v6 policy on
2026-11-01.

1. Confirm SG board populations from original hardware photographs and Sega's
   own model pages. Consult existing PAL clock observations, the TI VDP manual,
   SC-3000 manufacturer schematic and vendored MAME/ares. The donor archives
   are absent. Do not use SC-3000 wiring as a complete SG console specification.
2. Reproduce the SG PAL audio/runtime-rate mismatch in a bounded original tone
   cartridge test. Before extraction, agree independent PAL CPU/PSG and VDP
   oscillators: nominal 3,580,000 Hz and 10,738,635 Hz / 2 respectively. This is
   corroborated by Sega's SC-3000 circuit and the original console clock report,
   but does not qualify every PAL console revision. Preserve NTSC 3:2 phase.
   Recommend v6 saves, exact reading of v5 NTSC/early-II saves, rejection of v5
   PAL saves whose old phase units cannot retain exact continuation. This schema/timing policy is now explicitly approved.
3. Independently inspect Oric's 1984 service manual pp. 8, 10–11, 22–23 and
   parts lists: correct the false Oric-1-versus-Atmos RAM distinction in
   runtime-oric-atmos/src/profiles.rs. Shared 48K-board identity is distinct
   from the separate 16K PCB and historical circuit/PCB revisions. Do not
   manufacture an Oric split from ROM/case/keyboard differences alone.
4. Inspect Atari's 1983 5200 service manual board identities and current code.
   Separate its three documented controller-board revisions from the code's
   unqualified PAL option. No new historical PAL machine claim or API removal
   without evidence/agreement. Preserve the unrelated locked input worktree.
5. Before an approved SG correction/split, retain complete original v5 saves
   and native video/audio/clock/final-state continuations for all three profile
   IDs. Check firmware-less/empty restores, cartridge retention across reset,
   region validation, VDP memory bounds and Z80 walker rehydration. Keep old
   fixtures immutable and prove an intentional corrupt-output control fails.
6. Move shared wiring into common-sega-sg-1000; create fixed SG NTSC, PAL and
   early SG-II owners only once each identity is evidenced. The existing II
   profile may bind the early TMS9918 board; later TMS9118/custom-chip revisions
   remain explicit unqualified work. Use the established closed runtime
   dispatcher, retaining profile IDs, cartridge routes and one family runner.
   Update the narrow runtime-shape decision, registry and generated status.
7. Add direct invariant tests per owner, compare the original continuations,
   run strict Clippy/rustdoc, registry/fixture/ignore guards and full CI. Search
   the local software library and exercise available original software without
   redistributing it; distinguish synthetic tests from historical qualification.
8. Publish current docs and exact public routes/player mappings. Retain legacy
   URLs and do not attach a screenshot to a board it did not prove. Update
   #2144/#2143 with exact scope and evidence. Commit/push green increments,
   merge verified heads and verify the deployed end of the chain.
9. Inspect tracked/untracked/ignored files and remote retention; remove task
   worktrees, clones, caches and processes. Preserve primary checkouts and all
   unrelated work.
