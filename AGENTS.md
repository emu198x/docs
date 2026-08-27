# Emu198x docs

This repo owns Emu198x documentation and current status summaries. It sits inside the `Emu198x/` org container alongside the emulator source repo (`../emu198x/`) and public site repo (`../emu198x.github.io/`).

## Read first

- [`README.md`](README.md) — docs repo front door and reading routes.
- [`status.md`](status.md) — current status router.
- [`status/current-system-usability.md`](status/current-system-usability.md) — current boot/usability status by system.
- [`status/outstanding-work.md`](status/outstanding-work.md) — current cross-system remaining work.
- [`../emu198x/CLAUDE.md`](../emu198x/CLAUDE.md) and [`../emu198x/RULES.md`](../emu198x/RULES.md) — emulator source rules before code changes.

## Current-state rule

Keep front-door docs focused on current operational truth. Historical reasoning belongs in `plans/`, `archive/`, `brainstorms/`, `handoffs/`, or project decision records. If a plan/archive/handoff conflicts with `status/` or the emulator source, treat the plan/archive/handoff as historical context.

## Ownership

- Commit docs/status changes in this repo: `Emu198x/docs/`.
- Commit emulator code and codebase-tied hardware distillation in `Emu198x/emu198x/`.
- Commit public website changes in `Emu198x/emu198x.github.io/`.
- Keep local ROM/media files in `Emu198x/roms/` out of commits unless a dedicated repo/policy is created.
