# Site Rebuild 3: Documentation Set and Homepage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the site a curated documentation set it owns, and a homepage that argues one thing instead of three.

**Architecture:** Five documentation pages authored in the site repo, edited down from roughly 2,500 lines of design documents in `emu198x/docs/features/`. The internal repo is never published, so internal thinking cannot leak into the site by accident. The homepage leads with the automation surface and shows a real script with its real output.

**Tech Stack:** Astro 7, the existing `DocLayout`, the `198x-ui` kit for furniture.

**Spec:** `Emu198x/docs/plans/2026-08-24-site-rebuild-design.md` § "The documentation set" and § "Homepage"

**Depends on:** Plan 1 Task 7 — the dead nav entries must already be gone, so this task rebuilds a nav instead of editing one that lies.

## Global Constraints

- **Curation is authorship.** Do not copy a source document and delete the headings you dislike. Each page is written for a reader arriving cold, with the internal framing gone.
- Every page answers, in this order: what this is and the mental model needed; what works today; how to use it, with a runnable example; what does not work yet. The fourth section is not optional.
- `emu198x/docs/features/frontend.md` is **not published**. Its 913 lines are launcher design — `## Optional: Unified Launcher`, `### Design Principles`, per-system behaviour tables. Its user-facing residue becomes one section of Getting started.
- Never state a capability the emulator does not have. Where a source document says a thing is planned, the site says so too.
- House prose style applies: `vale <file>` must report no errors, warnings or suggestions before a commit.
- The a11y gate must stay at zero serious/critical defects: `npm run a11y`.
- Long-form prose is Literata, headings Archivo, code JetBrains Mono. `DocLayout` already sets this; do not override it per page.

---

### Task 1: The documentation index and the nav

**Files:**
- Modify: `src/pages/docs/index.astro`
- Modify: `src/components/SiteHeader.astro`
- Modify: `src/layouts/DocLayout.astro`

- [ ] **Step 1: Rewrite the nav around the new set**

In `src/components/SiteHeader.astro`, set the items to routes that will all exist by the end of this plan:

```javascript
const items = [
  { label: 'Start', href: '/docs/getting-started/' },
  { label: 'Automation', href: '/docs/mcp/' },
  { label: 'Systems', href: '/systems/' },
  { label: 'Accuracy', href: '/accuracy/' },
  { label: 'Download', href: '/downloads/' },
  { label: 'Docs', href: '/docs/' },
];
```

`Automation` points at MCP because that is the spine's front door, and a reader who wants the rest reaches it from there.

- [ ] **Step 2: Rewrite the docs sidebar**

In `src/layouts/DocLayout.astro`, set the sidebar links to: Getting Started, MCP, Scripting, Capture, Observability, Downloads, Changelog. Every one must resolve by the end of this plan.

- [ ] **Step 3: Rewrite the docs index**

In `src/pages/docs/index.astro`, replace the page body with a short orientation and one line per page saying what question it answers. Lead with the automation three — MCP, Scripting, Capture — because they are the spine.

- [ ] **Step 4: Check the prose**

Run: `vale src/pages/docs/index.astro`
Expected: `0 errors, 0 warnings and 0 suggestions`

- [ ] **Step 5: Commit**

```bash
git add src/components/SiteHeader.astro src/layouts/DocLayout.astro src/pages/docs/index.astro
git commit -m "feat: rebuild the nav around the documentation the site will own

The nav lost two entries when the sync went, because they pointed at pages
that never existed. This puts back a set that will all resolve, and leads
with Automation instead of burying the thing the site is actually about
three clicks down.

The index says what question each page answers, so a reader can pick one
without opening all five."
```

---

### Task 2: Getting started

**Files:**
- Modify: `src/pages/docs/getting-started.astro`

**Source material:** `emu198x/docs/features/frontend.md` (the launcher section only), the flagship `README.md`, and `emu198x/docs/adding-a-system.md` for what a machine needs to run.

- [ ] **Step 1: Read the sources**

Read `../emu198x/README.md` and `../../docs/features/frontend.md`. From the latter, take only what a reader needs to launch a machine: that each system ships its own binary, that a launcher appears when no file is given, and how to skip it. Leave the design principles, the per-system behaviour tables and the unified-launcher proposal where they are.

