# Sibling investigations: published components as general tools

**Date:** 2026-10-21

**Status:** Source reconnaissance and existing baseline checks completed below.
The isolated, registry-backed experiments are required follow-up work during
migration; none is claimed complete by these baseline tests.

Steve has included four investigations in the repository/publication programme:
Build198x artifact execution, Lang198x language analysis, Isa198x conformance and
Debug198x family-runtime consumption. Every outcome aims for best-in-class.
These are deliverables of the programme, not optional suggestions to discard
once source directories have moved.

Parent: [system-family repository plan](../2026-10-21-system-family-repositories.md).

## Quality and ambition

Best-in-class means useful standalone tools and supported capabilities that work
for valid inputs beyond the current lessons. Scope can grow in stages; correctness
within a supported capability is not limited to the first fixture. Each
investigation must identify a real user workflow, an independent reference where
one is available, adverse cases, reproducible evidence and a clear account of
what remains unsupported or unknown. A green build, self-round-trip or package
upload alone is not its success condition.

This follows umbrella `decisions/emu198x-best-in-class.md` and
`decisions/family-tools-are-general.md`, with the user's explicit best-in-class
direction applying to all four investigations. Published component boundaries
must preserve the existing master-clock, accuracy and source-of-truth rules.
No public best-in-class claim is established by this document.

## Lang198x direction

Lang198x is the home for language frontends, source analysis, dialect/release/
extension profiles and language services, including LSP. Highlighting is an
early delivery surface, not the project's endpoint. The current AMOS repository
already also has a source-preserving parser/checker for its documented opening
forms. Highlighting breadth and semantic coverage must be reported separately.

The programme should make room for richer parsing, names/scopes and diagnostics,
navigation, completion, safe transformations and editor services as their
language models are established. Native-file interoperability and eventual
compiler/interpreter capabilities deserve their own researched designs. This
direction does not commission a universal AST, replace original runtimes or
claim those capabilities already exist. AMOS and subsequent languages retain
their own models and release/extension evidence.

Boundaries remain explicit: Lang198x owns analysis/services; Format198x owns
historical file codecs; Build198x owns artifact/media construction; Asm198x owns
canonical assembly semantics; Emu198x owns machine execution; Debug198x owns
debug-info exchange. Forge may consume those services later under its existing
deferred status.

## Inspected source baselines

| Repository | Revision |
|---|---|
| `build198x/build198x` | `f7016398deb1fff9dc1efb6713dfab8c7bacf2d0` |
| `format198x/format198x` | `7436ad36a7df872ac2a9655edb01f1e7c3d95fa9` |
| `lang198x/amos` | `dcb73677d710ca4e59b99197f192febbae0fbe51` |
| `isa198x/isa198x` | `4bd1876b3e5572c2ce79b11f1db57a7c03ac6370` |
| `debug198x/debug198x` | `2585c6e97f6d1a47edc841c62f09d04a6d9f6702` |
| `emu198x/emu198x` | `f2a6213be7654a1d146cf8574772696f9f095ef9` |

The Lang198x ownership decision and initial migration inventory were read from
umbrella commit `dd9bdfa0cf272fb87763c15afa45f6b35e0978e2`, as linked by the
Lang198x agent context. They are not present in this umbrella working tree.
The current AMOS implementation/coverage takes precedence over that decision's
historical "implementation not started" status line.

Unrelated AMOS corpus/investigation documentation was committed separately during
this work (`b16ea7f622c97b2acd52a86e77cb0be54d63ad8a`). It was left untouched;
the parser, tests and manifests did not change from the inspected revision above.
This investigation changed no production code, dependencies, public APIs or
save-state counters.

## B1: Build198x artifact-to-execution validation

**Finding.** `crates/build198x/src/basic/mod.rs` already builds Spectrum TAP and
C64 PRG from text using published Format198x libraries. The BASIC CLI suite
decodes containers and checks lint/refusal behaviour; it does not execute the
resulting program in an original machine environment. Build198x's validation
decision already calls for emulator-backed pipeline checks.

