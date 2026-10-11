# Reproduce the Mealybug LCD-boundary survey

These are measurements of unchanged guest ROMs and emulator cores. No ROMs,
third-party source trees or framebuffer images are distributed here.

## Pinned inputs

- Emu198x: `ba718712062cf16dbe881ef7f99d16220b558dbe`.
- Mealybug: `mattcurrie/mealybug-tearoom-tests`
  `70e88fb90b59d19dfbb9c3ac36c64105202bb1f4`; `corpus.json` identifies the local
  24 ROMs, 24 DMG-blob PNGs and two DMG-CPU B PNGs.
- SameBoy: `208ba4afabffab9edde416f2dbb8ae459e34adb8`, DMG-B, own DMG boot ROM.
- GateBoy (`aappleby/metroboy`): `36797ad4cf77b3e04ffe45716218a79b5280076a`.
- metrolib: `57ba4df22ae8241660385826e6b9a8847a482b23`.

## Emu198x

Set `EMU198X_GB_MEALYBUG_ROOT` to the external `ppu/` fixture directory.
Run `cargo test -p machine-nintendo-game-boy mealybug_dmg_ppu_gate -- --ignored --nocapture`
and the same command with filter `diagnostic_mealybug_dmg`. Both logs are
included. The gate checks all 24 marker completions and expected counts;
the diagnostic reports the DMG-blob counts, so it prints 22/24 rather than
the CPU-B-selected gate's 23/24.

`emu-trace.patch` is temporary instrumentation against that source revision.
It prints PPU state on line 19 and visible pixel emissions, then executes
one asserting guest test. Its fixture and dump paths reflect the local
workspace; adjust those two paths when reproducing elsewhere. Run
`cargo test -p machine-nintendo-game-boy temporary_mealybug_bg_trace -- --nocapture`.
The final line trace and positive one-test result are retained. The patch is
not a production change. `bg-frame-identity.json` records equality with
SameBoy's entire frame, including its four incorrect pixels.

## SameBoy

Build the pinned external tree with `make lib bootroms CONF=release -j4`.
Place it at `SameBoy/` next to `reference_mealybug.c`, then compile:

```sh
clang -O2 reference_mealybug.c SameBoy/build/lib/libsameboy.a -lm -lpthread -o reference_mealybug
./reference_mealybug SameBoy/build/bin/BootROMs/dmg_boot.bin "$ROM" "$OUTPUT"
```

The host requires the guest's LD B,B completion after the boot ROM exits,
checks that every emitted RGB colour is a valid DMG grey, and writes 23,040
shade bytes. `sameboy-survey.json` records every ROM's marker address and
exact pixel counts. A missing ROM exits 3 rather than producing a pass.

## GateBoy

Use fresh external source archives at `GateBoy/` and `metrolib/` beside
`build_gateboy.py`. The latter contains `metrolib/core/` etc. inside it.
No repository source is edited; the only host stub discards audio samples.

```sh
python3 build_gateboy.py
EMU198X_GB_MEALYBUG_ROOT="$FIXTURE_PPU" python3 survey_gateboy.py
```

The build script needs clang++, and the survey needs the already-installed
Pillow package to read expected PNGs. It creates per-ROM shade outputs and
LCD pin traces locally. The native framebuffer is `<rom>-gateboy.shades`;
the separate 159-pixel shift plus CPL capture is the `.lcd` sibling.
Every complete frame must contain 23,040 valid shades. The run waits one
frame after LD B,B, as the original GateBoy experiment did.

`gateboy-survey.json` contains 24 positive marker observations. Each row
compares both capture paths byte-for-byte and scores each against the same
expected image. `gateboy-line19-pins.csv` is the final BG_EN line's boundary
excerpt, with packed signal metadata masked to the actual pin bit.

The separate sampler follows the method in Thomas Spurden's
[hardware capture report](https://thomas.spurden.name/blog/capturing-gb-lcd/).
This is a check on reference capture, not a claim to have measured our own
physical Game Boy or to have validated GateBoy's register delivery.

`negative-controls.json` verifies that both reference hosts reject a missing
ROM with exit 3. The completion marker, frame size, valid shade checks and
24-row coverage are all required. Neither a zero-test invocation nor a
missing capture is counted as success.
