# Dizzy loads on the 128K through 48 BASIC

Issue [#1924](https://github.com/emu198x/emu198x/issues/1924) reproduces when
the original 1987 tape is loaded through the 128K menu's **Tape Loader**.
It also reproduces in Fuse with real tape playback. Selecting **48 BASIC**
on the same 128K instead reaches the title. All 6,912 screen bytes agree
between Emu198x's 48K run, its 128K/48 BASIC run, and Fuse's 128K/48 BASIC run.
No emulator behaviour change is justified by this reproduction.

## Inputs and source

`identity.json` pins source `b4c26f0baf2e3620f7203a20326b0f98fdfcb9a8`,
the unmodified TOSEC TZX and the English 128K ROM pair. ROMs, the tape and
save states are local inputs/outputs and are not included here.

Sinclair's *ZX Spectrum 128 Introduction*, “Tape Loader” and “48 BASIC”,
explicitly directs 48K/16K tape programs through 48 BASIC. The local primary
source is
[`reference/by-system/sinclair-zx-spectrum/zx-spectrum-128-introduction-sinclair.txt`](../../../../reference/by-system/sinclair-zx-spectrum/zx-spectrum-128-introduction-sinclair.txt)
in the umbrella checkout, lines 298–303 and 323–344; provenance is in its
adjacent `.source.json`.

## Observations

| Machine and startup | Observation |
| --- | --- |
| Emu198x 48K, `LOAD ""` | Title at 16,000 frames; still present at 40,000 |
| Emu198x 128K, Tape Loader | Loading picture at 16,000, 20,000 and 40,000 frames; tape progress 1.0; CPU remains in the ROM tape-reading routines |
| Fuse 128K, Tape Loader | Loading picture at 17,000 frames; PC `$05ED`, SP `$FF4C` |
| Emu198x 128K, 48 BASIC then `LOAD ""` | Title after 16,000 playback frames; pressing K then running 100 frames reaches the first room |
| Fuse 128K, 48 BASIC then `LOAD ""` | Title at 17,000 total frames; PC `$FDFD` |

The three title screens share SHA-256
`e452aefb327773df0365da1184e5b4a05aefe04722145dfd320f54e91db28f1b`.
The retained PNGs show the title prompt and the first playable room.
This qualifies loading and starting this exact image, not full-game completion
or real-hardware operation.

## Why the menu path fails

The tape's 60-byte bootstrap loads at `$5B00`. In 128 BASIC that RAM already
holds the ROM's bank-switching routines. `trace.report.json` first observes
the resident routine there, beginning `PUSH AF; PUSH BC; LD BC,$7FFD`.
The ROM tape reader then writes the game's bootstrap over it. Execution
subsequently reaches the game's clearing loop with the wrong entry state:
the captured writes at PC `$5B13` erase `$5B00` onward, including its own
initialisation instructions.

The first 60 bytes at `$5B00` in Fuse's failed run match Emu198x's damaged
loader exactly: the first 18 are zero and byte 18 is `$55`, replacing the
bootstrap's `LD (HL),A` opcode `$77`. In Fuse's successful 48 BASIC run the
original bootstrap remains intact. The retained hex files and CPU write watch
establish this collision independently of the visual symptom. Timing has not
been adjusted to make the incompatible startup work.

## Replay Emu198x

Build the pinned source with:

```sh
cargo build --release -p emu198x-spectrum --no-default-features
```

Use a disposable output directory and an absolute path to each retained script.
`EMU` below is the built binary, `TAPE` is the identified unzipped TZX, and
`EVIDENCE` is this directory. The scripts write screenshots and states in the
current working directory. Keep the conventional ROM bundles installed under
`~/.emu198x/roms/`.

```sh
"$EMU" --machine spectrum_issue3_48k --tape "$TAPE" --autoload-tape \
  --script "$EVIDENCE/48k.json" > 48k.report.json
"$EMU" --machine spectrum_128k --tape "$TAPE" --autoload-tape \
  --script "$EVIDENCE/128k.json" > 128k.report.json
"$EMU" --machine spectrum_128k --tape "$TAPE" \
  --script "$EVIDENCE/48basic-manual.json" > 48basic-manual.report.json
"$EMU" --machine spectrum_128k --tape "$TAPE" --autoload-tape \
  --script "$EVIDENCE/trace.json" > trace.report.json
"$EMU" --machine spectrum_128k --script "$EVIDENCE/start-game.json" \
  > start-game.report.json
```

Use `read-screen.json` and `read-screen128.json` to read the two retained
16,000-frame states in 256-byte chunks. Concatenate `bytes` from their
`memory_read` observations to obtain the 6,912-byte SCR files. A full
screen cannot be obtained in one call: `memory_read` caps each result at 256.

The 48 BASIC control uses real menu keys, waits 200 frames for the ROM's
48 BASIC reset, then types the command and starts tape transport. It does
**not** call `autoload_tape`: that helper deliberately hard-resets an already
running machine and would select Tape Loader again.

## Replay Fuse

The reference is vendored Fuse 1.7.0 with vendored libspectrum 1.6.0. Apply
`fuse-null-observer.patch` to a disposable source copy and build its null UI.
The patch adds host-side keys, fixed observation checkpoints, SCR/snapshot
output and a frame limit. It changes no CPU, tape, contention or machine code.
The original vendored source is unchanged.

The local libspectrum build used its internal GLib replacement and disabled
libgcrypt and WAV. Its bundled libtool could not link correctly on this Mac;
the compiled objects were archived with `/usr/bin/ar`, excluding libtool's
intermediate aggregate object, and Fuse linked that archive with `-lbz2 -lz`.
This is a reference-build workaround, not an emulator change.

Run the instrumented Fuse with this environment and arguments; add
`DIZZY_48BASIC=1` for the successful control. Choose distinct output paths
for each run.

```sh
DIZZY_FRAMES=17000 DIZZY_SCR="$SCR" DIZZY_SNAP="$SNAP" \
  "$FUSE" --machine 128 --no-auto-load --no-sound --speed 1000000 \
  --no-traps --no-fastload --no-detect-loader --no-accelerate-loader \
  --rom-128-0 "$ROM0" --rom-128-1 "$ROM1" --tape "$TAPE"
```

All four loader shortcuts must be disabled. Otherwise their accelerated
execution changes the relationship between host key checkpoints and tape
progress. `--speed 0` is not unlimited in this Fuse; it means 1% speed.

## Evidence checks

`python3 verify_evidence.py` checks complete title equality, the failed-load
observations, and agreement on the damaged bootstrap. It validates these
retained artefacts; it does not execute an emulator. A negative control that
flipped one byte of a copied title SCR failed with
`FAIL: 48K, 128K/48 BASIC and Fuse title screens disagree`.

`SHA256SUMS` covers every retained file other than itself. Temporary reference
builds, extracted media and diagnostic states can be removed once these
artefacts and their source commits are retained.
