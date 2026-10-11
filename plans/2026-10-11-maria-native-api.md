# Retire MARIA's aggregate scanline path

This is the next bounded engineering-frontier slice of the approved
`2026-10-10-maria-timed-dma-design.md`. The machine already uses native
ticks. The chip still exposes a second renderer that fetches a whole line,
draws its graphics immediately, releases WSYNC at the line boundary and
raises the current zone's DLI after that zone. Its read count is advertised
as stolen CPU cycles. Those behaviours contradict the qualified pipeline.

1. In `crates/atari-maria/src/lib.rs`, demonstrate the old helper's output
   disagrees with native playback for the same descriptor and graphics.
   Keep the public-pin native fixture as a regression for the measured
   descriptor/fetch/playback sequence, with nonzero read/event assertions.
2. Remove `render_line`, `dma_cycles` and `clear_wsync`, their private bulk
   rendering helpers and the obsolete read counter. This is the API removal
   already covered by the approved design. Callers must route pins around
   `tick_dma`; a callback cannot express concurrent CPU writes/ownership.
   Keep explicit debugger register writes and image clearing.
3. Migrate existing chip tests onto native ticks. Preserve border, palette,
   transparency, frame completion, DMA disable/restart and descriptor-event
   checks. In `video.rs`, exercise playback through its native stage rather
   than bulk framebuffer flushing. In `fetch.rs`, `dma.rs` and `state.rs`,
   remove only the unused aggregate count and its snapshot fields. The
   approved, unreleased runtime v6/direct version-1 layout continues to evolve.
4. Run affected package tests, Asteroids, Clippy and formatting. Check the
   workspace for remaining callers, and deliberately suppress native pixel
   playback to verify the migrated outcome checks fail. Record results and
   commit this slice; keep source PR #1704 draft.

## NMI research boundary

The original GCC1702B acceptance specification (PDF page 14) specifies a
one-CPU-cycle pulse. MiSTer's first DMA revision
`aef45f04b8dd8e97d9c041f2bfdf1d9c01e6acfa` includes a disabled selector-based
path with a comment explicitly extending NMI so the 6502 sees it; its active
shift-register path produces the longer pulse previously measured. The
current revision retains that shift-register path. This establishes a
reference implementation choice, not a measurement of production silicon.

The 1984 gate-level PDF contains the selector network on page 17, but its
TIA/MARIA combined-chip design and combined HALT/NMI pad require revision
adjudication before treating them as the production 7800 pin timing. The
physical NMI assertion/width gate remains open. No interrupt delay is chosen
by this API removal, and neither #196 nor #197 is closed.

## Result

The old/new comparison failed on the first active pixel of rasters 16–18:
the aggregate path produced `[foreground, black, black]`; native playback
produced `[black, black, foreground]`. Both used DLL `$2000` with bytes
`00 30 00`, DL `$3000` with `00 1f 05 00`, graphics `$0500 = c0`, CTRL `$40`
and palette colour 3 `$66`. Native memory came from actual read strobes,
with Sally sampling HALT and retaining an undriven address. This reproduces
the bulk helper's missing descriptor-prefetch/line-RAM delay.

Source commit `edc96b5a` removes `Maria::render_line`, `Maria::dma_cycles`, `Maria::clear_wsync`, the
private bulk descriptor/list/render helpers, and the unused aggregate read
counter from both snapshot encodings. No workspace caller remains. Native
register, clock, DMA and playback timing are unchanged. The public migration
instructions direct callers to `tick_dma`, `dma_read_pending` and ownership
pins; neither memory reads nor image helpers advance an alternative clock.

The migrated checks cover native border output, transparency, WSYNC release,
DMA disable/restart, descriptor decoding in both regions, the first graphics
row and frame completion. Mode/palette tests now transfer and play their
line RAM through native ticks. Existing reference vectors and snapshot
continuation checks still pass. The descriptor fixture stops at its third
read: running to the line boundary incorrectly included the next DMA request.

All **126 affected package tests** pass, plus the separate **200-frame
Asteroids** smoke, Clippy and formatting. Forcing playback to black makes the
new first-graphics test fail. Both the old/new failure and the playback
negative are retained in the [evidence directory](2026-10-11-maria-native-api/).
Full local logs are under `/private/tmp/maria-native-api/`.

Verification from `Emu198x/emu198x/`:

```sh
cargo test -p atari-maria -p machine-atari-7800 -p runtime-atari-7800 -p emu198x-atari-7800
EMU198X_ATARI_7800_CART="$HOME/.emu198x/media/atari-7800/Asteroids (1987)(Atari)(NTSC).a78" cargo test -p machine-atari-7800 --test cart_boot -- --ignored --nocapture
cargo clippy -p atari-maria -p machine-atari-7800 -p runtime-atari-7800 -p emu198x-atari-7800 --all-targets -- -D warnings
cargo fmt --all --check
```

PR #1704 remains draft. Physical NMI timing, actual interrupt/raster acceptance
and POKEY chip-clock/sample separation remain required before merging.
