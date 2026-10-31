# Fixed C64 and C128 configuration owners

Continue the approved #2144 programme in the engineering-frontier lane. Split
four implemented C64 configurations (breadbin PAL/NTSC and C64C PAL/NTSC) and
two C128 regions into fixed owners. Preserve the generic family runtime,
profile/firmware IDs, aliases, native/browser interfaces and version-22 saves.
These identify implemented chip/clock configurations, not every PCB revision,
C128D board or early NTSC VIC revision. No new registry dependencies.

1. Recheck RULES.md, ownership/runtime decisions and local Commodore reference
   records. Confirm implemented identities and record unqualified variants.
   Donor archives are absent; use existing family precedents. No chip/timing
   algorithms change; VICE remains a prerequisite for any such correction.
2. Freeze complete original v22 saves and three native continuations for all
   six configurations, including active display, SID audio, held controls,
   arbitrary partial frames and available media/expansions. Verify restored
   execution and reset; deliberately corrupt a fixture to prove failure.
   Reproduce fidelity failures before fixing them and ask before schema changes.
3. Move C64 wiring/tests into existing common-commodore-c64 alongside timing;
   move C128 wiring/tests into common-commodore-c128. The latter imports shared
   keyboard code rather than depending on another machine. Add thin fixed
   owners with checked state binding and no replaceable whole-engine access.
   Runtime dispatch stays within its existing C64FamilyMachine generic shape.
   Preserve wire payloads without enum discriminants. Update direct consumers,
   profile machine IDs, registry ownership and generated current status.
4. Give all six owners exclusive direct tests of board identity, bus/memory,
   video, audio, controls and restore rejection. Run common/owner/runtime/runner
   and fleet tests, strict Clippy/rustdoc, registry/status/fixture/ignore guards.
   Use available original firmware and retain exact identities and results.
5. Publish current docs and six system routes/captures. Browser mapping must
   match exact variants in the existing pinned player. Keep legacy URLs as
   default-profile redirects. Run site tests, build and accessibility; inspect
   source CI evidence ownership, merge exact green heads, deploy and verify
   live route signatures, registry links, browser selections and image hashes.
6. Save verification receipts in this plan's directory, update #2144 and remove
   task worktrees/caches/helpers after checking remote retention, ignored files
   and task processes. Preserve unrelated primary checkouts and locked records.

Old failure modes to test: mismatched profile and hardware payload, wrong VIC/
SID/CIA revisions, first resumed field/audio/clock drift, dropped controls,
firmware/media/expansions after restore/reset, foreign snapshot mutation,
misattributed shared evidence and browser fallthrough to another board.
