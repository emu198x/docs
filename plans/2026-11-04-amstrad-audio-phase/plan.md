# Qualify the six Amstrad tape-audio differences

Engineering-frontier continuation of #2265 after merged #2285. The first batch
covers RoboCop, Out Run and Where Time Stood Still on +2A and +2B. Their existing
frame oracles still match; their audio changed after physical WAIT was corrected.
Keep every expectation unchanged until the affected semantic/audio behaviour is
explained. The binding `routing-versions-do-not-cover-cpu-timing.md` requires
investigation and semantic anchors, not a mechanical recapture.

1. Extract only the verified retained producer executables/manifests and these
   six waveforms from the private recovery archive into
   `/private/tmp/198x-amstrad-oracle-evidence`. Verify each extracted SHA-256.
   Preserve archive/input bytes. Record actual code/manifest/binary identities.
2. Run the retained pre-fix producer on the three +2A cases, with the original
   manifest, bounded child runtimes/logs and complete output. Accept a baseline
   only if both hashes exactly match the existing expected pair. An old binary
   is not automatically a valid oracle. If it differs, diagnose before using it.
3. Compare complete old/new WAV formats and samples, including timing/lag,
   changed sample locations and waveform/content. Verify +2B equivalence rather
   than assuming it. Correlation alone cannot authorize an oracle change.
4. If needed, inspect existing AY write watches in
   `crates/common-sinclair-zx-spectrum-amstrad-class/src/core.rs` and the native
   catalogue/session path. Collect actual bus/register timing with bounded
   host-side observation; do not inject guest code or change hardware timing.
5. If qualified, change only the six `[entry.audio].hash` fields in
   `crates/emu198x-catalogue/manifest/spectrum.toml`, documenting the mechanism
   and semantic anchors. Preserve every frame hash, frozen fixture and old
   evidence. Verify against current main (which now also contains the separate
   keyboard-ghosting fix), including deliberate stale/wrong-oracle controls.
   Otherwise leave hashes unchanged and publish the precise remaining blocker.
6. Retain results under the Emu198x docs repository's plans/evidence convention,
   update #2265, run applicable checks, commit/push and use normal PR CI. Do not
   expand this batch to CPC (#2284), which stays on Z80 0.8, or Asm198x.
7. Resources: isolated source worktree `/private/tmp/198x-amstrad-oracle-audit`;
   evidence `/private/tmp/198x-amstrad-oracle-evidence`; create a separate task
   build cache only if required. Archive unique evidence privately and verify
   remote refs before removing completed worktrees, caches and processes.

The three retained baselines exactly reproduce all old frame/audio hashes, but
Out Run and Where Time Stood Still do not show a trivial small-lag PCM change.
Collect bounded AY state/command observations on current e125cf697 and the
immediate pre-WAIT f176914a sources. A temporary ignored catalogue-local test
reuses the real boot/media/waypoint helpers and existing AY watch, records the
chip state at the audio-window edges and per-field command sequence, and checks
that the resulting ordinary audio hash is unchanged by observation. A temporary
`AY_EDGE` diagnostic inside the existing armed-watch branch records native HC,
PC, register and value only for this bounded audio window. These diagnostics
must be archived then removed; no debug output, API or schema change will ship.
Additional owned workspace: `/private/tmp/198x-amstrad-oracle-before`; shared
rebuildable cache: `/private/tmp/198x-amstrad-oracle-target`.

The observers reproduce both original and corrected normal hashes exactly. All
three corrected windows start 354,540 master ticks (one native field) later.
RoboCop/WTSS have identical per-field AY command streams; Out Run matches all
99 overlapping fields at a one-field shift. The extra 35,454 AY input clocks
exactly predict prescaler and sample-error differences. Test the causal
hypothesis once: delay ordinary tape start on the old build by one native
field, recording firmware-menu, tape-start and tape-stop times. Retain a zero
delay control. Do not sweep delays, edit chip state or tune phase to fit a hash.
