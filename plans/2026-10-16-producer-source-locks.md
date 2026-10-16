# Producer source locks

Approach approved on 2026-10-16 under emulator RULES §31. Engineering-frontier
work: shared infrastructure and validation. Tracks umbrella issue #137.

1. Adapt Build198x's `scripts/source_lock.py` and rejection controls in the
   emulator repository. Derive the full suite from workspace manifests, require
   every package on each native target, and bind receipts to the checked-out
   commit, unchanged committed lock, run, attempt and actual archive/executable
   bytes. Verify with deliberate missing/changed lock, receipt and archive cases.
2. Update `Cargo.toml` and `.github/workflows/release.yml` to build unpublished
   PR packages through the real release producer. Gate signing credentials to
   publishing runs; retain existing signing and notarization steps. Recheck
   bytes after notarization. Keep the existing manually maintained CI convention
   and test its critical gates rather than regenerate away its custom steps.
3. Add a five-host reusable qualification workflow before hosting. Preserve
   `test-linux-packages.yml`'s historical artifact-only dispatch route and reuse
   its Linux Homebrew checksum/install/smoke checks. Avoid duplicate PR builds.
4. Run Python controls and existing release Homebrew tests, inspect a real dist
   plan, then push a PR. Read real five-host CI reports and Linux smoke outcomes;
   record failures honestly. No release or merge is authorized by this plan.
5. Retain compact JSON evidence here, remove task-owned packaging output and
   temporary files after checking ownership/open files, and push docs separately.

Receipts are unsigned statements about source-lock identity. They do not prove
the executable's compiled package/feature graph or hardware compatibility.
Unsigned PR packages do not qualify Developer ID signing or Gatekeeper behavior.
