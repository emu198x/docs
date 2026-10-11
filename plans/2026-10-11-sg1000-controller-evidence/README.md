# SG-1000 controller capture

A full MAME 0.289 run and the corrected Emu198x core agree on all 4,096
home-console controller combinations at $DC/$DD. The baseline core differs
in 4,032 cases; the 64 states with player two released are controls.

`baseline.csv`, `mame.csv` and `fixed.csv` retain every observed guest byte.
MAME additionally records both host input ports. Each row includes guest RAM
execution markers from before and after sampling. `verify.py` checks all rows,
input values, markers, both controller bytes and the regenerated guest hash:

```sh
python3 -B plans/2026-10-11-sg1000-controller-evidence/verify.py
```

`build_guest.py` generates the original 32 KiB cartridge. It continuously
reads the canonical controller ports into $C000/$C001 and increments $C002.
The trace host does not write CPU registers, RAM or machine I/O.

The retained `capture.lua` and `probe.rs` use the original scratch paths
under `/private/tmp/198x-sg1000-input-evidence/`. Place the generated
`input.sg` there for exact reproduction. MAME was run with:

```sh
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy mame sg1000 \
  -cart /private/tmp/198x-sg1000-input-evidence/input.sg \
  -video none -sound none -nothrottle -skip_gameinfo -autoboot_delay 0 \
  -autoboot_script /private/tmp/198x-sg1000-input-evidence/capture.lua \
  -homepath /private/tmp/198x-sg1000-input-evidence/mame-home -seconds_to_run 240
```

Compile `probe.rs` with the source workspace's pinned Rust toolchain and
its `machine_sega_sg_1000` / `common_z80_machine` rlibs. Capture stdout before
and after the correction. `provenance.json` identifies the source revisions,
original guest and installed MAME binary. Separately inspected vendor source
revisions are not asserted to be that binary's build inputs.

The source regression `tests/controller_wiring.rs` is broader than the
canonical capture: all 4,096 states in both regions, all 64 aliases, changing
inputs and snapshots. The baseline `red.log` has two failing regressions;
`tests.log` has 25 affected-package passes and one explicit fixture ignore.
`clippy.log` records the affected all-target check.

MAME's driver does not map every $C0-$FF alias. The hardware investigation
and Ares source support that extent; the MAME capture proves only its
canonical ports. Physical waveform timing, SC-3000 peripherals and cartridge
mappers are outside this correction.
