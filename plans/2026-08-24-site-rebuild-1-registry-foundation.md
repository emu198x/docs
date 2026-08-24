# Site Rebuild 1: Registry Foundation and Evidence Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Drive the site's machine list and evidence from the flagship's registry so it cannot drift, and remove every dead route.

**Architecture:** The site reads `docs/status/systems.toml` and `docs/status/current-system-usability.md` from a checkout of `emu198x/emu198x`, validates a stated contract before rendering anything, and generates `/systems/`, thirty per-machine pages and `/accuracy/` from that data. Captures join to the registry through an explicit `machineId` on each capture entry — never by pattern. Every failure is a hard build failure.

**Tech Stack:** Astro 7, Node 24 (`node:test` for unit tests — no new test runner), `smol-toml` for parsing the registry.

**Spec:** `Emu198x/docs/plans/2026-08-24-site-rebuild-design.md`

## Global Constraints

- The registry contract is exactly four fields per entry: `machine_id`, `crate`, `label`, `milestone`. Read nothing else.
- Never infer a machine join by pattern matching. `198x/decisions/...` — the flagship's `evidence-is-what-ran-not-what-was-claimed.md` records three attempts that produced wrong answers.
- Never publish a per-machine maturity figure. No percentages, no progress bars, no status pills implying maturity.
- Per-machine URLs use `machine_id` verbatim: `/systems/sinclair-zx-spectrum/`, not `/systems/zx-spectrum/`.
- Every failure listed in this plan is a hard build failure. A skipped step that reports success is the bug this work exists to remove.
- The a11y gate must stay at zero serious/critical defects in both themes: `npm run a11y`.
- Flagship checkout path comes from `EMU198X_SOURCE_ROOT`, defaulting to `../../Emu198x/emu198x` relative to the site root.

---

### Task 1: Registry reader and contract check

**Files:**
- Create: `src/lib/registry.js`
- Test: `tests/registry.test.mjs`
- Modify: `package.json` (add `smol-toml` dependency, add `test` script)

**Interfaces:**
- Produces: `readRegistry(sourceRoot) -> Machine[]` where `Machine = { machineId: string, crate: string, label: string, milestone: string }`, sorted by `machineId`. Throws `Error` with a message naming the path on any contract breach.

- [ ] **Step 1: Write the failing test**

Create `tests/registry.test.mjs`:

```javascript
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { readRegistry } from '../src/lib/registry.js';

function fixture(toml) {
  const root = mkdtempSync(join(tmpdir(), 'reg-'));
  mkdirSync(join(root, 'docs', 'status'), { recursive: true });
  if (toml !== null) {
    writeFileSync(join(root, 'docs', 'status', 'systems.toml'), toml);
  }
  return root;
}

const ONE = `
[[system]]
machine_id = "sinclair-zx-spectrum"
crate = "emu198x-spectrum"
label = "system:spectrum"
milestone = "ZX Spectrum 100%"
`;

test('reads the four contract fields', () => {
  const machines = readRegistry(fixture(ONE));
  assert.equal(machines.length, 1);
  assert.deepEqual(machines[0], {
    machineId: 'sinclair-zx-spectrum',
    crate: 'emu198x-spectrum',
    label: 'system:spectrum',
    milestone: 'ZX Spectrum 100%',
  });
});

test('sorts by machineId', () => {
  const machines = readRegistry(fixture(`${ONE}
[[system]]
machine_id = "acorn-atom"
crate = "emu198x-acorn-atom"
label = "system:atom"
milestone = "Acorn Atom 100%"
`));
  assert.deepEqual(machines.map((m) => m.machineId), ['acorn-atom', 'sinclair-zx-spectrum']);
});

test('a missing file names the path it looked in', () => {
  const root = fixture(null);
  assert.throws(() => readRegistry(root), (err) => err.message.includes('systems.toml'));
});

test('an empty registry fails', () => {
  assert.throws(() => readRegistry(fixture('# nothing here\n')), /no \[\[system\]\] entries/);
});

test('a missing field fails and names the machine', () => {
  assert.throws(
    () => readRegistry(fixture(`
[[system]]
machine_id = "acorn-atom"
crate = "emu198x-acorn-atom"
label = "system:atom"
`)),
    /acorn-atom.*milestone/s,
  );
});

test('an entry with no machine_id fails and names its index', () => {
  assert.throws(
    () => readRegistry(fixture(`
