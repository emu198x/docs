# WASM Web Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development`
> or `superpowers:executing-plans` to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish Emu198x to npm as an embeddable browser emulator, generic over
`FamilyRuntime`, shipping the ZX Spectrum first, so Code198x lessons can run the
code a learner just assembled.

**Architecture:** Two new crates. `emu198x-web` is a generic web shell over the
existing `FamilyRuntime` + `MachineCore` traits, supplying browser
implementations of the host contracts `emu198x-shell` already defines
(`FrameSink`, `AudioSink`, keyboard input). `emu198x-spectrum-web` is a thin
binding that instantiates it with `SpectrumRuntimeKind` and produces the npm
artifact. `emu198x-native-video` is generalised so the browser renders through
the same WGSL shader as the native app, CRT filter included.

**Tech Stack:** Rust (workspace pin 1.98.0), `wasm-bindgen` 0.2.127,
`wasm-pack`, `wgpu` 30 (WebGL2/WebGPU backends), Web Audio `AudioWorklet`,
`wasm-bindgen-test` for headless CI.

**Spec:** this document. Project convention keeps design and task breakdown in a
single `plans/` document; the design sections below are the spec the tasks argue
from.

## Global Constraints

- Rust toolchain 1.98.0, per `rust-toolchain.toml`. `RUSTUP_TOOLCHAIN` is set in
  some shells and silently overrides the pin — use `env -u RUSTUP_TOOLCHAIN`.
- Crate naming: `{org}198x-{rest}`. New crates are `emu198x-web` and
  `emu198x-spectrum-web`.
- The accuracy bar does not move for the web. A web build that is not
  bit-identical to native is a defect, not a trade-off (Task 8 enforces this).
- WASM must not displace Spectrum launch-hardening before Crash! Live
  (October 2026). See the sequencing note below.
- No BYO-ROM browser play and no "web-ready" marketing. Those remain deferred by
  `wasm-sequencing.md`; only curriculum-owned content on firmware-permission
  systems is in scope.
- Conventional Commits — `release-plz` derives version bumps and CHANGELOG
  entries from them.

---

## Why this is now cheap: measured evidence

Recorded 2026-09-02. A throwaway spike (105 lines, no changes to any existing
crate) established the following on an M-series Mac:

| Measurement | ms/frame | fps | vs 50 fps realtime |
|---|---|---|---|
| Native (`frame_throughput` criterion bench, real ROM) | 2.701 | 370 | 7.4x |
| WASM, emulation only | 3.466 | 288.5 | 5.8x |
| WASM + canvas blit | 3.641 | 274.6 | 5.5x |

WASM runs at **78% of native**, the top of the 60-80% band
`wasm-sequencing.md` anticipated. The wasm artifact is **125 KB** after
`wasm-opt`. Canvas presentation costs 0.18 ms/frame.

Also established:

- `runtime-sinclair-zx-spectrum` and the whole `emu198x-spectrum` binary
  (`--no-default-features`) compile for `wasm32-unknown-unknown` with **zero
  errors and no source changes**.
- There is **no `std::thread`** in the shell or the Spectrum binary, and **no
  production wall-clock** — all seven `SystemTime::now` calls are in tests.
- `FamilyRuntime::from_firmware` takes ROM **bytes**, and media loads via
  `load_media`/`load_tape_bytes(&[u8])`. `std::fs` is confined to the CLI
  boundary, so "no `std::fs` on the web" never arises.

This is why `wasm-sequencing.md`'s 6-8 week estimate is stale: it priced
building host seams that `emu198x-shell` already has. **Revised estimate: 4-5
weeks** for the scope below.

### Sequencing

The estimate is not a schedule. The roadmap drift trigger stands: this work must
not displace Spectrum launch-hardening before Crash! Live. Task 1 is the largest
unknown and is deliberately first, so the cost is known early and the programme
can be paused after any task without leaving a broken tree.

## Design

### Crate layout

| Crate | Responsibility |
|---|---|
| `crates/emu198x-web` (new) | Generic web shell over `FamilyRuntime`. Browser `FrameSink`/`AudioSink`, DOM keyboard mapping, frame pacing, wgpu canvas presentation, media-from-bytes. Contains no per-system knowledge. |
| `crates/emu198x-spectrum-web` (new) | Binds the shell to `SpectrumRuntimeKind`, maps Spectrum keys, exports the `wasm-bindgen` class, produces the npm package. |
| `crates/emu198x-native-video` (modify) | Surface creation generalised off `winit::window::Window`; async device init added. Shader and filters shared verbatim with the web. |
| `crates/emu198x-shell` (modify) | `cpal`/`gilrs` target-gated off `wasm32`. |

