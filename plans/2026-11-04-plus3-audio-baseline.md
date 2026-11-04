# Trace the five +3 audio-only failures

Engineering-frontier continuation of #2265, approved by the user after the
Rainbow repair. Start from source 1abe54f1b and docs 6d20a84. Keep all nine
remaining expected pairs unchanged until their differences are explained.

1. Restore the existing private AY observer from the verified prior archive,
   checking archive and extracted-member SHA-256. Reuse its normal-session
   navigation, write watch and pre/post AY serialization; adapt only the +3
   disk setup. No dependency, public API or save-format change.
2. Use isolated current/original worktrees at 1abe54f1b and cf6ee98c2. Before
   changing either, record their clean state and manifest identities. The
   latter already reproduces both original hashes for all five audio-only
   cases. Retain and verify the exact production binaries from the Rainbow
   archive as an independent observer-output control.
3. Observe each unchanged capture window with existing AY write watches,
   physical clock timestamps, write PC/register/value, start/end AY state and
   native-field counts. Require every observed complete WAV hash to equal
   that producer's independent normal capture. Bound builds to 600 seconds,
   case runs to 300 seconds, logs to 16 MiB and abort owned builds if free disk
   drops below 512 MiB. Never reuse an executable after a failed build.
4. Compare all five cases, starting with Chase H.Q. Separate command-sequence
   changes, fixed time shifts, oscillator/prescaler state and output-mixer
   changes. Sample guest RAM/state if needed to establish a semantic music
   anchor. Do not fit a delay to a desired hash or assume old code is correct.
5. Consult original software plus held AY/+3 primary references and vendored
   Fuse/MAME/SpecIde before any chip/timing change. If a fault is reproduced,
   explain its cause and use a failing control before making a narrow fix.
   Ask before any new dependency, API/schema change or architectural pattern.
6. Qualify only supported changes; preserve failed experiments. Publish the
   concrete findings even if they identify a further blocker. Run appropriate
   checks and normal exact-head CI for shipping changes, commit/push, update
   #2265, then archive raw observations and remove owned temporary resources.

Owned worktrees: /private/tmp/198x-plus3-audio-current,
/private/tmp/198x-plus3-audio-original, /private/tmp/198x-plus3-audio-docs.
Evidence: /private/tmp/198x-plus3-audio-evidence. Separate release-only caches:
/private/tmp/198x-plus3-audio-current-target and
/private/tmp/198x-plus3-audio-original-target. Other sessions' files and
worktrees remain outside this task.

## Qualification result

All five retain their complete music-driver command prefixes. The current AY
and speaker implementations reproduce the historical ones bit-for-bit for
identical state and timed input. Offline replay reconstructs every PCM sample
of both original and current two-second recordings, including the beeper in
Chase H.Q. and Where Time Stood Still. Three games also reproduce both complete
AY command windows in MAME; its two other original disks remain loader-bound.

Update only the five phase-specific audio hashes, following the existing
qualification procedure. Keep all frame hashes, capture settings, routing
versions, other four +3 failures and engine code unchanged. Require normal
production PASS plus snapshot replay for each of the five, and retain a stale
expectation rejection. The combined ledger must label five fresh observations
and 98 reused observations; no new full sweep is claimed.
