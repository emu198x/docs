# Shared Amiga RAM configuration before board extraction

Engineering-frontier continuation of #2144, under the approved fixed-owner
splits. This increment removes an existing forbidden machine-to-machine edge;
it does not introduce boards, clocks, dependencies or a new save version.

Root cause: ECS and A1200 re-export `RamConfig` from the OCS machine crate.
The type and its family-wide validation belong to the common hardware layer.
All three already depend on `common-commodore-amiga`.

1. Move the existing `RamConfig` declaration, presets, validation and Default
   implementation, unchanged, from
   `crates/machine-commodore-amiga-ocs/src/lib.rs` into
   `crates/common-commodore-amiga/src/ram_config.rs`; expose it from common's
   `src/lib.rs`. Keep OCS/ECS/A1200 public re-exports for source compatibility.
2. Remove the OCS dependency from ECS/A1200 `Cargo.toml` and update Cargo.lock.
   Verify cargo metadata contains no machine-to-machine edges for these crates.
   Add the existing rule-34 dependency check to `scripts/status/check_registry.py`
   with regression coverage for normal, renamed/workspace/target dependencies
   and an empty scan. Prove the check rejects the original manifests.
3. Add `crates/runtime-commodore-amiga/tests/ram_config_boundary.rs` proving
   the old paths remain one type and postcard retains the old three-field
   encoding. Exercise defaults, expansion configurations and invalid layouts.
   Existing RAM/layout and snapshot suites remain the behavioural authority.
4. Run the three machines' and common's suites, runtime RAM/snapshot tests,
   strict all-target Clippy, rustdoc, registry and full CI. Commit/push one
   source change, merge the verified head, retain CI evidence with this plan.
5. Update #2144 with the prerequisite and remaining A1200 regional owners.
   Inspect tracked/untracked/ignored files and remote retention, then remove
   task worktrees/build caches. Preserve the existing primary checkouts and
   unrelated locked worktrees.

Next extraction: A1200 PAL/NTSC fixed owners over shared AGA wiring, preserving
v66 state bytes and generic Amiga runtime/live access. Inspect the schematic's
oscillator/strap identities and qualify both configurations before claiming
particular PCB revisions. OCS/ECS multi-board groupings remain separate work.