### Data flow

```
JS load_media(bytes) ---> MachineCore::load_media
rAF tick ---> pace() ---> run_until(target, HostIo { .. })
                            |- FrameSink -> rgba_u32_to_bytes -> wgpu texture -> shader.wgsl -> canvas
                            |- AudioSink -> ring buffer -> AudioWorklet
DOM keydown/keyup ---> InputEvent ---> HostIo::input_events
```

### Two traps this plan exists to avoid

**Frame pacing.** `requestAnimationFrame` fires at roughly 60 Hz; the Spectrum
runs at 50.08 Hz (19.968 ms/frame, per the criterion bench). Running one machine
frame per callback runs the machine ~20% fast. Pacing must accumulate elapsed
wall time and run 0..n frames per tick. Once audio is enabled the audio clock
becomes master, because a machine paced off rAF while feeding a fixed-rate
audio device will drift and crackle.

**Palette byte order.** Palette entries are `0xRRGGBBAA`. The canonical
conversion is `emu198x_shell::capture::rgba_u32_to_bytes`. The spike
reimplemented it as `0xAARRGGBB` and rendered black as pure blue and normal
white as lavender — a plausible-looking picture that is wrong. The web renderer
must call the existing helper, never its own.

---

## Task 1: Target-gate the native host dependencies

**Files:**
- Modify: `crates/emu198x-shell/Cargo.toml`
- Modify: `crates/emu198x-shell/src/audio.rs` (module gate)
- Modify: `crates/emu198x-shell/src/lib.rs` (re-export gate)

**Interfaces:**
- Consumes: nothing.
- Produces: `emu198x-shell` builds for `wasm32-unknown-unknown` without `cpal`
  or `gilrs` in the dependency graph. `NativeAudioOutput` becomes
  non-`wasm32` only; the `AudioSink` **trait** stays unconditional, because
  Task 5 implements it.

`cpal` and `gilrs` resolve web backends and do compile for wasm, so this is
about weight and honesty, not breakage.

- [ ] **Step 1: Confirm the current state**

```bash
cd crates/emu198x-shell
env -u RUSTUP_TOOLCHAIN cargo tree --target wasm32-unknown-unknown | grep -E "cpal|gilrs"
```
Expected: both present.

- [ ] **Step 2: Gate the dependencies**

In `crates/emu198x-shell/Cargo.toml`, move `cpal` and `gilrs` out of
`[dependencies]` into:

```toml
[target.'cfg(not(target_arch = "wasm32"))'.dependencies]
cpal = { workspace = true }
gilrs = { workspace = true }
```

- [ ] **Step 3: Gate the module and its re-exports**

In `crates/emu198x-shell/src/lib.rs`, gate the `audio` module and any
`NativeAudioOutput` re-export with `#[cfg(not(target_arch = "wasm32"))]`.
Leave `host::AudioSink` ungated.

- [ ] **Step 4: Verify both targets still build**

```bash
env -u RUSTUP_TOOLCHAIN cargo check -p emu198x-shell
env -u RUSTUP_TOOLCHAIN cargo check -p emu198x-shell --target wasm32-unknown-unknown
env -u RUSTUP_TOOLCHAIN cargo test -p emu198x-shell
```
Expected: all pass; `cargo tree` for wasm32 no longer lists `cpal`/`gilrs`.

- [ ] **Step 5: Commit**

```bash
git commit -am "chore(shell): keep the native audio and gamepad backends off wasm builds"
```

---

## Task 2: Render through the shared shader on the web

**Files:**
- Modify: `crates/emu198x-native-video/src/lib.rs:244-254`
- Modify: `crates/emu198x-native-video/Cargo.toml`
- Test: `crates/emu198x-native-video/tests/surface_target.rs` (create)

**Interfaces:**
- Consumes: Task 1's wasm-clean shell.
- Produces:
  ```rust
  impl VideoRenderer {
      pub async fn new_async(
          target: impl Into<wgpu::SurfaceTarget<'static>>,
          width: u32,
          height: u32,
          profile: VideoProfile,
      ) -> Result<Self, VideoError>;
  }
  ```
  The existing `new(window: Arc<Window>, ..)` stays as a native convenience
  wrapper that calls `pollster::block_on(new_async(window, ..))`, so no native
  caller changes.