[[system]]
crate = "emu198x-acorn-atom"
label = "system:atom"
milestone = "Acorn Atom 100%"
`)),
    /entry 0.*machine_id/s,
  );
});

test('a duplicate machine_id fails', () => {
  assert.throws(() => readRegistry(fixture(`${ONE}${ONE}`)), /duplicate.*sinclair-zx-spectrum/s);
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `node --test tests/registry.test.mjs`
Expected: FAIL — `Cannot find module '../src/lib/registry.js'`

- [ ] **Step 3: Declare the dependency and add the test script**

`smol-toml` is already resolved in the tree as an Astro transitive. Declare it so a future Astro update cannot remove it.

```bash
npm pkg set dependencies.smol-toml="$(node -p "require('smol-toml/package.json').version")"
npm pkg set scripts.test="node --test 'tests/**/*.test.mjs'"
npm install
```

- [ ] **Step 4: Write the implementation**

Create `src/lib/registry.js`:

```javascript
/**
 * The machine registry, read from the flagship repo.
 *
 * `docs/status/systems.toml` is the one place the project's four naming
 * vocabularies meet, and every join in it is stated and never inferred —
 * three attempts to infer them by pattern produced wrong answers. The site
 * reads exactly the four fields below and nothing else; that is the contract.
 *
 * Every breach throws. The bug this file exists to prevent was a step that
 * skipped silently and reported success.
 */
import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { parse } from 'smol-toml';

const FIELDS = ['machine_id', 'crate', 'label', 'milestone'];

export function registryPath(sourceRoot) {
  return join(sourceRoot, 'docs', 'status', 'systems.toml');
}

export function readRegistry(sourceRoot) {
  const path = registryPath(sourceRoot);

  if (!existsSync(path)) {
    throw new Error(
      `registry: no systems.toml at ${path}. ` +
        'Set EMU198X_SOURCE_ROOT to a checkout of emu198x/emu198x.',
    );
  }

  let parsed;
  try {
    parsed = parse(readFileSync(path, 'utf8'));
  } catch (err) {
    throw new Error(`registry: ${path} did not parse as TOML: ${err.message}`);
  }

  const entries = parsed.system;
  if (!Array.isArray(entries) || entries.length === 0) {
    throw new Error(`registry: ${path} has no [[system]] entries`);
  }

  const seen = new Set();
  const machines = entries.map((entry, index) => {
    for (const field of FIELDS) {
      if (typeof entry[field] !== 'string' || entry[field].length === 0) {
        const name = entry.machine_id ?? `entry ${index}`;
        throw new Error(`registry: ${name} is missing ${field}`);
      }
    }
    if (seen.has(entry.machine_id)) {
      throw new Error(`registry: duplicate machine_id ${entry.machine_id}`);
    }
    seen.add(entry.machine_id);
    return {
      machineId: entry.machine_id,
      crate: entry.crate,
      label: entry.label,
      milestone: entry.milestone,
    };
  });

  return machines.sort((a, b) => a.machineId.localeCompare(b.machineId));
}
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `node --test tests/registry.test.mjs`
Expected: PASS — 7 tests

- [ ] **Step 6: Verify against the real registry**

Run:
```bash
node -e "
import('./src/lib/registry.js').then(({ readRegistry }) => {
  const m = readRegistry('../emu198x');
  console.log(m.length, 'machines;', m[0].machineId, '...', m.at(-1).machineId);
});
"
```
Expected: `30 machines; acorn-atom ... tatung-einstein`

- [ ] **Step 7: Commit**

```bash
git add src/lib/registry.js tests/registry.test.mjs package.json package-lock.json
git commit -m "feat: read the machine registry, and fail on a broken contract

The site is about to publish a machine list it does not own. This reads
the flagship's systems.toml and states the contract it depends on: four
fields per entry, nothing else.

Every breach throws with the path or the machine named — a missing file, a
parse failure, an empty registry, a missing field, a duplicate id. The bug
this work exists to remove was a step that skipped silently and reported
success, so nothing here degrades quietly."
```

---

### Task 2: State the capture join

**Files:**
- Modify: `src/data/boot-screenshots.js`
- Create: `src/lib/fleet.js`
- Test: `tests/fleet.test.mjs`

**Interfaces:**
- Consumes: `readRegistry(sourceRoot)` from Task 1.
- Produces: `buildFleet({ machines, captures }) -> FleetEntry[]` where `FleetEntry = { machineId, crate, label, milestone, captures: Capture[] }`, one per registry machine, sorted by `machineId`. Throws on an unknown `machineId` or a duplicate claim.

- [ ] **Step 1: Write the failing test**

Create `tests/fleet.test.mjs`:

