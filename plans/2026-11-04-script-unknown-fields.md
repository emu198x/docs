# Reject unknown script fields

Lane: engineering-frontier shared tooling. Issue: emu198x/emu198x#2207.
Agreed approach: reject unknown fields and name the offending field.

1. Add parser regressions in `crates/emu198x-shell/src/script.rs` for the
   reported `run_until_pc.max_ticks`, misspelled `step.count`, fields belonging
   to another action, and fieldless actions. Run them against the current
   parser and require failures showing that invalid scripts were accepted.
2. Enforce strict deserialization on `ScriptStep`. Serde's internally tagged
   unit variants ignore remaining fields even with `deny_unknown_fields`;
   give those variants a shared empty-object deserializer while preserving
   their public Rust shape. Keep existing defaults and aliases working.
3. Run all shell library tests, formatting and Clippy. Exercise the actual
   Spectrum binary with invalid scripts and a valid synthetic-ROM control;
   require a nonzero exit and an error naming the unknown field.
4. Review the diff, commit and push the focused change and this plan in their
   owning repositories. Remove the task-owned temporary build directory.

No dependencies, hardware behaviour or public Rust enum shapes change.

## Verification

The initial regression failed because the parser produced
`RunUntilPc { addr: 32782, max_steps: None }` from a step containing
`max_ticks: 838656`. With only `deny_unknown_fields`, the fieldless regression
still failed because `ClearAudioCapture` accepted an invented field.

After the complete fix:

- `cargo test -p emu198x-shell --lib --quiet`: 304 passed, none ignored.
- `cargo clippy -p emu198x-shell --all-targets -- -D warnings`: passed.
- `cargo fmt --all -- --check` and `git diff --check`: passed.
- `cargo test -p emu198x-spectrum --test script_startup`: passed.
- The actual Spectrum executable exited 1 for `run_until_pc.max_ticks`,
  `step.count` and `query_cpu.unexpected`, naming each unknown field. The
  first error also named the accepted `addr` and `max_steps` fields.
- A synthetic zero-filled 16 KiB ROM with `step.instructions: 16` followed
  by `query_cpu` exited 0 and reported PC `$0010`.

The changes are limited to shared step deserialization and its regressions in
`crates/emu198x-shell/src/script.rs`. Scripts containing previously ignored
fields now fail to load; valid scripts retain their defaults and aliases.
