# Integrate the verified VIA and light-pen corrections

Lane: engineering-frontier accuracy. The missing external drive can be
replaced for validation by the existing private CI catalogue mirror, under
the standing maintainer decision in `test-data/accuracy-corpora.md`.

1. Verify the private store and its configured tag, download the C64
   catalogue archive and checksum manifest, then check the archive and all
   17 internal firmware/media files. Retain identities, not private payloads.
2. Assemble current main plus the already approved changes from PRs 1689,
   1694 and 1692 in `integrate/c64-via-lightpen`. Preserve the four separate
   commits. No further architecture or snapshot schema change is proposed.
3. Run the complete C64 catalogue with the mirrored media and firmware,
   including fresh-runtime snapshot replay for every entry. Do not update
   hashes to make failures pass; investigate any discrepancy first.
4. Run the focused native VIA/light-pen and snapshot regressions on this
   combined tree, formatting and affected-target Clippy. Previous broad
   consumer checks remain recorded in the individual plans.
5. Retain results and open an integration PR for the exact tested tree.
   Merge only after all required CI and catalogue gates pass. Close the
   superseded PRs and timer-start issue only after the combined fix lands;
   keep the broader HMOS issue open for its remaining sprite timing work.

Starting main: `f081faa8`. Original commits: `0a3c6c5d`, `145dc6cf`,
`6de2aba7`, `d75aa434`. The archive's SHA-256 is
`130a3097ce6216c6857b316642c75efcba6ebdda42c5605ccae08631b68b1521`.
All 17 internal checksums pass. This clears the missing-media prerequisite;
it does not yet prove the catalogue passes.

## Combined-tree checks

The integration tree is `8ef8394cf659f8028c4f79f5f3fc3e7ec0ee2f7b`, in
[source PR 1695](https://github.com/emu198x/emu198x/pull/1695).

The combined chip/runtime suites pass 324 ordinary tests, including both
native VIA guests and the timer/light-pen save-state regressions. The two
strict light-pen fixture checks pass: all 5,120 measured bytes match native
VICE and the prepared physical references. All 17 affected packages pass
all-target Clippy with warnings denied, and workspace formatting passes.

The [evidence directory](2026-10-10-c64-accuracy-integration/) retains these
logs, exact commands, the source tree identity and the mirrored files'
checksums. It contains no private firmware or media payloads.

The complete 13-entry catalogue is running. A firmware boot and selected
game passes are not sufficient to clear the gate: require every manifest
entry's unchanged frame/audio hashes and a `SNAP-PASS` before merging.
