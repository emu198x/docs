# Testing policy

The verification standard for Emu198x: what a contributor runs before opening a
PR, what counts as proof that a component is correct, and the mechanisms that
stop a test reporting a pass it never earned.

Accuracy is the project's whole claim, so tests carry more weight here than they
would in most workspaces. That cuts both ways — a test that silently stops
running does more damage than one that was never written, because the green tick
goes on being read as evidence.

Paths in `backticks` are in the [`emu198x/emu198x`](https://github.com/emu198x/emu198x)
repository. For current support state see [status.md](status.md); for the
crate-by-crate audit against this policy see [testing-audit.md](testing-audit.md).

## Before you open a PR

Four commands, in the order CI runs them:

```bash
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo test --workspace --doc
```

Clippy must pass clean. The workspace denies `unwrap_used`, `dbg_macro` and
`todo`, and forbids `unsafe_code` outright.

`cargo test --workspace` passes on a clean tree with no ROMs. Tests that need
media you do not have skip rather than fail, and each test file's prologue names
the environment variable gating it (`EMU198X_SPECTRUM_MANIC_MINER_TZX`,
`EMU198X_GB_BLARGG_ROOT`, and so on).

If you have the wider 198x tree checked out, most external corpora are already
on disk — Tom Harte's under `assets/test-suites/`, FUSE's inside the vendored
emulator tree. Nothing points the environment at them by default, so suites skip
on machines that have had the data all along. Fix that in one line:

```bash
eval "$(scripts/check-fixtures.sh --export)"
```

Run it without `--export` to see which corpora resolve and which variable each
one wants. Staging what you can is worth the minute it costs: a change to a CPU
core is not really tested until the conformance suites have seen it.

## Core principles

- Tests are spec-driven, not coverage-driven.
- Every behaviour under test has a clear source, an observable outcome, or both.
- Component tests come before machine tests wherever behaviour can be isolated.
- Fast deterministic tests form the default development loop.
- Slow ROM suites and differential checks confirm; they are not the first line
  of defence.
- A bug fix strengthens or adds a regression test in the same change.
- A crate is not `Complete` unless it meets the expectations below or documents
  the remaining gap explicitly.

## Evidence hierarchy

Use reference material in this order:

1. Vendor manuals, hardware reference manuals, and original technical
   documentation.
2. Measured behaviour, logic-analyser captures, and authoritative test programs
   or ROM suites.
3. Project-local fixtures, engineering notes, and generated reference data.
4. Mature external emulators as secondary oracles, where the primary sources are
   incomplete or ambiguous.

The primary prose library in the 198x tree is the first place to look; the
emulator's own `knowledge/` tree is a codebase-tied distillation that cites it
rather than replacing it. When two sources disagree, record the chosen
interpretation in the test or in a short linked engineering note.

External emulator behaviour is not primary truth unless the hardware behaviour
is otherwise undocumented. Where a comparison against a reference emulator
settles a timing question, that reference is a prerequisite rather than a
nicety — `RULES.md` § Reference emulators is binding on this point.

## The verification ladder

Every reusable component moves through the same ladder. A change is expected to
add evidence at the rung it actually touches.

### 1. Contract tests

The basic external contract: reset state, register map, read and write masks,
address decode windows, unmapped behaviour, documented side effects.

### 2. Functional tests

The component's main behaviour in isolation: instruction semantics for CPUs,
pixel generation for video chips, waveform and mixer behaviour for audio chips,
DMA and arbitration decisions, parse and serialise behaviour for format crates.

### 3. Timing tests

Cycle, tick, or phase-accurate behaviour where timing matters: interrupt timing,
DMA slot timing, bus contention, raster and beam counters, audio period
behaviour, peripheral handshakes.

### 4. Integration confirmation

That the machine wiring matches the component contract: machine-level register
visibility, cross-chip interactions, boot-path checks for the subsystem, and one
or two representative end-to-end scenarios per major feature. This rung catches
the class of bug where every part is right and the assembly is not.

### 5. Reference programs and differential checks

The slower confirmation layers: diagnostic ROMs, conformance programs,
cross-checks against measured fixtures, differential traces against trusted
implementations. They support the component tests; they do not replace them.

Beyond that sit the system-level checks — screenshots, audio captures,
`--script` runs and MCP probes — for behaviour that only appears with the whole
machine assembled.

## Minimum expectations by crate type

- **CPU** — instruction semantics, flags, exceptions, interrupts and timing,
  covered by single-step or equivalent authoritative suites.
- **Chip** — reset state, register behaviour, masks, side effects, interrupts,
  DMA or arbitration, timing invariants, and output behaviour, in isolation.
- **Peripheral** — protocol handling, register or port behaviour, error paths,
  and handshake timing, in isolation.
- **Format** — parse success cases, round-trip where applicable, rejection of
  corrupt and truncated input, and checksum or structural validation where the
  format defines it.
- **Machine** — wiring tests, representative boot or smoke tests, cross-component
  timing checks, and per-model configuration checks.
- **Runnable `emu198x-*`** — CLI and host API behaviour, media loading, scripting
  and MCP entry points, and headed-versus-headless parity where both exist.
- **Transitional stubs** — narrowly scoped contract tests proving the exact
  behaviour relied on today, with the missing behaviour documented explicitly.

## Status gates

Applied to a component crate, the labels mean:

- **Not started** — no meaningful isolated behaviour implemented or verified.
- **Stub** — only the minimum needed to unblock another path; tests cover that
  narrow contract.
- **In progress** — major behaviour exists, one or more required test categories
  still missing.
- **Complete** — meets the relevant expectations above, with any remaining
  limitation documented.

`Complete` does not mean "boots one thing" or "seems to work in the machine".

## Coverage is an audit signal, not the gate

Line coverage tells you where nobody looked. It does not tell you whether what
ran was checked, and a workspace can reach a high number while asserting very
little. Treat it as a map of unvisited ground:

- Read the total as a directional signal, never as a quality gate on its own.
- Use the HTML and JSON output to find gaps worth auditing.
- Treat thin coverage in machine wrappers and runtime crates as a prompt to add
  isolated tests, not as a status to explain away.

`scripts/coverage.sh` produces the reports locally. Coverage was taken off the
per-PR critical path on 2026-08-13 for costing around five minutes on every run;
it is an audit you invoke, not a gate you wait on.

The one place it is enforced is the Spectrum family, where
`scripts/coverage-gate.sh` fails if an in-scope crate drops below its threshold.
That gate exists because those crates carry a shipping deadline, not because the
number is the standard.

## A skip is not a pass

`libtest` prints `ok` for a test that returned early. Nothing in the output
distinguishes it from a test that ran.

This is not a theoretical concern. The Dragon golden-frame test compared encoded
PNG bytes rather than pixels and broke when a dependency changed its deflate
settings. CI reported it `ok` for nearly three months, because CI has no Dragon
ROM and the test returned before it got that far.

So a test that cannot find its fixture declares the fact:

```rust
let Some(session) = booted_dragon_session() else {
    emu198x_test_skip::skip!("Dragon 32 ROM not staged (EMU198X_DRAGON32_ROM)");
};
```

The macro counts the skip, and — when `EMU198X_STRICT_FIXTURES` is set — panics
instead. That variable is set anywhere the fixture is supposed to be present:
the nightly accuracy run, and your own machine once you have staged the corpora.
A test that quietly stopped running then fails on the day it stops.

`scripts/check-fixture-guards.py` runs in CI and rejects a bare early return in
a fixture guard, so the pattern cannot return by being copied.

## Say which kind of `#[ignore]`

`#[ignore]` means five different things in this workspace, and a batch
`--ignored` sweep renders all of them as one red bar. The reason string must
start with the kind:

| Prefix | Meaning |
|---|---|
| `FIXTURE` | Needs data that is not in the repo. Passes in the nightly once the corpus is staged. |
| `DIAGNOSTIC` | A hand-run investigation tool. Not part of anyone's pass/fail reading. |
| `SLOW` | Passes; too expensive to run per-PR. |
| `KNOWN DIVERGENCE` | Deliberately red, expected to fail everywhere. |
| `KNOWN LIMITATION` | Deliberately red, expected to fail everywhere. |

Both `KNOWN` forms also carry an anchor — a `#NNN` issue or a
`knowledge/decisions/*.md` path — because their whole purpose is that somebody
comes back to them. `scripts/check-ignore-reasons.py` enforces all of this.

Without the prefix you cannot separate a regression from an unset environment
variable without opening every test, which is how a real failure sat unread in a
crowd of expected ones for two weeks.

## Execution tiers

- **Fast** — the default local loop: unit, contract, small timing and parser
  tests. Cheap enough to run while changing the crate they cover.
- **Per-PR** — everything above plus format, clippy, the cross-platform build,
  the hygiene checks, and the redistributable-firmware boot set.
- **Nightly** — the external conformance corpora, full boot matrices and larger
  media sweeps.

## External corpora run nightly

The CPU conformance corpora are too large and too licence-encumbered to check
in, so their tests are `#[ignore]`d by default and the `nightly-accuracy`
workflow runs them against a provisioned mirror: SingleStepTests (6502, Z80,
68000), Klaus Dormann, FUSE, Wolfgang Lorenz, ZEXDOC/ZEXALL and SM83.

`test-data/accuracy-corpora.md` is the single source of truth for that set — one
row per corpus giving the crate and test file, the environment variable, the
upstream source and the licence. Add a corpus there first;
`scripts/check-fixtures.sh` and the workflow read the same contract.

A completed nightly run records only the comparison it executed. The workflow's
existence establishes nothing on its own, which is why every job provisions its
fixtures in an explicit step and runs with `EMU198X_STRICT_FIXTURES` set.

## Fixture and reference data rules

- Keep fast tests self-contained where you can.
- Put reusable binary fixtures under crate-local `tests/data/`.
- Where a fixture is generated or transformed, document the generation steps or
  provenance next to it.
- Where redistribution is restricted, keep a checksum, an acquisition note and
  any conversion script rather than committing an unclear blob.
- Where a test depends on an external program or ROM suite, state that
  dependency in the test module prologue.

## What CI will judge your PR on

Beyond format, clippy, the cross-platform build and the test suite:

- **Test hygiene** — the fixture-guard, `#[ignore]`-reason, doc-link, workflow
  `apt`-pinning and `--help` checks. Each runs `--self-test` first, because a
  checker that has stopped detecting fails silently in exactly the way it exists
  to prevent.
- **System registry** — `scripts/status/check_registry.py`, and
  `scripts/status/render_status.py --check` to confirm the in-repo status pages
  still match the workspace.
- **Synthetic cartridges** — the committed test cartridges are rebuilt from
  source and compared.
- **Firmware boot evidence** — the redistributable-firmware boot set: the
  Spectrum variants to their prompts, C-BIOS on MSX, Open ROMs on C64.
- **Evidence ledger** — the test job records what actually executed and uploads
  it, so a green tick is not the only thing the run produces.

## Change policy

- A new reusable crate lands with contract tests at minimum.
- New externally visible behaviour lands with isolated tests for that behaviour.
- A regression fix includes a regression test, or a documented reason why one is
  not practical.
- Put a test at the lowest rung of the ladder that can prove the thing. Reaching
  for a full-machine screenshot to prove a register edge makes the failure
  harder to read and slower to run.
- Where a test needs an external corpus, add its row to
  `test-data/accuracy-corpora.md` in the same change.

## Per-crate verification matrix

Each crate should have an auditable record of what it claims. The format is not
fixed, but the information needs to exist in a reviewable form:

- the observable behaviour being claimed;
- the reference source or fixture backing that claim;
- the test file covering it;
- whether the coverage is contract, functional, timing or integration;
- any known gap or intentionally stubbed behaviour.

The current first-pass audit against this policy lives in
[testing-audit.md](testing-audit.md).