- [ ] **Step 2: Write the page**

Four sections, in the plan's required order:

1. **What Emu198x is** — per-system binaries, not one launcher; a machine boots its own firmware or takes media. Name the thing that surprises people: there is no single `emu198x` command.
2. **What works today** — the fleet count from the registry, and where to see it (`/systems/`). Do not restate the list.
3. **Running a machine** — a real invocation for one machine, with the firmware path shown as an obvious placeholder, and the same command shown for a release archive as well as a source checkout.
4. **What you need that we cannot give you** — firmware and media. Link the rights position; do not restate it.

- [ ] **Step 3: Check the prose and build**

Run:
```bash
vale src/pages/docs/getting-started.astro
EMU198X_SOURCE_ROOT=../emu198x npm run build > /dev/null 2>&1 && echo built
```
Expected: no style findings, and a successful build.

- [ ] **Step 4: Commit**

```bash
git add src/pages/docs/getting-started.astro
git commit -m "docs: write a getting-started page for a reader arriving cold

The page existed but assumed its reader already knew the shape of the
project. The thing that surprises people is that there is no single
emu198x command — each machine ships its own binary — so that goes first
instead of being discovered from an error.

The launcher material comes from features/frontend.md, which is a design
document: 913 lines of launcher behaviour, design principles and a
unified-launcher proposal. What a reader needs from it is two paragraphs,
so that is what this takes."
```

---

### Task 3: MCP

**Files:**
- Create: `src/pages/docs/mcp.astro`

**Source material:** `emu198x/docs/features/mcp.md` — 620 lines.

- [ ] **Step 1: Read the source**

Read `../../docs/features/mcp.md`. Its opening already states the mental model well: the core stays hardware-specific, the MCP server is a thin control and inspection adapter, observability is path-based so tools can discover what a machine exposes. Keep that framing.

Note its two honest caveats — "Not all planned tools are implemented yet" around line 26, and the guidance at line 117 to prefer the path-based `query` where a tool is not implemented for a system. Both belong on the page.

- [ ] **Step 2: Write the page**

1. **What it is** — the three-point mental model above, in the source's own terms.
2. **What works today** — the core tools that are live across runnable packages.
3. **Driving a machine** — one worked example: boot, run frames, press a key, capture. Show the actual tool calls.
4. **What does not work yet** — save states, breakpoint conditions and the rest the source names, plus the `query` fallback for machines a tool has not reached.

- [ ] **Step 3: Check the prose and build**

Run:
```bash
vale src/pages/docs/mcp.astro
EMU198X_SOURCE_ROOT=../emu198x npm run build > /dev/null 2>&1 && test -f dist/docs/mcp/index.html && echo "route OK"
```
Expected: no style findings, `route OK`.

- [ ] **Step 4: Commit**

```bash
git add src/pages/docs/mcp.astro
git commit -m "docs: publish the MCP surface, with the tools that do not exist yet named

MCP is the reason to choose this emulator over a more accurate one, and it
has been documented only inside a repo the site never published.

The mental model comes over intact because the source states it well: the
core stays hardware-specific, the server is a thin control and inspection
adapter, and observability is path-based so a tool can discover what a
machine exposes instead of being told.

The unimplemented tools are named on the page. A capability list without
its gaps is the same failure as a status page without its evidence, and
the source document was already honest about this."
```

---

### Task 4: Scripting

**Files:**
- Create: `src/pages/docs/scripting.astro`

**Source material:** `emu198x/docs/features/scripting.md` — 354 lines.

- [ ] **Step 1: Read the source and the real interface**

Read `../../docs/features/scripting.md`. Then read a real script definition from the site's own data — `src/data/boot-screenshots.js` builds script JSON for the Spectrum variants — so the documented shape matches what the binaries accept.

- [ ] **Step 2: Write the page**

1. **What it is** — a JSON script of steps driving a machine headlessly, and why that exists: a run that can be repeated exactly is what makes a capture evidence and not an anecdote.
2. **What works today** — the step kinds available.
3. **Writing a script** — a complete, runnable example. Use a machine whose firmware a reader might have, and show the command that runs it.
4. **What does not work yet** — anything the source flags, and the known limit that an open-loop script cannot force a multi-event outcome; a script sets up a run, it does not react to one.

