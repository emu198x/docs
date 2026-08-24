# Design: rebuild emu198x.github.io around the automation surface

**Date:** 2026-08-24
**Status:** Approved, not yet implemented
**Repo affected:** `emu198x/emu198x.github.io`
**Reads from:** `emu198x/emu198x` (`docs/status/`, `CHANGELOG.md`)

## Why

The site has five nav links that 404 on production: `/docs/features/mcp/`,
`/docs/features/scripting/`, `/docs/features/capture/`,
`/docs/features/observability/` and `/docs/systems/`.

`scripts/sync-public-docs.mjs` copies those paths out of `emu198x/emu198x`.
They have never existed there — the feature documents live in `emu198x/docs`
at different paths, and the workflow does not check that repo out. The sync
skips a missing file without complaining, so CI builds eight pages, reports
success, and publishes a nav pointing at nothing. The links have been dead
long enough that nobody noticed, which is the same failure `#825` was filed
about one repo over.

Two further problems surfaced while diagnosing that one.

**The accuracy page contradicts a binding decision.** `evidence-is-what-ran-not-what-was-claimed.md`
(ACTIVE, 2026-08-18) governs anything reporting per-machine maturity and rules
that a status page "states claims and evidence side by side, and never lets a
claim stand in for evidence". The page is 265 lines of hand-typed data inside
`src/pages/accuracy/index.astro`: 28 machines, hand-typed progress percentages,
hand-typed status pills. It has already drifted — the registry has 30 machines.

**The site is a fifth naming vocabulary.** The registry exists because one
machine is a crate, a `machine_id`, an issue label and a milestone at once, and
those agree only by convention. The site adds a fifth: its 28 capture ids, nine
of which differ from the registry (`zx-spectrum` against `sinclair-zx-spectrum`,
`nes` against `nintendo-nes`, `dragon-32` against `dragon`, `oric-atmos` against
`oric`, `msx1` against `microsoft-msx1`, `colecovision` against
`coleco-colecovision`, `game-boy` against `nintendo-game-boy`, `zx80`/`zx81`
against `sinclair-zx80`/`sinclair-zx81`).

## Decisions taken before this design

| Question | Decision |
|---|---|
| Where curated docs live | The site repo. `emu198x/docs` stays internal and is never published. |
| The site's spine | The automation surface — MCP, scripting, deterministic capture. |
| Scope | Full information-architecture rebuild. |
| Per-machine pages | Yes, one per registry machine. |
| Hand-typed percentages | Deleted. No honest source exists for them. |

## Binding constraints

- `emu198x/knowledge/decisions/evidence-is-what-ran-not-what-was-claimed.md` —
  claims and evidence side by side; a claim never stands in for evidence. The
  registry states joins instead of inferring them.
- `198x/decisions/family-visual-identity.md` — the plate, the palette, the type
  roster, project colour confined to a plate cell and the §3b ground tint.
- `198x/decisions/sibling-cross-promotion.md` — the footer family strip's
  wording and peer framing.
- `198x/decisions/publishing-third-party-imagery.md` — the standing rights
  notice on every surface carrying imagery, and the per-capture note.

## Data flow

The site stops syncing prose. `scripts/sync-public-docs.mjs` is deleted.

CI already checks the flagship out at `emu198x-source`. The build reads exactly
two files from it:

| File | Gives |
|---|---|
| `docs/status/systems.toml` | the machine registry: 30 entries of `machine_id`, `crate`, `label`, `milestone` |
| `docs/status/current-system-usability.md` | per-machine evidence: own-crate count, shared-crate count, issue link, milestone link |

`CHANGELOG.md` keeps its existing working sync for `/docs/changelog/`.

Everything else on the site is authored in the site repo.

**A missing checkout fails the build.** The current sync's silence is what
published a broken nav; the replacement states the problem and stops. The error
names the environment variable and the path it looked in.

### What the evidence layer can honestly say

The flagship publishes no test counts, on purpose: "They would be stale within a
day, and a page that is usually wrong trains people to stop reading it." So the
per-machine facts available are the crate counts, the issue and milestone links,
and — from the site's own captures — whether a machine has been seen to boot.

That is the whole of it. There is no source for a percentage, which is why the
existing ones are deleted instead of re-derived.

## The join

Every capture entry in `src/data/boot-screenshots.js` gains an explicit
`machineId` naming its registry entry. Nothing pattern-matches.

A build-time check enforces three things:

1. Every `machineId` on a capture exists in the registry. An unknown id fails
   the build.