This is the largest unknown in the plan. It is first for that reason.

- [ ] **Step 1: Write the failing test**

```rust
// crates/emu198x-native-video/tests/surface_target.rs
//! `new_async` must accept any wgpu surface target, not only a winit window —
//! the browser passes an HtmlCanvasElement.
#[test]
fn new_async_accepts_a_generic_surface_target() {
    fn assert_accepts<T: Into<wgpu::SurfaceTarget<'static>>>() {}
    assert_accepts::<std::sync::Arc<winit::window::Window>>();
}
```

- [ ] **Step 2: Run it and watch it fail**

```bash
env -u RUSTUP_TOOLCHAIN cargo test -p emu198x-native-video --test surface_target
```
Expected: FAIL — `new_async` does not exist.

- [ ] **Step 3: Generalise surface creation and split the async path**

Replace the `Arc<Window>` parameter at `lib.rs:244` with
`target: impl Into<wgpu::SurfaceTarget<'static>>` and pass it straight to
`instance.create_surface(target)`. Move the body to `new_async`, awaiting
`request_adapter` and `request_device` rather than `pollster::block_on`,
because blocking the browser main thread deadlocks. Keep `new` as:

```rust
pub fn new(
    window: Arc<Window>,
    width: u32,
    height: u32,
    profile: VideoProfile,
) -> Result<Self, VideoError> {
    pollster::block_on(Self::new_async(window, width, height, profile))
}
```

- [ ] **Step 4: Add the web backend feature**

In `Cargo.toml`, add for wasm only:

```toml
[target.'cfg(target_arch = "wasm32")'.dependencies]
wgpu = { workspace = true, features = ["webgl"] }
web-sys = { version = "0.3", features = ["HtmlCanvasElement"] }
```

`webgl` gives a fallback where WebGPU is unavailable.

- [ ] **Step 5: Verify native is unchanged and wasm compiles**

```bash
env -u RUSTUP_TOOLCHAIN cargo test -p emu198x-native-video
env -u RUSTUP_TOOLCHAIN cargo check -p emu198x-native-video --target wasm32-unknown-unknown
env -u RUSTUP_TOOLCHAIN cargo test -p emu198x-spectrum   # native UI still builds
```
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git commit -am "feat(video): present through any wgpu surface, so the browser shares the shader"
```

---

## Task 3: The generic web shell and its frame pacing

**Files:**
- Create: `crates/emu198x-web/Cargo.toml`
- Create: `crates/emu198x-web/src/lib.rs`
- Create: `crates/emu198x-web/src/pacing.rs`
- Create: `crates/emu198x-web/src/frame.rs`
- Modify: `Cargo.toml` (workspace members)

**Interfaces:**
- Consumes: `VideoRenderer::new_async` (Task 2).
- Produces:
  ```rust
  pub struct WebMachine<R: FamilyRuntime> { /* .. */ }

  impl<R: FamilyRuntime> WebMachine<R> {
      pub fn new(runtime: R) -> Self;
      /// Runs whole frames to consume `elapsed_ms`. Returns frames run.
      pub fn advance(&mut self, elapsed_ms: f64) -> Result<u32, MachineError>;
      pub fn frame_rgba(&self) -> &[u8];
      pub fn frame_size(&self) -> (u32, u32);
  }

  pub struct Pacer { /* .. */ }
  impl Pacer {
      pub fn new(frame_ms: f64) -> Self;
      /// Accumulates elapsed time; yields whole frames owed, capped.
      pub fn frames_owed(&mut self, elapsed_ms: f64) -> u32;
  }
  ```
  `frame.rs` holds the `FrameSink` impl, which **must** call
  `emu198x_shell::capture::rgba_u32_to_bytes` for `Indexed8`.

- [ ] **Step 1: Write the failing pacing tests**

```rust
// crates/emu198x-web/src/pacing.rs  (#[cfg(test)] mod tests)
const Q: f64 = 19.968; // Spectrum frame, ms