- [ ] **Step 3: Verify the example is real**

Run the documented command against a machine whose firmware is present, and confirm it writes a screenshot. Do not publish an example that has not run.

- [ ] **Step 4: Check the prose and build**

Run:
```bash
vale src/pages/docs/scripting.astro
EMU198X_SOURCE_ROOT=../emu198x npm run build > /dev/null 2>&1 && test -f dist/docs/scripting/index.html && echo "route OK"
```
Expected: no style findings, `route OK`.

- [ ] **Step 5: Commit**

```bash
git add src/pages/docs/scripting.astro
git commit -m "docs: publish the scripting surface, with an example that has been run

Scripting is what makes a capture repeatable, and repeatability is what
separates evidence from an anecdote — so it belongs next to the accuracy
page instead of inside a repo nobody outside the project reads.

The example on the page was run before it was published. An example that
has only been read is a claim, and this site has just finished removing
one set of those."
```

---

### Task 5: Capture

**Files:**
- Create: `src/pages/docs/capture.astro`

**Source material:** `emu198x/docs/features/capture.md` — 287 lines.

- [ ] **Step 1: Read the source**

Read `../../docs/features/capture.md`. It is the closest of the five to user documentation already — an overview, the current workflow, screenshots and video with their formats and options, and a programmatic path.

- [ ] **Step 2: Write the page**

1. **What it is** — screenshots and video out of a deterministic run.
2. **What works today** — the formats and options the source lists.
3. **Capturing** — a screenshot example and a video example, both runnable.
4. **What does not work yet** — whatever the source flags.

Include the resolved dithering note where it matters: video preserves dithering at the current settings, which was not always true.

- [ ] **Step 3: Check the prose and build**

Run:
```bash
vale src/pages/docs/capture.astro
EMU198X_SOURCE_ROOT=../emu198x npm run build > /dev/null 2>&1 && test -f dist/docs/capture/index.html && echo "route OK"
```
Expected: no style findings, `route OK`.

- [ ] **Step 4: Commit**

```bash
git add src/pages/docs/capture.astro
git commit -m "docs: publish the capture surface

Every screenshot on this site was made with it, including the synthetic
cartridge captures on the systems pages, so a reader who wonders how those
were produced can now find out and reproduce them."
```

---

### Task 6: Observability

**Files:**
- Create: `src/pages/docs/observability.astro`

**Source material:** `emu198x/docs/features/observability.md` — 326 lines.

- [ ] **Step 1: Read the source**

Read `../../docs/features/observability.md`. Note the caveat in its opening — something is "still planned" — and the "Planned, not implemented yet" list around line 116. Both belong on the page.

- [ ] **Step 2: Write the page**

1. **What it is** — path-based inspection of chip state, and why paths instead of a fixed API: a tool can discover what a machine exposes instead of being told per machine.
2. **What works today** — the paths available.
3. **Inspecting a machine** — a worked query and its output.
4. **What does not work yet** — the source's planned list, verbatim in substance.

- [ ] **Step 3: Check the prose and build**

Run:
```bash
vale src/pages/docs/observability.astro
EMU198X_SOURCE_ROOT=../emu198x npm run build > /dev/null 2>&1 && test -f dist/docs/observability/index.html && echo "route OK"
```
Expected: no style findings, `route OK`.

- [ ] **Step 4: Verify every sidebar link now resolves**

Run:
```bash
node -e "
const { readFileSync, existsSync } = require('node:fs');
const html = readFileSync('dist/docs/index.html', 'utf8');
const hrefs = [...new Set([...html.matchAll(/href=\"(\/[^\"#]*)\"/g)].map(m => m[1]))];
const bad = hrefs.filter(h => !existsSync('dist' + h.replace(/\/\$/, '') + '/index.html') && !existsSync('dist' + h));
console.log(bad.length ? 'DEAD: ' + bad.join(' ') : 'every docs link resolves');
process.exit(bad.length ? 1 : 0);
"
```
Expected: `every docs link resolves`

- [ ] **Step 5: Commit**

