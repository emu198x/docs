# Qualify the four remaining +3 picture/audio cases

Engineering-frontier continuation of #2265, requested after the five audio-only
cases merged. Source baseline 2ae3a5119; docs baseline b181062. Keep Cybernoid,
Stormlord, Tetris and Dragon Ninja's expectations intact until their complete
picture/audio differences are explained. Existing approved physical WAIT,
immutable-media and ordinary-input decisions remain binding.

1. Restore only needed probes and exact production binaries from the verified
   plus3-audio recovery archive. Verify archive/member SHA-256. Run the four
   unchanged cases on the exact historical/current production binaries with
   explicit manifests, screenshots and full WAVs. Require all eight complete
   results and actual historical matches before calling that producer a baseline.
2. Reuse the existing private AY/speaker observer, replay tests and guest-screen
   probes. Record complete native-field write histories, displayed RAM, paging,
   guest PC/stack and start/end sound state. Observe animation/cycle transitions
   rather than choosing a field by desired hash. Compare the actual pixels and
   software state represented by both old and current pictures.
3. Reuse vendored MAME/Fuse/SpecIde precedent and bounded reference observers.
   Match complete displayed bytes and guest-program transitions where possible.
   Preserve any loader-bound reference failures. Never change canonical images,
   fabricate matching clocks, weaken FDC pacing or install guest-state shortcuts.
4. Explain each first meaningful difference. Re-derive the entry's semantic
   anchor from original software and complete observations. Prefer preserving a
   golden through an evidence-backed stable waypoint when the existing fixed
   navigation convention applies; otherwise qualify a changed oracle only with
   concrete pixel/guest-state and sound reconstruction evidence. A new hardware
   fix, dependency, API/schema or pattern needs its own agreed concrete design.
5. Remove all temporary implementation hooks before production verification.
   Run each changed real entry plus snapshot replay, retain stale-oracle and
   changed-input failures, and run catalogue tests/Clippy. Shipping changes must
   pass normal exact-head CI; docs use actual local validation (no CI workflow).
6. Reconcile the complete 103-entry ledger with explicit fresh/reused counts.
   Do not claim a fresh sweep if some observations are reused. Close #2265 only
   if all four are accounted for and verified. CPC remains separate under #2284.
7. Archive all raw evidence, failed hypotheses and exact signed commits/binaries,
   verify every member, then remove owned worktrees/caches/processes. Preserve
   unrelated work in all primary checkouts.

Resource bounds: builds 600 seconds, each source case 300 seconds, each MAME
run 90 wall seconds and an explicit emulated-time endpoint, logs 16 MiB unless
a measured larger bounded trace is recorded first. Stop owned builds if free
disk falls below 512 MiB. Source worktrees:
/private/tmp/198x-plus3-four-current and /private/tmp/198x-plus3-four-original;
docs /private/tmp/198x-plus3-four-docs; evidence
/private/tmp/198x-plus3-four-evidence; separate release caches
/private/tmp/198x-plus3-four-current-target and
/private/tmp/198x-plus3-four-original-target.

## Outcome

All four frame/audio differences are accounted for. The original producer
reproduces every old pair; current cases retain their intended animated
menu/title state. Complete guest writes and cross-producer native pictures
explain three frames. Dragon Ninja's 1600 timed attribute writes reproduce
every native pixel of both captures; swapped timing fails on exactly 45
pixels. All eight complete PCM windows reconstruct exactly.

The source patch retains every capture setting and changes only eight hashes,
semantic comments and changelog. All four production runs and snapshot replay
checks pass; independent stale-frame/audio controls remain red. The combined
ledger accounts for 103 entries, four fresh and 99 reused, with no failures.
[Evidence and reproduction](2026-11-04-plus3-final-four-evidence/README.md).
