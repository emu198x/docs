# Five +3 audio expectations explained

We qualify the current audio windows for Chase H.Q., Starglider 2, Lotus Esprit
Turbo Challenge, RoboCop and Where Time Stood Still. Their complete frame
hashes, input media, firmware, capture settings and routing versions stay
unchanged. The other four failing +3 entries retain both original expectations.

The historical producer reproduces every original frame/audio pair. The
current producer executes the same ordered music commands at different times.
Replaying the observed state and timed inputs through both versions of the
production sound components reproduces **every PCM sample in all ten original
and current recordings**: 88,200 samples per two-second window. This explains
the changed expectations without changing emulator code or fitting a delay.

Source [PR #2290](https://github.com/emu198x/emu198x/pull/2290),
commit `7537577e8b7a86f5840089aedaa783038fc4304e`, changes only the manifest and changelog.
Source baseline: `1abe54f1b49f23a43853ce161fde022dcc228cea`.
Historical producer: `cf6ee98c2857c37b0683945107c695c316a49fcc`, built unchanged
with its pinned Rust 1.99.0. Both original binaries and complete input identities
were already verified in [the Rainbow evidence](../2026-11-04-rainbow-guest-state-evidence/README.md).
The written work plan is [here](../2026-11-04-plus3-audio-baseline.md).

## Changed windows, preserved programs

Each observer uses ordinary firmware/menu/ENTER/disk navigation and asserts
its producer's independently captured complete WAV hash. The watch cannot
silently truncate: every native field checks the capacity. We record all
startup writes, the 100-field audio window and 400 continuation fields.

| Entry | First main music write moves by native fields | Ordered AY commands compared |
|---|---:|---:|
| Chase H.Q. | 163 | 40,676 |
| Starglider 2 | 73 | 51,273 |
| Lotus | 88 | 61,639 |
| RoboCop | 116 | 87,738 |
| Where Time Stood Still | 128 | 66,651 |

The complete current stream is a prefix of the historical stream across the
bounded observation, with one disclosed startup difference: Starglider makes
four additional writes repeating the same muted configuration before its main
music starts. They write zero to each volume and retain the mixer value. The
remaining sequence matches exactly, including issuing PC, register and value.
The raw extra writes remain in the retained evidence.

The fixed audio window starts one native field later in absolute master time:
354,540 master ticks. Its duration is unchanged, 35,454,000 ticks. That extra
field predicts both the observed AY prescaler and Bresenham sample-error state
exactly. Later music writes have the observed different time offsets; we do
not assume a constant shift for every program or choose one by correlation.
A short repeated musical phrase initially suggested a smaller Chase shift;
tracking the complete command history removes that ambiguity.

[analysis.json](analysis.json) records all five complete comparisons, clock
predictions, edge-delta distributions and independent-reference matches.

## Reconstruct the actual audio

The AY library changed from 0.6.0 to 0.6.1 between producers. We feed each
observed starting chip state and exact timed write schedule through **both**
versions. Every resulting `f32` sample is byte-identical for identical input.
This directly checks the relevant synthesis behaviour instead of relying on
the changelog's claim about unrelated YM2149/port-B additions.

For Starglider, Lotus and RoboCop, applying the unchanged AY gain and production
PCM conversion reconstructs all 88,200 samples of each actual recording.
Chase and Where Time Stood Still also contain beeper output; AY alone fails to
reconstruct their complete WAVs. We retain that failed hypothesis.

For those two, we observe every physical speaker transition from reset and
replay the complete history through both versions of the production speaker
mixer. The speaker results are also byte-identical for identical input. Mixing
those samples with the AY samples reconstructs both complete original and
current recordings exactly, including clipping and negative PCM values:
[mixed-pcm-reconstruction.json](mixed-pcm-reconstruction.json).

Chase preserves all 63,662 current speaker transitions as an exact prefix of
the historical stream; Where Time Stood Still preserves all 240. PC and output
level agree, not just the number of transitions. See
[beeper-prefix-comparison.json](beeper-prefix-comparison.json).
The first diagnostic PCM converter rounded negative half-ties incorrectly;
using the production `f32::round` rule, ties away from zero, removes the last
single-LSB discrepancies without a tolerance. The failed diagnostic and a
positive/negative half-tie check are retained.

## Independent reference and its limits

Read-only MAME 0.289 I/O taps reproduce both complete original and current
captured AY-command windows for Chase, Starglider and Lotus. These include PC,
register and value for every command, rather than matching a screenshot or
recognizable tune. Chase's speaker transition windows also occur in the
reference stream. Adding the speaker observer preserves every reference AY
event and its final pixels byte-for-byte against the AY-only control.

All five original disks declare 42 tracks and are mounted byte-for-byte.
No geometry accommodation is needed. Full firmware/ZIP/disk hashes are in
[baseline-five-results.json](baseline-five-results.json). MAME uses the same
firmware pair identities as the preceding Rainbow probe; its binary SHA-256 is
`6d40df87963c58cdd3857d203e186af854fea49ae03b2ab555e30ef1029636d9`.

MAME's original RoboCop and Where Time Stood Still disks remain loader-bound,
with only two firmware AY writes. Those are **failed music comparisons**,
not qualified reference boots. Their qualification rests on the reproduced
historical producer, complete program-command comparison and exact production
component/PCM reconstruction. We do not claim matching MAME PCM or complete
physical-drive timing. Different absolute boot/load times are not fitted into
a hardware timing assertion.

## Regression checks

All five normal production runs pass their complete frame/audio checks
and snapshot/replay checks after removing every temporary observer. The old
Chase expectation still fails on that same production binary with exit 1,
while snapshot replay passes. All 45 catalogue tests and release Clippy pass.
See [production-verification.json](production-verification.json). A separate
observer negative control rejects the stale audio hash with exit 101:
[stale-audio-negative.json](stale-audio-negative.json).
The comparison also rejects an empty/truncated history and a changed command.

The source change touches only five audio hashes, their provenance comments
and the catalogue changelog. No Rust implementation, dependency or save format
changes. The combined catalogue ledger labels five fresh production runs and
98 reused observations; it must not be presented as a fresh 103-entry sweep.

## Reproduce and inspect

`observer.rs` is a private ignored unit-test module for the catalogue crate,
using existing APIs in both producer checkouts. The temporary core hooks log
AY write phase/PC/register/value, actual beeper transitions and native frame
completion while the existing watch is armed. Those hooks do not return data,
write guest memory or alter the clock. The exact hook patches and original
probe versions are retained in the private archive.

`replay_saved_ay.rs` and `replay_beeper.rs` expose the focused replay tests for
review. They use the production chip/mixer components, with their existing
serialized state or reset state. They do not execute guest CPU instructions or
replace either machine's normal run loop. No additional crate is required.

The public analysis scripts consume the private bounded observations:

```sh
EMU198X_AUDIO_EVIDENCE_ROOT=/path/to/restored-evidence python3 reconstruct_mixed.py
EMU198X_AUDIO_EVIDENCE_ROOT=/path/to/restored-evidence python3 analyse.py
```

Both commands require actual complete inputs and assert exact output bytes.
The MAME Lua observer requires `PROBE_OUTPUT`, ordinary original +3 firmware
and disk mounting, and a run limit beyond its 210-second endpoint. The earlier
150/170-second Chase attempts ended before the relevant second attract cycle;
they are retained rather than discarded as empty matches.

Private game memory, timed music commands and recordings stay in the verified
local recovery archive. This report publishes code, aggregate evidence and
hashes, not the game inputs or music data.

## Qualified hashes

| Entry | Retained historical audio hash | Qualified current audio hash |
|---|---|---|
| chase-hq-plus3 | `xxh64:1173a13fcb7720a2` | `xxh64:4d025de7d2a76994` |
| starglider-2-plus3 | `xxh64:f42fcebdf253d1b1` | `xxh64:818ec2364d7b17f3` |
| lotus-esprit-plus3 | `xxh64:4677446a6698a8be` | `xxh64:254a1bc10fa235a9` |
| robocop-plus3 | `xxh64:0358393c6b155f61` | `xxh64:df7c2c10ba78103c` |
| where-time-stood-still-plus3 | `xxh64:b89c6f95d98b7924` | `xxh64:530fff8f06271e68` |

[combined-ledger.json](combined-ledger.json) records 99 matching entries and
the four retained failures, using five fresh production runs and 98 identified
prior observations. `reconcile.py` rejects empty, missing, duplicate and
unexpectedly changed-entry inputs before writing a report.

The private archive retains 351 verified files, including all failed
diagnostic attempts and exact binaries. SHA-256:
`2d3f58171842972af7a275a2a3986351960a50ae62651c48442c73534f12554d`.
See [private-archive.json](private-archive.json) for its local location.