```bash
git add src/pages/docs/observability.astro
git commit -m "docs: publish the observability surface, and close the documentation set

Path-based inspection is the part of the automation surface that makes the
other parts useful: a tool can ask what a machine exposes instead of
carrying a table of what each one supports.

This completes the five, and every link in the sidebar now resolves — which
is the state the site was supposed to be in before the sync quietly stopped
copying files that had never existed."
```

---

### Task 7: The homepage

**Files:**
- Modify: `src/pages/index.astro`

- [ ] **Step 1: Choose the demonstration**

Pick one worked example that shows the spine in a single screen: a script or MCP session that boots a machine, drives it and writes a capture. Run it, and keep its real output.

The Spectrum is the strongest candidate — it has firmware present, the largest variant coverage, and it is the machine the family leads with elsewhere.

- [ ] **Step 2: Rewrite the hero**

Replace the three-claim lede. The claim is one sentence: thirty machines, driven from MCP or a script, deterministically, with the result captured.

Keep the evidence panel, but replace its hand-typed figures with the fleet count from `loadSiteData()` so the homepage cannot drift from the registry either.

- [ ] **Step 3: Show the run, do not describe it**

Below the hero, put the example from Step 1: the script on one side and the frame it produced on the other. The image is a capture the site already holds.

- [ ] **Step 4: Reorder the rest**

Sections in this order after the demonstration: what it runs (link to `/systems/`), how accurate it is (link to `/accuracy/`), how to get it (link to `/downloads/`). Cycle accuracy and public evidence become the support for the automation claim instead of competing headlines.

- [ ] **Step 5: Check contrast on the changed surfaces**

Run:
```bash
EMU198X_SOURCE_ROOT=../emu198x npm run build > /dev/null 2>&1 && npm run a11y
```
Expected: `0 defect(s)`

The homepage carries the ground tint and the accent-filled buttons, both of which have failed contrast before; the gate is the check that they still hold.

- [ ] **Step 6: Look at it in both themes**

Run: `npm run preview` and open the homepage in light and dark. Confirm the demonstration reads at a glance and the hero headline does not collide with the panel — it has overrun its column twice before.

- [ ] **Step 7: Check the prose**

Run: `vale src/pages/index.astro`
Expected: `0 errors, 0 warnings and 0 suggestions`

- [ ] **Step 8: Commit**

```bash
git add src/pages/index.astro
git commit -m "feat: lead with the automation surface instead of arguing three things

The homepage opened by claiming cycle accuracy, a deterministic automation
surface and public accuracy evidence at once. A page that argues three
things tends to land none of them, and the automation surface is the one
no other emulator offers.

So it makes one claim and shows it: a real script and the frame it
produced, instead of a paragraph asserting that this is possible. The two
other claims stay as its support — accuracy is the reason to trust the
output, and the evidence is how that is checked.

The fleet count comes from the registry, so the homepage cannot drift from
the machine list either."
```

---

## Self-Review

**Spec coverage.** The five curated pages → Tasks 2–6. The four-section shape with its non-optional fourth section → the Global Constraints and every page task. `frontend.md` excluded, its residue in Getting started → Global Constraints and Task 2. The `/docs/` index → Task 1. Homepage rewrite around the spine → Task 7. Nav rebuilt after Plan 1 left it short → Task 1.

**Type consistency.** `loadSiteData()` is consumed in Task 7 with the signature defined in Plan 1 Task 4. Route paths used in the nav (Task 1) match the files created in Tasks 2–6 exactly: `/docs/getting-started/`, `/docs/mcp/`, `/docs/scripting/`, `/docs/capture/`, `/docs/observability/`.

**Placeholder scan.** No TBDs. The page tasks specify the four sections, the source document and line references for the caveats that must survive, and the verification command per page. They do not contain the finished prose, because the prose is the deliverable of the task and writing it here would move the work instead of planning it — the constraint that makes it checkable is the four-section shape plus `vale` plus a route test, all of which are stated.

**One gap named here, not papered over.** Task 4 Step 3 and Task 7 Step 1 both require running a machine, which needs firmware the executor may not have. If it is absent, the honest move is to pick a different machine or a synthetic cartridge from Plan 2 — not to publish an unrun example. Both steps say so.