#[test]
fn a_sixty_hertz_tick_does_not_run_sixty_frames_a_second() {
    let mut p = Pacer::new(Q);
    let mut frames = 0;
    for _ in 0..60 { frames += p.frames_owed(1000.0 / 60.0); }
    // One second of rAF ticks must yield ~50 frames, not 60.
    assert!((50..=51).contains(&frames), "ran {frames} frames in a second");
}

#[test]
fn fractional_remainder_carries_between_ticks() {
    let mut p = Pacer::new(Q);
    assert_eq!(p.frames_owed(10.0), 0);
    assert_eq!(p.frames_owed(10.0), 1); // 20ms accumulated
}

#[test]
fn a_long_stall_is_capped_rather_than_replayed() {
    let mut p = Pacer::new(Q);
    // A backgrounded tab returning after 5s must not run 250 frames.
    assert!(p.frames_owed(5000.0) <= Pacer::MAX_FRAMES_PER_TICK);
}
```

- [ ] **Step 2: Run them and watch them fail**

```bash
env -u RUSTUP_TOOLCHAIN cargo test -p emu198x-web pacing
```
Expected: FAIL — `Pacer` does not exist.

- [ ] **Step 3: Implement `Pacer`**

```rust
pub struct Pacer { frame_ms: f64, accumulated: f64 }

impl Pacer {
    pub const MAX_FRAMES_PER_TICK: u32 = 4;

    pub fn new(frame_ms: f64) -> Self { Self { frame_ms, accumulated: 0.0 } }

    pub fn frames_owed(&mut self, elapsed_ms: f64) -> u32 {
        self.accumulated += elapsed_ms;
        let mut owed = 0;
        while self.accumulated >= self.frame_ms && owed < Self::MAX_FRAMES_PER_TICK {
            self.accumulated -= self.frame_ms;
            owed += 1;
        }
        // Drop the backlog a stalled tab accrued rather than fast-forwarding.
        if self.accumulated > self.frame_ms * f64::from(Self::MAX_FRAMES_PER_TICK) {
            self.accumulated = 0.0;
        }
        owed
    }
}
```

- [ ] **Step 4: Implement `WebMachine` and the frame sink**

`advance` calls `Pacer::frames_owed`, then for each frame owed runs
`run_until(MachineTime::new(self.runtime.time().get() + self.frame_ticks), &mut host)`
with `frame_ticks` from `FamilyRuntime::native_frame_ticks()`.

- [ ] **Step 5: Verify**

```bash
env -u RUSTUP_TOOLCHAIN cargo test -p emu198x-web
env -u RUSTUP_TOOLCHAIN cargo check -p emu198x-web --target wasm32-unknown-unknown
```
Expected: pass.

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(web): pace the machine off elapsed time, not the animation frame"
```

---

## Task 4: Keyboard input

**Files:**
- Create: `crates/emu198x-web/src/input.rs`
- Test: in-module `#[cfg(test)]`

**Interfaces:**
- Consumes: `WebMachine` (Task 3).
- Produces:
  ```rust
  impl<R: FamilyRuntime> WebMachine<R> {
      pub fn queue_input(&mut self, event: InputEvent);
      /// Events queued but not yet handed to the machine. Test-facing:
      /// it is how the drain-exactly-once test observes the queue.
      pub fn pending_input(&self) -> &[InputEvent];
  }
  /// Maps a DOM `KeyboardEvent.code` to a shell input event.
  pub fn input_from_dom_code(code: &str, pressed: bool) -> Option<InputEvent>;
  ```
  `test_machine()` is a shared `#[cfg(test)]` helper introduced in Task 3,
  building a `WebMachine` over a 48K runtime from the test ROM fixture.
  Queued events drain into `HostIo::input_events` on the next `advance`.

- [ ] **Step 1: Write the failing tests**

```rust
#[test]
fn a_dom_code_maps_to_a_key_event() {
    assert!(input_from_dom_code("KeyA", true).is_some());
}

#[test]
fn an_unmapped_code_is_ignored_rather_than_guessed() {
    assert!(input_from_dom_code("F13", true).is_none());
}

#[test]
fn queued_events_drain_exactly_once() {
    let mut m = test_machine();
    m.queue_input(input_from_dom_code("KeyA", true).unwrap());
    m.advance(20.0).unwrap();
    assert!(m.pending_input().is_empty(), "input must not replay next frame");
}
```

- [ ] **Step 2: Run and watch fail**

```bash
env -u RUSTUP_TOOLCHAIN cargo test -p emu198x-web input
```