```javascript
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildFleet } from '../src/lib/fleet.js';

const machines = [
  { machineId: 'acorn-atom', crate: 'c1', label: 'l1', milestone: 'm1' },
  { machineId: 'sega-game-gear', crate: 'c2', label: 'l2', milestone: 'm2' },
];

test('attaches captures to their stated machine', () => {
  const fleet = buildFleet({
    machines,
    captures: [{ id: 'acorn-atom', machineId: 'acorn-atom', kind: 'boot' }],
  });
  assert.equal(fleet.length, 2);
  assert.equal(fleet[0].captures.length, 1);
  assert.equal(fleet[0].captures[0].id, 'acorn-atom');
});

test('keeps machines with no capture, in place', () => {
  const fleet = buildFleet({ machines, captures: [] });
  assert.deepEqual(fleet.map((e) => e.machineId), ['acorn-atom', 'sega-game-gear']);
  assert.deepEqual(fleet.map((e) => e.captures.length), [0, 0]);
});

test('an unknown machineId fails and names the capture', () => {
  assert.throws(
    () => buildFleet({ machines, captures: [{ id: 'zx-spectrum', machineId: 'nope', kind: 'boot' }] }),
    /zx-spectrum.*nope/s,
  );
});

test('a capture with no machineId fails', () => {
  assert.throws(
    () => buildFleet({ machines, captures: [{ id: 'zx-spectrum', kind: 'boot' }] }),
    /zx-spectrum.*machineId/s,
  );
});

test('two captures of one kind claiming one machine fails', () => {
  assert.throws(
    () => buildFleet({
      machines,
      captures: [
        { id: 'a', machineId: 'acorn-atom', kind: 'boot' },
        { id: 'b', machineId: 'acorn-atom', kind: 'boot' },
      ],
    }),
    /acorn-atom.*boot/s,
  );
});

test('two captures of different kinds on one machine are fine', () => {
  const fleet = buildFleet({
    machines,
    captures: [
      { id: 'a', machineId: 'acorn-atom', kind: 'boot' },
      { id: 'b', machineId: 'acorn-atom', kind: 'software' },
    ],
  });
  assert.equal(fleet[0].captures.length, 2);
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `node --test tests/fleet.test.mjs`
Expected: FAIL — `Cannot find module '../src/lib/fleet.js'`

- [ ] **Step 3: Write the implementation**

Create `src/lib/fleet.js`:

```javascript
/**
 * Joins the site's captures to the registry's machines.
 *
 * The join is stated on each capture as `machineId`, never inferred from the
 * capture's own id — the site's ids are a fifth naming vocabulary and nine of
 * them differ from the registry's.
 *
 * The registry drives the list, so a machine with no capture still appears. A
 * page built from the captures can only show what it already has, which is how
 * twenty-eight came to look like the whole fleet.
 */
export function buildFleet({ machines, captures }) {
  const byMachine = new Map(machines.map((m) => [m.machineId, { ...m, captures: [] }]));
  const claimed = new Set();

  for (const capture of captures) {
    if (!capture.machineId) {
      throw new Error(`fleet: capture ${capture.id} has no machineId`);
    }
    const entry = byMachine.get(capture.machineId);
    if (!entry) {
      throw new Error(
        `fleet: capture ${capture.id} names machineId ${capture.machineId}, ` +
          'which is not in the registry',
      );
    }
    const key = `${capture.machineId}|${capture.kind}`;
    if (claimed.has(key)) {
      throw new Error(`fleet: two ${capture.kind} captures claim ${capture.machineId}`);
    }
    claimed.add(key);
    entry.captures.push(capture);
  }

  return [...byMachine.values()].sort((a, b) => a.machineId.localeCompare(b.machineId));
}

