# A500+ and A600 fixed regional owners

Engineering-frontier continuation of #2144 under the approved fixed-owner
split pattern. Start from source 85f99c20e45814daba85197bfc0ab662248b811b.
The A1200 website PR #43 is still gated by the missing public v0.46.0 manifest.
The three named donor archives are absent; no archived cycle code will be ported.

1. Re-consult RULES.md, each-machine/runtime-shape decisions and primary A500+
   and A600 board evidence. Preserve implemented configurations without claiming
   every PCB/chip fitting. Existing A500+ RTC wiring is suspect: the service
   manual (PDF page 3) says onboard RTC; machine construction gates decode on
   slow RAM. Reproduce with a guest-visible register write/read invariant before
   changing production. Retain a red result and original engine fixtures.
2. If the RTC discrepancy is confirmed, agree the save contract before any
   schema/restore-policy change. The RTC history already exists and advances;
   inspect whether a deterministic legacy migration can preserve it. Do not
   silently normalise legacy bytes or weaken exact fixture assertions.
3. Freeze original complete v66 saves and native continuations for four
   profiles, progressive/interlaced video and real debugger half-CCK cuts.
   Reuse the project-owned A1200 synthetic program with stack inside 1 MiB;
   record guest writes, held/released controls, persisted media, video packet
   hashes, every audio sample, clocks and final state. Capture only from the
   untouched baseline, create-new-only. Prove live/restore equality and a red
   control. Any approved correctness migration gets separate explicit evidence.
4. Move shared ECS wiring to common-commodore-amiga-ecs::EcsCore<C> and create
   fixed A500+ PAL/NTSC and A600 PAL/NTSC owners. Markers fix region, Gayle
   fitting and stock 1 MiB default; retain the saved field layout. Reject
   foreign region/Gayle state before mutation and remove A1000 constructors.
   Keep existing rich machine/debug surfaces and the shared generic runtime.
5. Replace grouped ECS dispatch with four concrete owners, validate profile
   against owner, and update construction, reset, restore, native/browser/debug
   consumers. Preserve profile IDs and aliases. Update all existing tests and
   regression scripts. Add seven direct invariant tests per owner and explicit
   construction/atomic restore tests. OCS and AGA behaviour stay outside this
   extraction except any explicitly approved family save-envelope versioning.
6. Add four registry IDs, retain aggregate Amiga for unsplit OCS. Regenerate
   status and verify no machine-to-machine dependencies. Run appropriate tests,
   strict Clippy, consumer builds, guards and full exact-head CI. Linear PR
   history is required. Push completed commits and merge only verified heads.
7. Retain captures/provenance, docs and tracker updates. Public board pages
   require exact browser profiles or omit embeds. Keep the existing release
   manifest gate; coordinate the pending A1200 site branch without bypassing it.
8. Preserve recovery/evidence remotely, inspect tracked/untracked/ignored files,
   and remove every task worktree, temporary build/cache and background process.
   Preserve unrelated primary checkout edits and locked worktrees. Record any
   external publication dependency and exact retry condition.
