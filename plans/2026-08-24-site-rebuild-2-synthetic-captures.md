# Site Rebuild 2: Synthetic Cartridge Captures Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Take the fleet from twenty captured machines to twenty-nine, using cartridges the project owns, so nobody needs to supply media to see the site complete.

**Architecture:** Eight site entries currently render "Waiting on local media" because their machines need a cartridge. The flagship already builds free cartridges for exactly this: plate cartridges that draw the Emu198x wordmark in each machine's own tiles, and Sega boot cartridges that put a known colour through CRAM. The capture script gains a `{source}` token so it can point at them, and the `mediaEnv` gate comes off.

**Tech Stack:** Node 24, the existing `scripts/capture-boot-screenshots.mjs`, `cargo run` against the flagship checkout.

**Spec:** `Emu198x/docs/plans/2026-08-24-site-rebuild-design.md` § "Closing the capture gap with synthetic cartridges"

**Depends on:** Plan 1 Task 2 — every capture must already carry a `machineId`.

## Global Constraints

- A capture made from a cartridge the project owns carries a different per-image note from one made from supplied firmware. Do not reuse the standing "Captured from locally supplied firmware or media" wording for synthetic captures; it implies a provenance question that does not arise.
- The site-wide rights notice in the footer stays. Firmware captures still need it.
- Never commit a cartridge or firmware image to the site repo. Cartridges are referenced in the flagship checkout, and only the resulting PNG is committed here.
- Sord M5 has no synthetic cartridge and stays uncaptured. Do not fabricate one in the site repo; that is flagship work.
- The a11y gate must stay at zero serious/critical defects: `npm run a11y`.

---

### Task 1: Point the capture script at the flagship's own files

**Files:**
- Modify: `scripts/capture-boot-screenshots.mjs`
- Test: `tests/capture-tokens.test.mjs`

**Interfaces:**
- Produces: a `{source}` token usable in `capture.args` and `capture.requiredFiles`, resolving to the flagship checkout root. `resolveToken(arg, capture, output, scriptPath, sourceRoot)` and `missingInputs(capture, sourceRoot)` both take the root explicitly.

- [ ] **Step 1: Write the failing test**

Create `tests/capture-tokens.test.mjs`:

