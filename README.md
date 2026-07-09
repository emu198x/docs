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

## Agent context

Agents should read [`CLAUDE.md`](CLAUDE.md) before editing this repo. `AGENTS.md` is a symlink to the same file.
