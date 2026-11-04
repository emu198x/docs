# CPC WAIT qualification before Z80 0.9 adoption

Engineering-frontier qualification for emu198x/emu198x#2284. The agreed first
step is diagnosis against CPC evidence, preserving every original v4/v5
specimen and expectation. Any changed snapshot policy requires a separate
concrete decision before implementation.

1. Establish the original CPU 0.8 baseline at source e8b693731. Run
   `runtime-amstrad-cpc` board baseline tests and existing common CPC timing
   tests. Record fixture identities and exact commands outside the source tree.
2. In a private candidate, change only
   `crates/common-amstrad-cpc/Cargo.toml` to published CPU 0.9. Record the
   resolved dependency graph. Reproduce each model independently, not just the
   first failing assertion; retain full old and candidate outputs privately.
3. Trace the first changed CPU edges, WAIT samples and bus events in
   `crates/common-amstrad-cpc/src/lib.rs`. Compare native chip time, IRQ
   acknowledge, memory and I/O cycles. Instrumentation must not add clocks or
   change scheduling. Reuse `tests/interrupt_timing.rs`, `microsecond_grid.rs`,
   `shaker.rs` and firmware tests where possible.
4. Check original firmware/service references, the CRTC Compendium and
   vendored Arnold/Caprice32/MAME implementations. Re-evaluate #959/#971's
   mechanisms against the actual CPU correction rather than treating issue
   descriptions or per-opcode tables as hardware evidence.
5. Propose a concrete save version/reader policy after determining what
   changes. Do not change runtime snapshot acceptance before approval.
6. Implement only qualified changes, with regression tests that fail under the
   old defect and complete native continuation checks on 464/664/6128. Verify
   actual firmware boot, frame/audio timing, relevant IRQ and bus tests,
   Clippy and exact-head CI. Keep original fixtures intact.
7. Commit and push the bounded changes, publish safe evidence and update the
   issue. Preserve private evidence with checked hashes and retained commits,
   then remove task worktrees/build caches and stop owned processes.

Task workspaces: `/private/tmp/198x-cpc-wait`,
`/private/tmp/198x-cpc-wait-docs`, `/private/tmp/198x-cpc-wait-evidence`,
`/private/tmp/198x-cpc-wait-target`.

## Save policy approved after reproduction

All three original v5 specimens reproduce exactly with CPU 0.8. With 0.9,
the master time (330033 T-states) and monitor scan are unchanged, but the CPU
is at PC 0x00a9, M1 T1 rising, with 27512 retired instructions, instead of
PC 0x00ab, an internal cycle, with 27521 retired instructions. The three
subsequent captured fields, pixel bytes and audio sample bits agree; their
final CPU states do not. Both complete saved execution and its continuation
must therefore remain independently versioned despite an unchanged CPU
serialized layout.

Approved by the user on 4 November 2026:

- `crates/runtime-amstrad-cpc/src/snapshot.rs` writes v6 on 464/664/6128 and
  rejects v4 and v5 from their version alone, before payload decoding or
  runtime mutation. No approximate legacy continuation.
- Retain every original file under `test-data/amstrad-cpc/board-split-v4/`
  and `test-data/amstrad-cpc/save-v5/` unchanged. Reuse them as rejection
  evidence; keep their recorded byte identities.
- Add independently named v6 specimens from fresh corrected execution;
  compare complete snapshots, the first three resumed native fields, audio
  and final state. Test blank and live restores and rejection atomicity.
- Change only the two direct CPC CPU requirements and their lockfile edges
  when qualification completes. Other families keep their existing versions.
- Do not alter the WAIT free phase to satisfy the previous fixtures. The
  existing #971 grid/acknowledge discrepancy is still reproduced by 0.9 and
  remains a separate accuracy limitation.
