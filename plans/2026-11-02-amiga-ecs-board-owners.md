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


## Approved RTC correction

On 2026-11-02 Steve approved v67 output with an explicit v66 reader. Migrate
only the A500+ saved RTC-presence flag, retaining clock history and all other
state. Other models' v66 payloads remain unchanged. Version-67 A500+ state must
retain the real onboard clock; a legacy flag is not a switchable board option.
The source regression reproduces a write of 5 reading as 15 for the stock
A500+ (PAL, slow_kb=0), matching the slow-RAM-gated decoder root cause. Primary
manual PDF page 3 / printed 1-1 states onboard battery-backed RTC and 1 MiB
stock RAM. Save original final envelopes too so post-migration field/byte
retention can be checked independently of the new writer.


Original capture/replay: 16 cases pass before production changes, with actual
half-CCK phase and time/tick consistency asserted. A disposable corrupted-output
control fails on elapsed clocks (141648 vs 141776), with all immutable originals
untouched. The capture commit is d35b9f86c. Initial RTC and migration checks pass:
all 16 ECS cases permit only the version and onboard RTC bit, all A1200 payloads
retain exact bytes after header translation, all 18 already-valid legacy
profiles restore, and malformed v67 missing-RTC state rejects atomically.
