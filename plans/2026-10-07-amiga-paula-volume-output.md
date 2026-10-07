# Establish Paula volume output timing

Continue the approved Amiga accuracy campaign locally; pushing stays deferred.
The completed active-target sweep checked the volume register, not the gain
at the DAC. This investigation must distinguish scalar approximations from
the hardware's documented 64-step volume duty cycle.

1. Inspect the HRM AUDxVOL definition and audio state-machine glossary, pinned
   WinUAE scalar/PWM paths, vAmiga volume reloads, and Minimig's live PWM route.
   Record disagreement rather than selecting a convenient latch model.
2. Add `test-data/commodore/amiga/paula-audio/volume-output-probe/` with a
   reproducible runner and Verilog testbench. Compile the unchanged pinned
   Minimig channel with the installed Icarus Verilog. Exercise all 128 volume
   encodings and writes at all 64 counter phases. Extract WinUAE's unchanged
   PWM stepping kernel separately; explicitly delimit the omitted scheduler,
   startup and filter behavior. Check sample gating and whole-cycle duty,
   exact inventory, and rejection of empty/corrupted output.
3. Record evidence in
   `reference/by-system/commodore-amiga/2026-paula-volume-output-observations.md`
   through the isolated reference worktree, then cite it from the existing
   Paula decision. Keep physical-hardware evidence distinct from reference
   implementations and synthetic counter alignment.
4. Choose the next bounded correction only after assessing counter phase and
   downstream resampling. Do not add a byte/word gain latch merely because a
   scalar reference uses one. A new saved PWM stage needs a concrete design
   and schema agreement before implementation. Commit the verified research
   locally; do not change production behavior on unresolved phase evidence.

## Findings and verified scope

The compiled probe covers 576 scenarios and 36,864 observations per reference.
All 128 volume encodings satisfy the HRM duty invariant. Seven write values
at every phase cover 448 dynamic windows, including unchanged-volume controls.
The WinUAE kernel is explicitly seeded to the RTL's initial counter; its
startup, scheduler and FIR are excluded. Under this synthetic alignment,
the gate differs in 19,530 rows. Integrated dynamic output differs from the
scalar comparator in 375 RTL and 378 WinUAE windows.

The actual native mixer diagnostic completes the same 36,864 observations,
then exits 1 with 26,464 instantaneous mismatches and
`native scalar output differs from PWM reference`. This is an intentionally
failing research diagnostic, not a new mandatory regression. The RTL phase
is not asserted as hardware truth. Empty/corrupted reference outputs fail
the checker; a second generation reproduces all four artifacts byte-for-byte.

Source inspection also establishes that the runtime point-samples the mixer
at 48 kHz before applying its analogue-filter approximation. A standalone
PWM counter would risk aliasing. A byte/word gain-latch fix would simply
choose between disagreeing scalar approximations. The next bounded work is
physical phase/reload evidence and a pre-decimation resampling comparison,
before proposing saved counter/filter stages. Snapshot version 60 and all
production behavior remain unchanged. The misleading steady-gain test
comment has been corrected to describe its limited scalar coverage.

Verification: the 16 existing audio tests pass, strict release Clippy passes
for all Paula targets, and Rust formatting plus Ruff check/format pass.
`validation.json` preserves the expected failing native diagnostic verbatim.
No broad machine rebuild is claimed for this research-only change.