export function uncaptured(fleet) {
  return fleet.filter((entry) => entry.captures.length === 0).map((entry) => entry.machineId);
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `node --test tests/fleet.test.mjs`
Expected: PASS — 6 tests

- [ ] **Step 5: Add `machineId` to every capture**

Edit `src/data/boot-screenshots.js`. Add a `machineId` to each top-level entry, and to the `spectrumVariant` and `amigaVariant` helpers so variants inherit their parent machine. The nine that differ from their capture id:

| Capture id | `machineId` |
|---|---|
| `zx-spectrum` and every `spectrumVariant` | `sinclair-zx-spectrum` |
| `zx80` | `sinclair-zx80` |
| `zx81` | `sinclair-zx81` |
| `nes` | `nintendo-nes` |
| `game-boy` | `nintendo-game-boy` |
| `dragon-32` | `dragon` |
| `oric-atmos` | `oric` |
| `msx1` | `microsoft-msx1` |
| `colecovision` | `coleco-colecovision` |

The remaining nineteen take their own id verbatim: `acorn-atom`, `acorn-bbc-micro`, `acorn-electron`, `atari-2600`, `atari-5200`, `atari-7800`, `atari-800xl`, `commodore-amiga` (and every `amigaVariant`), `commodore-c64`, `commodore-pet`, `commodore-vic-20`, `jupiter-ace`, `mattel-aquarius`, `memotech-mtx`, `sega-master-system`, `sega-sg-1000`, `sord-m5`, `spectravideo-svi-328`, `tatung-einstein`.

- [ ] **Step 6: Verify the join against the real data**

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
  console.log('fleet:', fleet.length);
  console.log('uncaptured:', fl.uncaptured(fleet).join(', ') || '(none)');
});
"
```
Expected: `fleet: 30` and `uncaptured: amstrad-cpc, sega-game-gear`

If it throws instead, a `machineId` is wrong — the error names the capture and the id it claimed. Fix that entry; do not relax the check.

- [ ] **Step 7: Commit**

```bash
git add src/lib/fleet.js tests/fleet.test.mjs src/data/boot-screenshots.js
git commit -m "feat: state the capture-to-machine join instead of implying one

The site's capture ids are a fifth naming vocabulary — zx-spectrum against
sinclair-zx-spectrum, nes against nintendo-nes, dragon-32 against dragon,
and six more. The registry exists because four vocabularies already
disagreed, and it states its joins because three attempts to infer them
produced wrong answers.

So every capture now names its machine, and an id the registry does not
contain fails the build. The registry drives the fleet list, so a machine
with no capture appears as one rather than vanishing: today that is the
Amstrad CPC and the Game Gear, which is why the page has been showing
twenty-eight of thirty machines and reading as complete."
```

---

### Task 3: Read the evidence table

**Files:**
- Create: `src/lib/evidence.js`
- Test: `tests/evidence.test.mjs`

**Interfaces:**
- Produces: `readEvidence(sourceRoot) -> Map<machineId, Evidence>` where `Evidence = { ownCrates: number, sharedCrates: number, issuesUrl: string, milestoneUrl: string }`. Throws if the file is missing, has no table, or a row will not parse.

- [ ] **Step 1: Write the failing test**

Create `tests/evidence.test.mjs`:

```javascript
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { readEvidence } from '../src/lib/evidence.js';

function fixture(body) {
  const root = mkdtempSync(join(tmpdir(), 'ev-'));
  mkdirSync(join(root, 'docs', 'status'), { recursive: true });
  writeFileSync(join(root, 'docs', 'status', 'current-system-usability.md'), body);
  return root;
}

const TABLE = `# Current system usability

Prose that is not a table.

| Machine | Ships from | Own crates | Shared crates | Issues | Milestone |
|---|---|---|---|---|---|
| \`acorn-atom\` | \`emu198x-acorn-atom\` | 4 | 9 | [system:atom](https://x/issues) | [Acorn Atom 100%](https://x/ms) |
`;

test('reads a row into evidence', () => {
  const evidence = readEvidence(fixture(TABLE));
  assert.deepEqual(evidence.get('acorn-atom'), {
    ownCrates: 4,
    sharedCrates: 9,
    issuesUrl: 'https://x/issues',
    milestoneUrl: 'https://x/ms',
  });
});

test('a file with no table fails', () => {
  assert.throws(() => readEvidence(fixture('# Nothing\n')), /no evidence table/);
});

