# Emu198x docs

This repo is the current documentation and status surface for Emu198x. It complements the emulator source repo at [`../emu198x/`](../emu198x/) and the public site repo at [`../emu198x.github.io/`](../emu198x.github.io/).

## Start here

| Need | Read |
|---|---|
| Current system boot/usability status | [`status/current-system-usability.md`](status/current-system-usability.md) |
| Current cross-system remaining work | [`status/outstanding-work.md`](status/outstanding-work.md) |
| Status overview | [`status.md`](status.md) |
| Architecture overview | [`architecture.md`](architecture.md) |
| Adding a system | [`adding-a-system.md`](adding-a-system.md) |
| Testing policy/audit | [`testing-policy.md`](testing-policy.md), [`testing-audit.md`](testing-audit.md) |
| Feature docs | [`features/`](features/) |
| System docs | [`systems/`](systems/) |

## Historical and planning material

The following folders preserve useful context, but their status claims are not automatically current:

- [`plans/`](plans/) — plans and implementation programmes.
- [`archive/`](archive/) — archived docs.
- [`brainstorms/`](brainstorms/) — exploratory notes.
- [`handoffs/`](handoffs/) — handoff logs and investigation notes.
- [`ideation/`](ideation/) — strategy and stress-test material.

When these disagree with files under `status/`, prefer `status/`.

## Reference material

This repo also contains substantial technical reference material, including the Amiga reference set (`amiga-*.md`) and Spectrum variant notes (`SPECTRUM-VARIANTS.md`). Treat derived references as implementation guidance; new uncited hardware facts should start in the umbrella `reference/` layer, then flow through `syntheses/` and emulator distillation as appropriate.

## Screenshots and rights

Some documents here carry screenshots taken while developing and verifying the emulator, including side-by-side comparisons against reference emulators. Those captures are ours, but what they show often is not: system firmware, Workbench and other bundled software remain the property of their respective owners, as do any other emulators appearing in frame. They are reproduced here to demonstrate and diagnose emulator behaviour, and nothing in them is claimed as our work.

Where a document embeds such a capture, the surrounding text names what is on screen. This repo does not distribute ROMs, disks, tapes or cartridges. Anything a rights-holder would prefer removed comes down on request.

See [`198x/decisions/publishing-third-party-imagery.md`](https://github.com/stevehill1981/198x) for the family-wide rules this follows.

## Agent context

Agents should read [`CLAUDE.md`](CLAUDE.md) before editing this repo. `AGENTS.md` is a symlink to the same file.

## Citations to the primary reference library

Paths written as `reference/by-system/...` refer to the project's **primary
source library** — the manuals, datasheets, magazines and service documentation
that hardware facts here are distilled from.

That library is **not public, and will not be made public.** It holds
third-party material the project may hold for reference but may not
redistribute: manufacturer documentation, book and magazine scans, and mirrored
community sites. Keeping it private is what makes holding it legitimate.

These citations are therefore **provenance records, not links.** They name which
document a fact came from so the claim is traceable and auditable, and so a
reader can seek out the same source independently. The facts themselves are
freely reusable — facts are not copyrightable, and this repository is openly
licensed.