- [ ] **Step 3: Implement the mapping and the drain**

Map `KeyboardEvent.code` (physical, layout-independent) rather than `key`, so a
learner on an AZERTY keyboard gets the key they pressed. Return `None` for
unmapped codes.

- [ ] **Step 4: Verify, then commit**

```bash
env -u RUSTUP_TOOLCHAIN cargo test -p emu198x-web
git commit -m "feat(web): drive the machine from physical key codes"
```

---

## Task 5: Audio through AudioWorklet

**Files:**
- Create: `crates/emu198x-web/src/audio.rs`
- Create: `crates/emu198x-web/js/worklet.js`

**Interfaces:**
- Consumes: `WebMachine` (Task 3).
- Produces: `WebAudioOutput`, implementing `emu198x_shell::AudioSink`, plus
  ```rust
  impl<R: FamilyRuntime> WebMachine<R> {
      pub fn audio_drain(&mut self) -> Vec<f32>;
      pub fn set_audio_enabled(&mut self, on: bool);
  }
  ```

Entirely unmeasured by the spike, which used `NullAudioSink`. Expect this task
to be the second-largest unknown after Task 2. Reuse
`emu198x_shell::audio::convert_audio_packet` for rate/channel conversion rather
than writing another resampler — it is not gated off wasm by Task 1.

- [ ] **Step 1: Write the failing test**

```rust
#[test]
fn pushed_samples_are_drained_in_order_and_only_once() {
    let mut out = WebAudioOutput::new(4096);
    out.push_audio(packet(&[0.25, -0.25])).unwrap();
    assert_eq!(out.drain(), vec![0.25, -0.25]);
    assert!(out.drain().is_empty());
}

#[test]
fn the_buffer_drops_oldest_rather_than_growing_without_bound() {
    let mut out = WebAudioOutput::new(2);
    out.push_audio(packet(&[1.0, 2.0, 3.0])).unwrap();
    assert_eq!(out.drain().len(), 2);
}
```

- [ ] **Step 2: Run and watch fail, then implement**

Ring buffer mirroring `audio.rs`'s existing `AudioBuffer`, drained by the
worklet. Once audio is on, prefer the audio clock as pacing master: feed
`advance` from samples consumed rather than rAF elapsed, so the machine cannot
drift against the output device.

- [ ] **Step 3: Verify, then commit**

```bash
env -u RUSTUP_TOOLCHAIN cargo test -p emu198x-web audio
git commit -m "feat(web): play machine audio through an AudioWorklet"
```

---

## Task 6: Load the learner's assembled program

**Files:**
- Modify: `crates/emu198x-web/src/lib.rs`

**Interfaces:**
- Produces:
  ```rust
  impl<R: FamilyRuntime> WebMachine<R> {
      /// Loads media from bytes. `slot` uses the machine profile's slot ids.
      pub fn load_media_bytes(&mut self, slot: &str, bytes: &[u8])
          -> Result<(), MachineError>;
  }
  ```
  Wraps `MachineCore::load_media` with a `MediaSet` built from the byte slice.
  No filesystem is involved at any point.

- [ ] **Step 1: Write the failing test**

```rust
#[test]
fn a_tap_image_loads_from_bytes_alone() {
    let mut m = test_machine();
    let tap = include_bytes!("../test-data/hello.tap");
    assert!(m.load_media_bytes("tape-1", tap).is_ok());
}

#[test]
fn an_unknown_slot_is_an_error_not_a_silent_no_op() {
    let mut m = test_machine();
    assert!(m.load_media_bytes("nonsense", &[0u8; 4]).is_err());
}
```

- [ ] **Step 2: Implement, verify, commit**

```bash
env -u RUSTUP_TOOLCHAIN cargo test -p emu198x-web
git commit -m "feat(web): load a program from bytes handed in by the page"
```

---

## Task 7: The Spectrum binding and the npm package

**Files:**
- Create: `crates/emu198x-spectrum-web/Cargo.toml`
- Create: `crates/emu198x-spectrum-web/src/lib.rs`
- Create: `crates/emu198x-spectrum-web/package.json.tmpl`
- Modify: `Cargo.toml` (workspace members)