2. No two captures of the same kind claim the same `machineId`.
3. Machines with no capture are collected and rendered as "no capture yet",
   not omitted. Today those are `amstrad-cpc` and `sega-game-gear`.

Point 3 is the reason the registry drives the list. A page built from the
captures can only ever show what it already has, which is how 28 came to look
like the whole fleet.

## Information architecture

| Route | Source | Note |
|---|---|---|
| `/` | authored | Automation spine |
| `/systems/` | registry + captures | All 30, including the two with no capture |
| `/systems/<machine-id>/` | registry + captures + evidence | 30 pages, keyed by `machine_id` |
| `/accuracy/` | flagship evidence | No percentages, no status pills |
| `/downloads/` | authored | Content unchanged; re-themed with the rest |
| `/docs/` | authored | Index |
| `/docs/getting-started/` | authored | |
| `/docs/mcp/` | authored | |
| `/docs/scripting/` | authored | |
| `/docs/capture/` | authored | |
| `/docs/observability/` | authored | |
| `/docs/changelog/` | flagship `CHANGELOG.md` | Existing sync retained |

Per-machine URLs use `machine_id` verbatim, so the site's public vocabulary and
the registry's are the same string. This is the one place to stop the fifth
vocabulary spreading.

### Removed

- `/docs/features/{mcp,scripting,capture,observability}/` — never existed.
- `/docs/systems/` — never existed.
- The hand-typed accuracy dataset, 265 lines.
- `scripts/sync-public-docs.mjs`.

### Redirects

`/docs/status/current-system-usability/` is live today and its content moves
into `/accuracy/`. It redirects there. The five dead routes get no redirect;
they have never resolved, so there is nothing to preserve.

## The documentation set

Five curated feature pages, plus the `/docs/` index that lists them, written
down from roughly 2,500 lines in
`emu198x/docs/features/`. Each answers, in this order:

1. What this is, and the mental model needed to use it.
2. What works today.
3. How to use it, with a runnable example.
4. What does not work yet.

Section 4 is not optional. The source documents already carry honest caveats
("Not all planned tools are implemented yet"), and that tone matches the
accuracy page. Publishing capability without its limits is what the evidence
decision objects to in a different form.

**`features/frontend.md` is not published.** Its 913 lines are launcher design
— `## Optional: Unified Launcher`, `### Design Principles`, per-system
behaviour tables. It is a design document. Whatever a reader needs from it
becomes a short section of Getting started about launching a machine.

Curation is authorship. These pages are rewritten for a reader arriving cold,
not copied with the internal framing left in.

## Homepage

Leads with the automation surface: any of thirty machines, driven from MCP or a
script, deterministically, with the result captured.

It shows a real script and its actual output instead of describing that this
is possible. The evidence and systems sections follow, then the download.

The three-way claim the current homepage opens with — cycle accuracy, automation
surface, public evidence — collapses to one claim with the other two as its
support.

## Error handling

| Condition | Behaviour |
|---|---|
| Flagship checkout absent | Build fails, naming the variable and the path |
| `machineId` not in the registry | Build fails, naming the capture |
| Registry machine with no capture | Rendered as "no capture yet" |
| Evidence file unparseable | Build fails; a silently empty table is the failure being designed out |

Every one of these is a hard failure by choice. The bug this rebuild exists to
fix was a skipped step that reported success.

## Testing

- The a11y sweep already gates the deploy; it covers every new route in both
  themes and must stay at zero serious or critical defects.
- The registry join check runs in the build, so a capture naming an unknown
  machine cannot ship.
- The rendered-spacing check stays.
- A route check compares the built route set against the current live set, so a
  page cannot silently disappear the way the docs pages silently never appeared.

## Out of scope

- Moving `emu198x/docs/features/` into the flagship repo. Considered and set
  aside; revisit if the docs start drifting from the code.
- Publishing a per-machine maturity figure. That is a change to the flagship's
  evidence decision, not a site change.
- Search. Asm198x has it over a large generated book; five authored pages do
  not need it yet.
- `/systems/` visual redesign beyond what the registry-driven list requires.

## Risks

**The site's content is no longer entirely in the site's hands.** A change to
`systems.toml` changes the site. That is the intent — it is what stops the
drift — but it means a flagship edit can break a site build. The join check and
the hard failures are there so it breaks loudly and at build time.

**Thirty per-machine pages start thin.** Each has a capture, two crate counts
and two links. They earn their place through deep links and search results; if
they still look thin after the rebuild, they can be folded back into the index
without changing anything upstream.