test('a row with a non-numeric count fails and names the machine', () => {
  const broken = TABLE.replace('| 4 | 9 |', '| many | 9 |');
  assert.throws(() => readEvidence(fixture(broken)), /acorn-atom/);
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `node --test tests/evidence.test.mjs`
Expected: FAIL — `Cannot find module '../src/lib/evidence.js'`

- [ ] **Step 3: Write the implementation**

Create `src/lib/evidence.js`:

```javascript
/**
 * Per-machine evidence, read from the flagship's generated status page.
 *
 * That page is produced by scripts/status/render_status.py and CI fails on
 * drift, so it is the closest thing to a checked source the site has. It
 * publishes no test counts on purpose: "They would be stale within a day, and
 * a page that is usually wrong trains people to stop reading it."
 *
 * So the facts available are the crate counts and two links. There is no
 * source here for a percentage, which is why the site publishes none.
 */
import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const ROW = /^\|\s*`([^`]+)`\s*\|\s*`[^`]+`\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*\[[^\]]*\]\(([^)]+)\)\s*\|\s*\[[^\]]*\]\(([^)]+)\)\s*\|$/;

export function evidencePath(sourceRoot) {
  return join(sourceRoot, 'docs', 'status', 'current-system-usability.md');
}

export function readEvidence(sourceRoot) {
  const path = evidencePath(sourceRoot);

  if (!existsSync(path)) {
    throw new Error(
      `evidence: no current-system-usability.md at ${path}. ` +
        'Set EMU198X_SOURCE_ROOT to a checkout of emu198x/emu198x.',
    );
  }

  const evidence = new Map();
  for (const line of readFileSync(path, 'utf8').split('\n')) {
    const match = line.match(ROW);
    if (!match) continue;
    const [, machineId, own, shared, issuesUrl, milestoneUrl] = match;
    const ownCrates = Number(own);
    const sharedCrates = Number(shared);
    if (!Number.isInteger(ownCrates) || !Number.isInteger(sharedCrates)) {
      throw new Error(`evidence: ${machineId} has non-numeric crate counts (${own}, ${shared})`);
    }
    evidence.set(machineId, { ownCrates, sharedCrates, issuesUrl, milestoneUrl });
  }

  if (evidence.size === 0) {
    throw new Error(`evidence: ${path} has no evidence table`);
  }

  return evidence;
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `node --test tests/evidence.test.mjs`
Expected: PASS — 3 tests

- [ ] **Step 5: Verify against the real file**

Run:
```bash
node -e "
import('./src/lib/evidence.js').then(({ readEvidence }) => {
  const e = readEvidence('../emu198x');
  console.log(e.size, 'machines with evidence');
  console.log('acorn-atom:', JSON.stringify(e.get('acorn-atom')));
});
"
```
Expected: `30 machines with evidence` and an object with `ownCrates`, `sharedCrates` and two URLs.

If the count is under 30, the row pattern has missed rows — fix the pattern; do not lower the expectation.

- [ ] **Step 6: Commit**

```bash
git add src/lib/evidence.js tests/evidence.test.mjs
git commit -m "feat: read per-machine evidence from the flagship's status page

That page is generated and CI fails on drift, which makes it the closest
thing to a checked source the site can cite. It publishes no test counts
deliberately, on the grounds that a page which is usually wrong trains
people to stop reading it.

So what comes back is two crate counts and two links, and that is the
whole of what the site can honestly say per machine. There is no source
here for the percentages the accuracy page currently shows, which is why
Task 6 deletes them rather than re-deriving them."
```

---

### Task 4: Rebuild the systems index from the registry

**Files:**
- Create: `src/lib/site-data.js`
- Modify: `src/pages/systems/index.astro`
- Test: manual, via the build

**Interfaces:**
- Consumes: `readRegistry`, `readEvidence`, `buildFleet`.
- Produces: `loadSiteData() -> { fleet: FleetEntry[], evidence: Map, sourceRoot: string }`. One call for every page to share, so the contract is checked once per build.

- [ ] **Step 1: Write the shared loader**

Create `src/lib/site-data.js`:

```javascript
/**
 * One load of the flagship's data per build, shared by every page that needs
 * it. Checking the contract once and throwing here means a broken registry
 * stops the build before a single page renders.
 */
import { resolve, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { readRegistry } from './registry.js';
import { readEvidence } from './evidence.js';
import { buildFleet } from './fleet.js';
import { bootScreenshots } from '../data/boot-screenshots.js';

const siteRoot = resolve(fileURLToPath(new URL('../..', import.meta.url)));

export function sourceRoot() {
  return resolve(process.env.EMU198X_SOURCE_ROOT ?? join(siteRoot, '..', 'emu198x'));
}

let cached = null;

export function loadSiteData() {
  if (cached) return cached;
  const root = sourceRoot();
  const machines = readRegistry(root);
  const evidence = readEvidence(root);
  const fleet = buildFleet({ machines, captures: bootScreenshots });

  const missing = fleet.filter((entry) => !evidence.has(entry.machineId));
  if (missing.length > 0) {
    throw new Error(
      `site-data: no evidence row for ${missing.map((m) => m.machineId).join(', ')}`,
    );
  }

  cached = { fleet, evidence, sourceRoot: root };
  return cached;
}
```

- [ ] **Step 2: Verify the loader fails without a checkout**

Run: `EMU198X_SOURCE_ROOT=/nonexistent node -e "import('./src/lib/site-data.js').then(m => m.loadSiteData()).catch(e => { console.log('OK:', e.message); process.exit(0); }).then(() => { console.log('FAIL: did not throw'); process.exit(1); })"`
Expected: `OK: registry: no systems.toml at /nonexistent/docs/status/systems.toml. Set EMU198X_SOURCE_ROOT...`

- [ ] **Step 3: Rewrite the systems index**

Modify `src/pages/systems/index.astro`. Replace its data source with `loadSiteData()`, iterating `fleet` and not the captures. For each entry render: the machine id, its crate, the boot capture if one exists, and a "No capture yet" state if none does. Keep the existing card markup, the `data-pagefind-body` attributes and the per-image rights note.

Delete the `.capture-state.published` / `.capture-state.pending` distinction in favour of two states that describe the capture, not a maturity: has a capture, or does not. Keep `--h-ink-muted` for the note text so the contrast fix from the a11y pass holds.

Each card links to `/systems/{machineId}/`.

- [ ] **Step 4: Build and check the count**

Run: `EMU198X_SOURCE_ROOT=../emu198x npm run build 2>&1 | grep 'page(s) built'`
Expected: the page count rises; `/systems/` renders thirty cards.

Verify: `grep -c 'systems/' dist/systems/index.html` returns at least 30.

- [ ] **Step 5: Run the accessibility gate**

Run: `npm run a11y`
Expected: `0 defect(s)`

- [ ] **Step 6: Commit**

```bash
git add src/lib/site-data.js src/pages/systems/index.astro
git commit -m "feat: drive the systems page from the registry, not from the captures

The page listed the captures it happened to have, so twenty-eight looked
like the fleet and the two machines with no capture were invisible. It now
lists the registry's thirty and says plainly which have no capture.

The loader checks the whole contract once per build and throws, so a
broken registry stops the build before a page renders instead of
publishing a shorter fleet."
```

---

### Task 5: Per-machine pages

**Files:**
- Create: `src/pages/systems/[machine].astro`
- Test: manual, via the build

**Interfaces:**
- Consumes: `loadSiteData()`.
- Produces: thirty routes at `/systems/<machine_id>/`.

- [ ] **Step 1: Write the page**

Create `src/pages/systems/[machine].astro`:

```astro
---
/**
 * One page per registry machine.
 *
 * The route parameter is the registry's own machine_id, so the site's public
 * vocabulary and the registry's are the same string. This is the one place to
 * stop a fifth naming vocabulary spreading into URLs.
 */
import BaseLayout from '@layouts/BaseLayout.astro';
import { loadSiteData } from '@lib/site-data.js';

export async function getStaticPaths() {
  const { fleet, evidence } = loadSiteData();
  return fleet.map((entry) => ({
    params: { machine: entry.machineId },
    props: { entry, evidence: evidence.get(entry.machineId) },
  }));
}

const { entry, evidence } = Astro.props;
const boot = entry.captures.find((c) => c.kind === 'boot');
---

<BaseLayout
  title={entry.machineId}
  description={`Emu198x evidence for ${entry.machineId}: boot capture, crate coverage, and open work.`}
>
  <main class="container" data-pagefind-body>
    <p class="eyebrow">System</p>
    <h1>{entry.machineId}</h1>
    <p class="lede">Ships from <code>{entry.crate}</code>.</p>

    {boot ? (
      <figure>
        <img src={boot.image} alt={boot.title} loading="lazy" />
        <figcaption>{boot.caption} {boot.rightsNote}</figcaption>
      </figure>
    ) : (
      <p class="no-capture">No capture yet for this machine.</p>
    )}

    <h2>Evidence</h2>
    <dl>
      <dt>Own crates</dt>
      <dd>{evidence.ownCrates}</dd>
      <dt>Shared crates</dt>
      <dd>{evidence.sharedCrates}</dd>
    </dl>
    <p>
      A crate in exactly one shipping closure is this machine's own, so its tests are
      evidence about this machine. A shared crate is common to several and distinguishes
      nothing.
    </p>

    <h2>Open work</h2>
    <p>
      <a href={evidence.issuesUrl}>Open issues</a> ·
      <a href={evidence.milestoneUrl}>Milestone</a>
    </p>
    <p>A closed milestone says its issues were closed. It says nothing about the machine.</p>
  </main>
</BaseLayout>
```

- [ ] **Step 2: Build and count the routes**

Run: `EMU198X_SOURCE_ROOT=../emu198x npm run build 2>&1 | grep 'page(s) built'`
Verify: `find dist/systems -name index.html | wc -l`
Expected: `31` — the index plus thirty machines.

- [ ] **Step 3: Check two known URLs resolve**

Run:
```bash
test -f dist/systems/sinclair-zx-spectrum/index.html && echo "spectrum OK"
test -f dist/systems/amstrad-cpc/index.html && echo "cpc OK"
grep -q 'No capture yet' dist/systems/amstrad-cpc/index.html && echo "cpc states its gap"
```
Expected: all three print.

- [ ] **Step 4: Run the accessibility gate**

Run: `npm run a11y`
Expected: `0 defect(s)` across the larger route set, both themes.

- [ ] **Step 5: Commit**

```bash
git add src/pages/systems/\[machine\].astro
git commit -m "feat: give every machine in the registry its own page

Thirty pages keyed by machine_id, so a public URL and the registry entry
behind it are the same string. Each states what can be honestly said: the
shipping crate, the boot capture where one exists, the own and shared
crate counts, and where the open work is tracked.

Own and shared are explained on the page rather than presented as a score.
A crate in one shipping closure is evidence about that machine; a shared
one distinguishes nothing, and a page that showed a single number would
hide the difference."
```

---

### Task 6: Rebuild the accuracy page on evidence

**Files:**
- Modify: `src/pages/accuracy/index.astro`

- [ ] **Step 1: Delete the hand-typed dataset**

Remove the `systems` array — roughly lines 4 to 264 — along with every reference to `progress`, `status` and the `.meter` / `.percent` / `.status` markup that renders them. Keep `sourceTiers`, `comparisonRules` and `referenceSources`; those are editorial prose about method, not per-machine claims.

- [ ] **Step 2: Render the evidence table instead**

Replace the progress table with one built from `loadSiteData()`: a row per registry machine with own crates, shared crates, whether a boot capture exists, and links to issues and the milestone. Keep the existing `.table-wrap` wrapper with its `tabindex="0"`, `role="region"` and label from the accessibility pass.

Add a short paragraph above the table stating why there are no percentages, quoting the flagship: test counts "would be stale within a day, and a page that is usually wrong trains people to stop reading it."

- [ ] **Step 3: Verify no percentages survive**

Run:
```bash
EMU198X_SOURCE_ROOT=../emu198x npm run build > /dev/null 2>&1
grep -cE '[0-9]+%' dist/accuracy/index.html
```
Expected: `0`

- [ ] **Step 4: Verify the row count**

Run: `grep -c '<tr' dist/accuracy/index.html`
Expected: at least 31 — a header row plus thirty machines.

- [ ] **Step 5: Run the accessibility gate**

Run: `npm run a11y`
Expected: `0 defect(s)`

- [ ] **Step 6: Commit**

```bash
git add src/pages/accuracy/index.astro
git commit -m "fix: stop the accuracy page claiming maturity it cannot evidence

The page was 265 lines of hand-typed data: twenty-eight machines with
hand-typed progress percentages and hand-typed status pills. That is a
claim standing in for evidence, which the flagship's
evidence-is-what-ran-not-what-was-claimed rules out for anything reporting
per-machine maturity. It had already drifted two machines behind the
registry.

There is no honest source for a percentage. The flagship declines to
publish test counts on purpose, so the page now shows what can be
evidenced — own and shared crates, whether the machine has been seen to
boot, and where its open work is tracked — and says why the numbers are
gone."
```

---

### Task 7: Remove the sync and the dead routes

**Files:**
- Delete: `scripts/sync-public-docs.mjs`
- Modify: `package.json`, `src/components/SiteHeader.astro`, `src/layouts/DocLayout.astro`, `astro.config.mjs`, `.gitignore`

- [ ] **Step 1: Delete the sync and its scripts**

```bash
git rm scripts/sync-public-docs.mjs
npm pkg delete scripts.sync
npm pkg set scripts.dev="astro dev"
npm pkg set scripts.build="astro build && node scripts/check-rendered-spacing.mjs && npx pagefind --site dist"
```

- [ ] **Step 2: Remove the dead nav entries**

In `src/components/SiteHeader.astro`, delete the `Status` and `MCP` items — `/docs/status/current-system-usability/` and `/docs/features/mcp/`. Task 8 of Plan 3 rebuilds the nav around the new documentation set; until then the nav must contain no route that does not exist.

In `src/layouts/DocLayout.astro`, delete the sidebar links to `/docs/systems/` and every `/docs/features/*` path. Keep Getting Started, Downloads and Changelog.

- [ ] **Step 3: Redirect the one live route that moves**

In `astro.config.mjs`, add:

```javascript
  redirects: {
    '/docs/status/current-system-usability': '/accuracy/',
  },
```

The five `/docs/features/*` and `/docs/systems/` routes get no redirect. They have never resolved, so there is nothing to preserve.

- [ ] **Step 4: Stop ignoring the synced content directory**

In `.gitignore`, remove the `src/content/docs/` line, and delete the directory if present: `rm -rf src/content/docs`. Nothing writes it now.

- [ ] **Step 5: Verify no route in the nav 404s**

Run:
```bash
EMU198X_SOURCE_ROOT=../emu198x npm run build > /dev/null 2>&1
node -e "
import { readFileSync, existsSync } from 'node:fs';
const html = readFileSync('dist/index.html', 'utf8');
const hrefs = [...html.matchAll(/href=\"(\/[^\"#]*)\"/g)].map(m => m[1]);
const bad = [...new Set(hrefs)].filter(h => !existsSync('dist' + h.replace(/\/\$/, '') + '/index.html') && !existsSync('dist' + h));
console.log(bad.length ? 'DEAD: ' + bad.join(' ') : 'no dead internal links');
process.exit(bad.length ? 1 : 0);
"
```
Expected: `no dead internal links`

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "fix: delete the sync that published five links to nothing

sync-public-docs.mjs copied five paths out of the emulator repo. They have
never existed there — the feature documents live in emu198x/docs, at
different paths, in a repo this workflow does not check out. The sync
skipped each missing file without complaining, so CI built eight pages,
reported success, and published a nav pointing at nothing.

The nav loses those entries, and the one live route that moves —
/docs/status/current-system-usability/ — redirects to /accuracy/, which
now holds its content. The five that never resolved get no redirect;
there is nothing to preserve. A link check runs over the built site so a
nav entry cannot outlive its page again."
```

---

### Task 8: Notice registry drift within a day

**Files:**
- Modify: `.github/workflows/pages.yml`

- [ ] **Step 1: Add the daily trigger**

In `.github/workflows/pages.yml`, extend the `on:` block:

```yaml
on:
  push:
    branches:
      - main
  # The registry and the evidence table live in emu198x/emu198x, so a change
  # there can break this build with nothing here to fire it. Daily and not
  # weekly: a week is a long time for a broken fleet list to sit on a public
  # site, and the contract check is what turns the break into a failure.
  schedule:
    - cron: "0 6 * * *"
  workflow_dispatch:
```

- [ ] **Step 2: Verify the workflow still parses**

Run:
```bash
python3 -c "
import yaml
d = yaml.safe_load(open('.github/workflows/pages.yml'))
print('triggers:', list(d[True].keys()))
print('steps:', [s.get('name') for s in d['jobs']['build']['steps']])
"
```
Expected: triggers include `push`, `schedule` and `workflow_dispatch`; the step list still has `Build site`, `Install the browser the sweep drives`, `Check accessibility`, `Upload Pages artifact` in that order.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/pages.yml
git commit -m "ci: notice a broken registry within a day

The site now publishes a machine list it does not own, and it builds only
on a push to its own main — so a change to systems.toml that broke the
contract would sit undetected until somebody happened to touch this repo.

A daily build runs the contract check against whatever the flagship
currently holds. It is the same backstop asm198x runs for the same reason:
a sibling repo owns content this site publishes. A repository_dispatch
would cut a day to minutes but needs a workflow change and a token in the
other repo; the schedule needs neither and closes most of the gap."
```

---

## Self-Review

**Spec coverage.** Data flow → Tasks 1, 3, 4. The join → Task 2. Registry contract and check → Tasks 1, 4. Daily schedule → Task 8. Systems index → Task 4. Per-machine pages → Task 5. Accuracy rebuild → Task 6. Removals and redirects → Task 7. Error handling table → Tasks 1, 3, 4 (every row is a throw). Testing → the `npm run a11y` step closing Tasks 4, 5 and 6, plus the link check in Task 7.

Not covered here, by design: the capture work (Plan 2) and the documentation set and homepage (Plan 3). The nav is left short at the end of Task 7 and rebuilt in Plan 3; the site is deployable in between, with no dead links.

**Type consistency.** `machineId` is camelCase throughout the site's own code and `machine_id` only inside the TOML; `readRegistry` maps between them once, in Task 1. `FleetEntry.captures` is always an array, empty when there is none, so no page needs a null check. `readEvidence` returns a `Map`, and every consumer reaches it through `loadSiteData()`, which has already proved every machine has a row.

**Placeholder scan.** No TBDs. Every step names its command and its expected output. Task 4 Step 3 and Task 6 Steps 1–2 describe edits to existing files in prose instead of as full listings, because both files are long and the change is a replacement of one data source with another; the interfaces they consume are given exactly.
