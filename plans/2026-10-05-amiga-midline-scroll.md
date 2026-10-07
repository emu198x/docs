# Mid-line independent playfield scroll accuracy

Status: complete.

Lane: engineering-frontier. Approved: compare independent mid-line scroll changes and fix reproduced inaccuracies.

1. Add `test-data/commodore/amiga/midline-scroll/tools/build.py`, reusing the neutral sprite probe bootloader. Two independently patterned bitplanes, distinct PF1/PF2 colours, pointer reset each line, static controls and Copper BPLCON1 changes across 32 phases. Cover lores/hires/superhires and 16/64-bit fetches.
2. Capture three FS-UAE reference fields and the native full raster for each guest under `/private/tmp/emu198x-midline-scroll`. Compare using the existing strict whole-raster comparator. Preserve all failing evidence; confirm guest identities, field counters and distinct data.
3. If differences occur, trace the register-to-output path in `common-commodore-amiga/src/denise.rs` and the reference before changing code. Add a failing regression in `runtime-commodore-amiga/tests/scroll_dma.rs`; correct only the proven cause. Agree any architectural or snapshot change first.
4. Repeat the full raster comparison, relevant Rust regressions, build, format and strict Clippy after a production fix. Record evidence and limits in the primary video observations and scroll decision. A clean comparison establishes this bounded reference agreement, not hardware calibration.

## Proposed correction (agreement pending)

The current Lisa model always copies both groups at zero-delay phase, then selects BPLCON1-delayed pixel history immediately. Registered FS-UAE instead compares the physical counter against each group's BPLCON1 selector and copies its pending holding register at that event, restarting that group's serial phase. Fixed offsets can agree while mid-line changes observe different pending data and phase.

Recommended scope: extend the existing odd/even pending-copy and serial stages in `crates/commodore-denise-ocs/src/chip.rs`, keep the physical copy comparator and existing timed resolution/fetch selectors, and preserve independent in-flight group timing in diagnostics and snapshots. Board-level regressions belong in `runtime-commodore-amiga/tests/scroll_dma.rs`; snapshot restoration in `display_register_pipeline.rs`; the runtime envelope would become version 45 with explicit version 44 rejection. The user has been asked to agree this pipeline and breaking snapshot design. No production changes have been made for this task.

## Discovery evidence

Steps 1 and 2 are complete. Twelve final guests rebuild byte-identically; both distinct colours are visible in every native and reference image. All six controls pass; all six changed-offset guests fail identically over three adjacent fields. Strict comparator result: `12 cases, 36 full-raster comparisons, 18 failed fields` (exit 1). The source-defined whole raster covers 31,243,968 RGB samples across 36 fields. Ruff checks and formatting pass. No production behavior has been changed and no production regression suite is claimed for this probe-only stage.

| lores-f0-control | 0 |
| lores-f0-changes | 2016 |
| lores-f3-control | 0 |
| lores-f3-changes | 4976 |
| hires-f0-control | 0 |
| hires-f0-changes | 784 |
| hires-f3-control | 0 |
| hires-f3-changes | 3156 |
| shres-f0-control | 0 |
| shres-f0-changes | 128 |
| shres-f3-control | 0 |
| shres-f3-changes | 2306 |

Artifact report: `/private/tmp/emu198x-midline-scroll/verified-colours-verification.json`. Implementation and its verification remain pending the requested pipeline/save-state agreement.

## Approved implementation

The user approved the independent timed playfield stages and snapshot v45. Engineering-frontier lane. Extend the existing pending-copy groups to compare integer/fractional offsets at every physical 35 ns period; restart only that group's serial clock. Retain a fixed output transport delay independently of programmable scroll. Preserve both group phases and held source data; expose both phases in diagnostics. Add a red-before-fix group-copy test, board output regression and restore checks, then run the 36 new raster comparisons and preceding display sweeps, strict video and boot gates, affected regression suite, build/format/Clippy.

## Completed implementation and verification

The user approved the pipeline extension and snapshot v45. Lisa now clocks
odd/even source groups independently, copies on each masked native-period scroll
phase, preserves complete BPL1DAT-frozen pending words, and samples BPLCON1 through
the existing normal-stage copies. Runtime saves reject v44 explicitly; phases
and pending tail lengths are validated. Diagnostics expose both clocks, frozen
tails and visible/pending selector values.

The complete holding-group freeze supersedes the temporary live-head experiment.
That experiment is rolled back: registered `bpldat_docopy` freezes all heads and
tails together, not live heads at the later comparator. The initial restore-clock
fixture used a narrow shres mask that loaded the odd group before the intended
rate change; it now uses a wide fetch to put the rate change between the two actual
copy phases, with a positive assertion that the clocks differ at snapshot time.

The capture helper initially enumerated an unadmitted `guests/src` folder and
failed with:

```text
subprocess.CalledProcessError: Command '['/Users/stevehill/Projects/198x/Emu198x/emu198x/target/release/emu198x-amiga', '--model', 'a1200', '--kickstart', '/Users/stevehill/Projects/198x/Emu198x/emu198x/../roms/kick31_40_068_a1200.rom', '--disk', '/private/tmp/emu198x-wide-sprite-validation/guests/src/probe.adf', '--script', '/private/tmp/emu198x-wide-sprite-validation/guests/src/v45.json']' returned non-zero exit status 1.
```

 Its original script and log are retained. Enumeration
now follows the nonempty diagnostic manifests, checks distinct paths and ADF
presence, and the five missing admitted captures were completed. All 74 admitted
previous guests then passed the strict comparator; no empty/filtered result was
used as evidence.

Final verification:

- 54 new guests rebuild byte-identically; the original twelve mid-line ADFs and
  their reference fields remain unchanged. All 162 new plus 222 preceding field
  comparisons match: 384 fields, 333,268,992 RGB samples, zero differences.
- Extended/fractional static scroll at DDF $30/$38 independently proves the
  earlier translation assumption false at some high wide-copy phases. The
  translation fixtures now use aligned DDF $38; both origins retain full raster
  reference gates. No reference image or boot golden was changed.
- 808 release tests pass across 67 targets, including all eight strict-asset boot
  checks. Both explicit Test Kit video gates match six patterns exactly. The
  broad suite retains 31 explicitly ignored fixture/campaign tests.
- The copy-timing regression failed before the correction. New tests cover pending
  wide-head/tail consistency, normal-stage scroll propagation, independent DMA
  playfield writes, restoration with differently phased streams, and rejection of
  invalid phases/tails and v44 saves. The final scroll tests were rerun after their
  test-helper argument cleanup; no production behavior changed afterward.
- Build, formatting, Ruff and strict Clippy pass. Logged reference fields match
  their original bytes, and unlogged reference source and executable are restored.

Artifact root: `/private/tmp/emu198x-midline-scroll/`; final evidence and hashes:
`final-verification.json`. Scope limits remain in the primary observations and
scroll decision. FMODE=2, other plane counts, arbitrary independently paired
fractions, priority/HAM interactions, combined resolution/fetch/scroll transitions
and physical hardware calibration are not claimed.