**First experiment.** Use the existing Spectrum BASIC-to-TAP path and a published
Spectrum runtime library, without waiting for the Spectrum repository move.
This avoids inventing Dragon build support just to demonstrate the Dragon pilot.
Use an original small diagnostic with an observable RAM result, load it through
the declared normal machine/ROM path and check execution reached that result.
Record the chosen machine, firmware hash, package versions, features and lockfile.

**Acceptance.** A fresh isolated consumer builds the artifact with registry
packages and executes it through the family runtime. A changed expected RAM
result fails; malformed or deliberately changed program input cannot leave a
stale successful result. Retain artifact bytes/hash, actual execution result
and bounded commands. A rendered screen is supporting evidence, not a substitute
for the program assertion. Private firmware stays outside the public fixture.

**Ownership.** Build198x owns artifact construction and its integration check;
Format198x owns codecs; Emu198x owns runtime behaviour. Start with verification,
not a new Build CLI verb. Any diagnostic/machine defect discovered is fixed as a
separate bounded issue before claiming the workflow passes.

## L1: Lang198x analysis extraction and semantic growth

**Finding.** There are concrete implementation seams to review:

- Format198x `crates/format198x-sinclair-zx-spectrum-bas/src/ast.rs`,
  `parser.rs` and public `parse()` expose Spectrum language analysis alongside
  storage encoding. The separate `tokenise_listing()` path is what Build uses.
- Build198x `crates/build198x/src/basic/lint.rs` exposes `check`, `fix` and located
  findings. Its listing-form rules include curriculum policy as well as
  language-specific hazards; moving the whole module unchanged would confuse
  valid-language semantics with preferred listing presentation.
- Lang198x AMOS `src/lib.rs` exposes original source, complete tokens/trivia,
  typed statements, ranges, recovery diagnostics and profile-aware checks. Its
  coverage is intentionally narrower than its highlighting vocabulary. This is
  a useful model of explicit supported/unsupported/unknown results, not a shared
  AST to impose on Spectrum or C64.

**First deliverable.** A reviewed extraction design identifying the Spectrum
AST/parser API, existing published callers, diagnostic semantics, source-location
gaps and adapter strategy. Classify each BASIC lint rule as language analysis,
codec/listing behaviour, build policy or teaching policy. Identify a first bounded
semantic service useful through both library/CLI and an eventual editor adapter.
Continue AMOS expansion independently; it does not wait for Spectrum migration.

**Acceptance.** List current failure modes before choosing adaptation or
replacement. Preserve Format198x's published tokenisation API and native byte
contracts through an explicit compatibility design; preserve Build's rule IDs,
locations, fixes and refusal behaviour. Test valid, invalid, unsupported and
unknown-profile inputs, plus positions/recovery beyond the existing examples.
No dependency cycle, second editor-only parser or inference of native execution
from host parsing. Define original-runtime comparisons for named profiles.

**Next investigation surfaces.** Broader AMOS expressions/statements, symbols
and scopes, release/extension resolution, diagnostics and source-preserving editor
operations. Prioritise them from documented language evidence and actual users;
choose individual milestones with measured coverage. Native AMOS codecs belong
to Format198x; native execution evidence belongs to Emu198x. A highlighting
release cannot stand in for completion of these capabilities.

## I1: Isa198x conformance using published CPU cores

**Finding.** Emu's Z80 already has
`crates/emu198x-zilog-z80/tests/isa_conformance.rs`, comparing its handwritten
disassembler with `isa198x-disasm`. It compares rendered text and instruction
length on their shared surface, asserts a positive comparison count and fails
on mismatches. It is not an execution or timing test. CPU crates need not move
into Isa198x to improve it.

**First experiment.** Reproduce that decoder cross-check in an isolated consumer
of the published Z80 and Isa198x packages. Audit whether each packaged crate
actually includes the required APIs/fixtures. Reconcile all generated cases into
compared, unsupported and missing outcomes, then choose a documented instruction
subset for execution observations through the CPU's existing pin interface.

**Acceptance.** Preserve exact package versions/features and a nonzero case
inventory. A deliberately wrong length/text expectation fails. For the execution
subset, observe resulting registers/memory/PC and relevant bus transactions;
derive expectations from primary/reference cases, not another path through the
same implementation. Unsupported encodings stay visible. Do not turn decoder
agreement into a cycle-accuracy or whole-ISA claim.