**Interfaces:**
- Produces the JS-facing API:
  ```ts
  export class Spectrum {
    static create(canvas: HTMLCanvasElement, rom: Uint8Array): Promise<Spectrum>;
    load(slot: string, bytes: Uint8Array): void;
    start(): void;
    stop(): void;
    keyDown(code: string): void;
    keyUp(code: string): void;
    setAudioEnabled(on: boolean): void;
    setFilter(filter: "raw" | "lcd" | "crt"): void;
  }
  ```
  `create` is async because wgpu adapter acquisition is (Task 2).

- [ ] **Step 1: Bind the shell to `SpectrumRuntimeKind`**

Build firmware from bytes exactly as the spike verified:

```rust
let mut firmware = FirmwareSet::new();
firmware.push(FirmwareImage::new("sinclair-zx-spectrum-48k-rom", rom));
let runtime = SpectrumRuntimeKind::from_firmware(Model::Spectrum48KPal, &firmware)?;
```

- [ ] **Step 2: Build the package**

```bash
cd crates/emu198x-spectrum-web
env -u RUSTUP_TOOLCHAIN wasm-pack build --target web --release
```
Expected: `pkg/` produced; wasm well under 1 MB.

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(spectrum-web): expose the Spectrum to JavaScript"
```

---

## Task 8: Prove the web build is the same emulator

**Files:**
- Create: `crates/emu198x-web/tests/parity.rs`
- Create: `.github/workflows/wasm.yml`

**Interfaces:**
- Consumes: everything above.
- Produces: CI enforcement that native and wasm agree.

The accuracy bar does not move for the web. This task is what makes that claim
checkable rather than asserted.

- [ ] **Step 1: Write the parity test**

```rust
// Boot N frames and hash the framebuffer. The same machine, compiled two ways,
// must produce identical pixels — anything else is a defect, not a trade-off.
#[test]
fn wasm_and_native_agree_on_the_boot_frame() {
    let hash = boot_and_hash(200);
    assert_eq!(hash, NATIVE_BOOT_HASH_200);
}
```

`twox-hash` is already a dev-dependency of the Spectrum runtime. Generate
`NATIVE_BOOT_HASH_200` from a native run and commit it as the golden value.

- [ ] **Step 2: Run headless in both targets**

```bash
env -u RUSTUP_TOOLCHAIN cargo test -p emu198x-web --test parity
env -u RUSTUP_TOOLCHAIN wasm-pack test --headless --chrome crates/emu198x-web
```
Expected: identical hashes.

- [ ] **Step 3: Add the CI workflow**

Add a `wasm` job installing the `wasm32-unknown-unknown` target and
`wasm-pack`, running `cargo check --target wasm32-unknown-unknown` for the web
crates plus `wasm-pack test --headless --chrome`. Do **not** assert an fps floor
in CI — shared runners make that flaky. Performance stays on the native
criterion bench.

- [ ] **Step 4: Commit**

```bash
git commit -m "test(web): hold the browser build to the native pixel output"
```

---

## Task 9: The Code198x embed and one real lesson

**Files:**
- Code198x repo: embed component + one lesson using it.
- Modify: `crates/emu198x-spectrum-web/README.md`

Cross-repo, and therefore the task most likely to slip. It is last because
every interface it consumes is settled by Tasks 1-8.

- [ ] **Step 1: Publish the package to npm**

Steve owns npm publishing; there is existing precedent in the family. Confirm
the package name before the first publish — it is a permanent public
identifier.

- [ ] **Step 2: Build the embed component**

Wraps the `Spectrum` class from Task 7: canvas, ROM fetch, load of the
learner's assembled `.tap`, and start/stop tied to the element's visibility so
a lesson page with several embeds does not run several emulators at once.

- [ ] **Step 3: Convert one lesson and verify in a browser**

Screenshot the running embed and compare against the same program captured
through the native pipeline. Per project practice, "the page returns 200" is
not verification — look at the pixels.

- [ ] **Step 4: Commit in the Code198x repo**

Note the repo split: commit from inside the Code198x working copy, not the
umbrella.

---

## Decisions this plan does not make

- **Renaming `emu198x-native-video`.** Once the browser renders through it, the
  name is wrong. A rename touches the workspace broadly and is Steve's call, so
  it is filed as a separate decision rather than folded into Task 2.
- **npm package name.** Permanent and public; confirm before first publish.
- **Extending beyond the Spectrum.** `emu198x-web` is generic so a second system
  is a binding crate rather than an engineering programme, but C64 and Amiga
  embeds remain blocked on firmware rights, not on code.