```javascript
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { resolveToken, missingInputs } from '../scripts/capture-boot-screenshots.mjs';

test('{source} resolves to the flagship root', () => {
  const arg = resolveToken('{source}/test-data/sega/synthetic-cart/game-gear.gg', {}, '/out.png', null, '/src');
  assert.equal(arg, '/src/test-data/sega/synthetic-cart/game-gear.gg');
});

test('{output} still resolves', () => {
  assert.equal(resolveToken('{output}', {}, '/out.png', null, '/src'), '/out.png');
});

test('a required {source} file that is absent is reported', () => {
  const missing = missingInputs({ requiredFiles: ['{source}/nope.gg'] }, '/src');
  assert.equal(missing.length, 1);
  assert.match(missing[0], /nope\.gg/);
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `node --test tests/capture-tokens.test.mjs`
Expected: FAIL — the script exports neither function.

- [ ] **Step 3: Add the token and export the helpers**

In `scripts/capture-boot-screenshots.mjs`:

Change `resolveToken` to take `sourceRoot` and handle `{source}`, and export it:

```javascript
export function resolveToken(arg, capture, output, scriptPath, sourceRoot) {
  if (arg === '{output}') return output;
  if (arg === '{script}') return scriptPath;
  if (arg === '{media}') return expandPath(process.env[capture.mediaEnv] ?? '');
  return expandPath(
    arg.replaceAll('{output}', output).replaceAll('{source}', sourceRoot),
  );
}
```

Change `missingInputs` to take `sourceRoot`, resolve `{source}` before the existence check, and export it:

```javascript
export function missingInputs(capture, sourceRoot) {
  const missing = [];
  if (capture.mediaEnv) {
    const value = process.env[capture.mediaEnv];
    if (!value) {
      missing.push(`${capture.mediaEnv} is not set`);
    } else if (!existsSync(expandPath(value))) {
      missing.push(`${capture.mediaEnv} does not exist: ${value}`);
    }
  }

  for (const path of capture.requiredFiles ?? []) {
    const resolved = expandPath(path.replaceAll('{source}', sourceRoot));
    if (!existsSync(resolved)) {
      missing.push(`missing ${path}`);
    }
  }

  return missing;
}
```

Update both call sites to pass `sourceRoot`, and `buildCargoArgs` to thread it through.

Guard the top-level run so importing the module for tests does not execute a capture. Wrap the loop and the argument parsing in:

```javascript
const isMain = process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) {
  // existing argument parsing and capture loop
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `node --test tests/capture-tokens.test.mjs`
Expected: PASS — 3 tests

- [ ] **Step 5: Verify the existing captures still resolve**

Run: `EMU198X_SOURCE_ROOT=../emu198x node scripts/capture-boot-screenshots.mjs --dry-run 2>&1 | head -5`
Expected: `dry <id>: cargo run --release ...` lines, and no crash.

- [ ] **Step 6: Commit**

```bash
git add scripts/capture-boot-screenshots.mjs tests/capture-tokens.test.mjs
git commit -m "feat: let a capture point at a file in the flagship checkout

The cartridges that make the next task possible live in the emulator repo,
not on the machine running the capture. Args could already be relative
because cargo runs with that repo as its working directory, but the
existence check runs here, where the same relative path means something
else — so a missing cartridge would have been discovered as a cargo
failure instead of as a missing input.

{source} resolves to the checkout in both places. The helpers are exported
and the run loop is guarded so importing the script for tests does not
start capturing."
```

---

### Task 2: Capture the Sega machines, including the Game Gear

**Files:**
- Modify: `src/data/boot-screenshots.js`

**Interfaces:**
- Consumes: the `{source}` token from Task 1, `machineId` from Plan 1 Task 2.

- [ ] **Step 1: Confirm the cartridges exist**

Run:
```bash
for f in master-system.sms game-gear.gg sg-1000.sg; do
  test -f "../emu198x/test-data/sega/synthetic-cart/$f" && echo "OK $f" || echo "MISSING $f"
done
```
Expected: three `OK` lines. If any is missing, stop — the cartridge is flagship work and this task cannot proceed without it.

- [ ] **Step 2: Convert the two gated Sega entries**

In `src/data/boot-screenshots.js`, for `sega-master-system` and `sega-sg-1000`: delete `mediaEnv` and `mediaLabel`, and set the cartridge argument to the synthetic one. For the Master System:

```javascript
    capture: {
      package: 'emu198x-sega-master-system',
      args: [
        '--cart', '{source}/test-data/sega/synthetic-cart/master-system.sms',
        '--frames', '120',
        '--screenshot', '{output}',
      ],
      requiredFiles: ['{source}/test-data/sega/synthetic-cart/master-system.sms'],
    },
```

Use `--cart {source}/test-data/sega/synthetic-cart/sg-1000.sg` and package `emu198x-sega-sg-1000` for the SG-1000.

Set the caption and rights note on both to describe what they are:

```javascript
    caption: 'Synthetic boot cartridge: a known colour written through CRAM and the VDP registers.',
    rightsNote: 'Captured from a synthetic cartridge built from source in this project. No third-party software is involved.',
```

- [ ] **Step 3: Add the Game Gear**

Add a new entry. It has never been on the site:

```javascript
  {
    id: 'sega-game-gear',
    machineId: 'sega-game-gear',
    name: 'Sega Game Gear',
    kind: 'boot',
    title: 'Game Gear boot',
    image: '/media/boot/sega-game-gear.png',
    caption: 'Synthetic boot cartridge: a known colour written through CRAM and the VDP registers. The Game Gear has no firmware to boot into, so a cartridge is the only way to show it running at all.',
    rightsNote: 'Captured from a synthetic cartridge built from source in this project. No third-party software is involved.',
    capture: {
      package: 'emu198x-sega-game-gear',
      args: [
        '--cart', '{source}/test-data/sega/synthetic-cart/game-gear.gg',
        '--frames', '120',
        '--screenshot', '{output}',
      ],
      requiredFiles: ['{source}/test-data/sega/synthetic-cart/game-gear.gg'],
    },
  },
```

- [ ] **Step 4: Capture all three**

Run:
```bash
EMU198X_SOURCE_ROOT=../emu198x node scripts/capture-boot-screenshots.mjs \
  --only=sega-master-system,sega-sg-1000,sega-game-gear
```
Expected: `boot screenshots: 3 captured, 0 skipped, 0 failed`

The first run compiles the crates and will take several minutes.

- [ ] **Step 5: Look at the images**

Run: `open public/media/boot/sega-game-gear.png public/media/boot/master-system.png public/media/boot/sg-1000.png`

Check each is a solid colour field, not black. Black means the machine never executed the cartridge, which is the failure the cartridge was designed to expose — treat it as a real bug and report it, do not commit the image.

Verify the Game Gear image is 160×144 and the other two 288×240:
```bash
node -e "
const { readFileSync } = require('node:fs');
for (const f of ['sega-game-gear','master-system','sg-1000']) {
  const b = readFileSync('public/media/boot/' + f + '.png');
  console.log(f, b.readUInt32BE(16) + 'x' + b.readUInt32BE(20));
}
"
```
Expected: `sega-game-gear 160x144`, and 288×240 for the other two.

- [ ] **Step 6: Commit**

```bash
git add src/data/boot-screenshots.js public/media/boot/sega-game-gear.png public/media/boot/master-system.png public/media/boot/sg-1000.png
git commit -m "feat: capture the Sega machines from the project's own cartridges

The Master System and SG-1000 were gated behind local media, and the Game
Gear was not on the site at all — it has no firmware to boot into, so
there was no screen to photograph without a cartridge.

The flagship builds synthetic cartridges for exactly this: fully free,
deterministic, and drawing a known colour through CRAM and the VDP
registers instead of poking a framebuffer, so a capture proves the CPU
ran and a frame reached the screen. The images confirm the geometry the
machines do not share — 160x144 for the Game Gear's LCD against 288x240
for a television.

These carry their own rights note. The standing one answers a provenance
question that does not arise for a cartridge we wrote."
```

---

### Task 3: Capture the NES, Game Boy and the Ataris from the plate cartridges

**Files:**
- Modify: `src/data/boot-screenshots.js`

- [ ] **Step 1: Confirm the cartridges exist and find their names**

Run:
```bash
ls ../emu198x/test-data/synthetic-cartridges/
ls ../emu198x/test-data/nintendo/synthetic-cart/ ../emu198x/test-data/atari/synthetic-cart/
```
Expected: `*-logo.*` images in `synthetic-cartridges/`, plus `nes.nes`, `game-boy.gb`, `atari-2600.a26` and `atari-7800.a78` in the per-vendor directories.

Prefer the plate cartridges in `synthetic-cartridges/` — they draw the Emu198x wordmark, which makes a coherent capture set. Use a per-vendor boot cartridge only where no plate image exists for that machine.

- [ ] **Step 2: Convert the five gated entries**

For `nes`, `game-boy`, `atari-2600`, `atari-5200` and `atari-7800`: delete `mediaEnv` and `mediaLabel`, point the cartridge argument at the plate image via `{source}`, and add the matching `requiredFiles`. Each keeps its existing `package` and its `--frames` count. For the NES:

```javascript
    capture: {
      package: 'emu198x-nes',
      args: [
        '--rom', '{source}/test-data/synthetic-cartridges/nintendo-nes-logo.nes',
        '--frames', '300',
        '--screenshot', '{output}',
      ],
      requiredFiles: ['{source}/test-data/synthetic-cartridges/nintendo-nes-logo.nes'],
    },
```

Set the caption and rights note on all five:

```javascript
    caption: 'Synthetic plate cartridge: the Emu198x wordmark, set in this machine\'s own tiles and drawn through its real video path.',
    rightsNote: 'Captured from a synthetic cartridge built from source in this project. No third-party software is involved.',
```

- [ ] **Step 3: Capture them**

Run:
```bash
EMU198X_SOURCE_ROOT=../emu198x node scripts/capture-boot-screenshots.mjs \
  --only=nes,game-boy,atari-2600,atari-5200,atari-7800
```
Expected: `boot screenshots: 5 captured, 0 skipped, 0 failed`

If a machine fails, report the cargo output. Do not substitute a different cartridge to make it pass.

- [ ] **Step 4: Look at the images**

Run: `open public/media/boot/nes.png public/media/boot/game-boy.png public/media/boot/atari-2600.png public/media/boot/atari-5200.png public/media/boot/atari-7800.png`

Each should show the divider plate — the prefix cell and the `198x` cell — legible in that machine's palette. A blank or garbled frame is a real failure; report it and do not commit it.

- [ ] **Step 5: Commit**

```bash
git add src/data/boot-screenshots.js public/media/boot/nes.png public/media/boot/game-boy.png public/media/boot/atari-2600.png public/media/boot/atari-5200.png public/media/boot/atari-7800.png
git commit -m "feat: capture the cartridge machines from the plate cartridges

The NES, Game Boy and three Ataris were all gated behind local media, so
five of the machines with the least to prove in public were the five with
no way to prove it.

The flagship's plate cartridges draw the Emu198x wordmark in each
machine's own tiles, assembled with Asm198x and rendered through the real
video path — CPU, video chip, nametable — rather than poking a
framebuffer. The NES cartridge even picks its prefix-cell colour by citing
family-visual-identity.md and taking the nearest entry its palette offers
to the Emu198x blue.

So the fleet gains five real screenshots that need nothing supplied, and
the set carries the family wordmark rendered by the hardware itself."
```

---

### Task 4: Capture the Amstrad CPC from its firmware

**Files:**
- Modify: `src/data/boot-screenshots.js`

- [ ] **Step 1: Confirm the firmware is present and the right size**

Run:
```bash
node -e "
const { statSync } = require('node:fs');
const p = process.env.HOME + '/.emu198x/roms/amstrad-cpc/cpc464.rom';
console.log(p, statSync(p).size, 'bytes');
"
```
Expected: `32768 bytes` — 16 KB OS plus 16 KB BASIC, which is what `emu198x-amstrad-cpc` expects.

If it is absent, this task cannot proceed; the CPC stays uncaptured and the fleet reads twenty-eight. That is a legitimate outcome, not a failure to hide.

- [ ] **Step 2: Add the entry**

```javascript
  {
    id: 'amstrad-cpc',
    machineId: 'amstrad-cpc',
    name: 'Amstrad CPC 464',
    kind: 'boot',
    title: 'Amstrad CPC 464 boot',
    image: '/media/boot/amstrad-cpc.png',
    caption: 'CPC 464 firmware boot capture.',
    rightsNote: 'Captured from locally supplied firmware or media. Emu198x does not distribute ROMs, disks, tapes, or cartridges.',
    capture: {
      package: 'emu198x-amstrad-cpc',
      args: [
        '--rom', '~/.emu198x/roms/amstrad-cpc/cpc464.rom',
        '--frames', '300',
        '--screenshot', '{output}',
      ],
      requiredFiles: ['~/.emu198x/roms/amstrad-cpc/cpc464.rom'],
    },
  },
```

This one keeps the standing rights note: it is a manufacturer ROM, so the provenance question the notice answers does apply.

- [ ] **Step 3: Capture it**

Run: `EMU198X_SOURCE_ROOT=../emu198x node scripts/capture-boot-screenshots.mjs --only=amstrad-cpc`
Expected: `boot screenshots: 1 captured, 0 skipped, 0 failed`

- [ ] **Step 4: Look at the image**

Run: `open public/media/boot/amstrad-cpc.png`
Expected: the CPC's boot screen with its BASIC banner and `Ready` prompt.

- [ ] **Step 5: Commit**

```bash
git add src/data/boot-screenshots.js public/media/boot/amstrad-cpc.png
git commit -m "feat: capture the Amstrad CPC, which was in the registry but not the site

The CPC ships from its own crate and has done for some time; it was
missing from the site because the site's list came from the captures it
happened to have rather than from the registry. Its firmware was on this
machine the whole time.

Unlike the cartridge machines in the preceding tasks, this is a
manufacturer ROM, so it keeps the standing rights note."
```

---

### Task 5: Confirm the fleet, and state what is left

**Files:**
- Modify: `src/pages/systems/index.astro` (copy only)

- [ ] **Step 1: Count the fleet**

Run:
```bash
node -e "
Promise.all([
  import('./src/lib/registry.js'),
  import('./src/lib/fleet.js'),
  import('./src/data/boot-screenshots.js'),
]).then(([reg, fl, data]) => {
  const fleet = fl.buildFleet({
    machines: reg.readRegistry('../emu198x'),
    captures: data.bootScreenshots,
  });
  const gaps = fl.uncaptured(fleet);
  console.log('machines:', fleet.length, 'captured:', fleet.length - gaps.length);
  console.log('uncaptured:', gaps.join(', ') || '(none)');
});
"
```
Expected: `machines: 30 captured: 29` and `uncaptured: sord-m5`

- [ ] **Step 2: Verify every referenced image exists**

Run:
```bash
node -e "
import('./src/data/boot-screenshots.js').then(({ bootScreenshots }) => {
  const { existsSync } = require('node:fs');
  const missing = bootScreenshots.filter(s => !existsSync('public' + s.image));
  console.log(missing.length ? 'MISSING: ' + missing.map(m => m.id).join(' ') : 'every capture has an image');
  process.exit(missing.length ? 1 : 0);
});
"
```
Expected: `every capture has an image`

- [ ] **Step 3: Say why Sord M5 is uncaptured**

In `src/pages/systems/index.astro`, where an entry has no capture, render the reason instead of a bare absence. Add a short note beneath the fleet list:

> One machine has no capture. The Sord M5 needs a cartridge to show anything and has no synthetic one yet — it pairs a Z80 with a TMS9918, the same as the SG-1000, so one is possible; it has not been written.

- [ ] **Step 4: Build and run the gate**

Run:
```bash
EMU198X_SOURCE_ROOT=../emu198x npm run build > /dev/null 2>&1 && npm run a11y
```
Expected: `0 defect(s)`

- [ ] **Step 5: Commit**

```bash
git add src/pages/systems/index.astro
git commit -m "docs: name the one machine still without a capture, and why

The fleet reads twenty-nine of thirty. The Sord M5 needs a cartridge to
show anything and has no synthetic one, so the page says that instead of
leaving a silent gap for a reader to interpret.

It pairs a Z80 with a TMS9918, the same as the SG-1000, so a cartridge for
it is a plausible piece of flagship work. Naming the reason is what makes
that visible as a task instead of as an oversight."
```

---

## Self-Review

**Spec coverage.** The `{source}` token → Task 1. Sega machines including Game Gear → Task 2. Plate cartridges for the NES, Game Boy and Ataris → Task 3. Amstrad CPC → Task 4. The rights-note split between synthetic and firmware captures → Tasks 2, 3 (synthetic wording) and 4 (standing wording). Sord M5 stated and not hidden → Task 5. The visual inconsistency between plate and colour-field cartridges is recorded in the spec as accepted, and Task 5 Step 3 names the remaining gap; no task attempts to resolve it, because writing Sega plate cartridges is flagship work.

**Type consistency.** `resolveToken` and `missingInputs` both gain `sourceRoot` as their final parameter in Task 1 and are used with that signature in every later step. `machineId` on the new Game Gear, CPC and converted entries matches the registry ids verified in Plan 1 Task 2. `requiredFiles` entries use the same `{source}` prefix that `missingInputs` expands.

**Placeholder scan.** No TBDs. Every capture step names its command and its expected output line. Steps that inspect an image say what a correct one looks like and what a failure looks like, so "it produced a file" is not mistaken for "it worked" — a black frame from a Sega cartridge is precisely the failure that cartridge exists to catch.