**Ownership.** CPU execution stays in Emu198x, executable ISA truth in Isa198x.
Keep cross-project execution tooling in an integration/conformance surface;
Isa198x's production crates retain their dependency constraints. The current
decision against per-CPU Isa crates remains until its own trigger fires.

## D1: Debug198x through an independently published family runtime

**Finding.** The published Debug198x contract already carries sections, source
lines, symbols and address spaces. Emu's
`crates/emu198x-shell/src/debug_info.rs` tests real sidecars, line/address lookups,
paging, relocation, ambiguous names, unknown records and malformed inputs.
Dragon's runtime already exposes debug primitives, but these importer tests do
not prove a breakpoint in a separately packaged runtime stops at the right source
instruction.

**First experiment.** Use a small Asm198x program and its actual `.debug198x`
sidecar with the published Dragon runtime/shell dependency graph. Load the
program, resolve a source-line breakpoint, execute and inspect the stopped PC,
symbol and machine state. Check package contents before assuming existing test
fixtures or source files are distributed. Preserve the frozen wire format.

**Acceptance.** Actual runtime stop agrees with the sidecar's source/address
mapping. A wrong mapping or expected PC fails; malformed/version-mismatched
sidecars fail clearly; a missing mapping cannot silently select another line.
Use paging/relocation cases from other families as follow-ups rather than
claiming Dragon validates them. Verify the isolated registry graph and record
writer/reader versions. No format revision is justified by extraction alone.

**Lang198x opportunity.** Future native language producers should assess this
contract for source maps. A compiler with real placement can emit mappings;
interpreted source needs a genuine source/token/runtime-location bridge. Do not
invent machine addresses from syntax highlighting or AST source spans.

## Executed baseline checks

Commands ran in the named source repositories with locked dependencies and no
network resolution. They exercise existing behaviour; they do not establish
the pending isolated integrations or original AMOS compatibility.

| Repository | Command | Observed result |
|---|---|---|
| Build198x | `cargo test --locked --offline -p build198x --test basic_cli` | 15 passed, 0 failed/ignored. Includes malformed input and nonzero/refusal checks. |
| Lang198x AMOS | `cargo test --locked --offline` | 14 integration tests passed, 0 failed/ignored; unit/doc targets had no tests. Includes unknown-profile, unsupported-form and source-position checks. |
| Emu198x Z80 | `cargo test --locked --offline -p emu198x-zilog-z80 --test isa_conformance -- --nocapture` | 1 test passed; 705 opcode comparisons, 708 reported skipped because Isa rendered data. Other early-return paths need reconciliation before asserting total coverage. |
| Debug198x | `cargo test --locked --offline -p debug198x` | 14 unit tests and 1 doctest passed, 0 failed/ignored. |
| Emu198x shell | `cargo test --locked --offline -p emu198x-shell --lib debug_info::tests` | 32 selected tests passed, 0 failed/ignored; 254 outside the selected scope. Includes malformed/version input and ambiguous/unmapped lookup checks. |

The Z80 test also ran once without `--nocapture`; it was rerun specifically to
read its comparison/skip counts. Existing expected error messages in the AMOS
CLI tests are passing negative controls, not failed commands. No full emulator
or all-sibling test pass is claimed. All task-started cargo processes completed.
Build output used normal workspace target directories; no temporary worktree or
custom build directory was created.

## Scheduling and closure

Keep B1, L1, I1 and D1 as four named migration work items, with their own evidence
and owning repositories. L1's source/design review can start now; registry
experiments follow publication of their exact dependency closures. B1 need not
block Dragon cutover merely because it uses Spectrum. D1 is a direct pilot
consumer check. Findings can create smaller bug fixes or capability designs;
do not hide those inside repository moves.

Each investigation closes with a source-backed recommendation, the outcome of
its specified experiment/design, retained commands and results, and explicit
remaining work. Where publication prerequisites prevent the experiment, keep it
open. The overall programme includes all four outcomes; baseline tests alone do
not close them.
