# Creation-ordered Emu198x issue triage

Review the initial organisation-wide queue in batches of around 25. Compare
issue bodies and latest scope comments with fixed main source, then record
positive completion evidence, remaining gaps and safe implementation boundaries.
Close only verified completions or exact duplicates. Keep architecture, API and
schema approval requirements explicit; do not turn a proposed design into an
adopted one merely because its documentation PR merged.

The frozen queue contains 246 issues open at the start of this continuation.
Twenty-three were already reviewed in batch 1; its two completed issues are no
longer open. Together these records cover 248 initial issues. New arrivals are
outside this sweep. The public [queue snapshot](2026-10-27-issue-triage-queue.json)
records creation order and original titles, not live status.

## Completed batches

| Batch | Original range | Count | Outcomes |
|---|---|---|---|
| [1](2026-10-27-oldest-issue-triage.md) | #35–#102 | 25 | #86/#88 completed; scope/evidence comments. |
| [2](2026-10-27-issue-triage-batch-02.md) | #103–#211 | 25 | #105 consolidated into #1284; hardware/scope corrections and fresh audio/pot reproductions. |
| [3](2026-10-27-issue-triage-batch-03.md) | #215–#260 | 25 | #244 completed; stale board, media, persistence and hardware premises corrected. |

| [4](2026-10-27-issue-triage-batch-04.md) | #261–#329 | 25 | MTX/Ace fixes in PRs #2167/#2168; malformed Einstein DSK input reproduced and promoted to a bug. |

| [5](2026-10-27-issue-triage-batch-05.md) | #333–#418 | 25 | Narrowed BBC Model B disk and Electron ROM work; preserved source/design gates and corrected persistence scope. |

| [6](2026-10-27-issue-triage-batch-06.md) | #421–#810 | 25 | #499 completed with real CPC disk execution; narrowed implemented cartridge/core work and retained qualification gaps. |

| [7](2026-10-27-issue-triage-batch-07.md) | #823–#1424, plus docs/site | 25 | docs #2 completed; aligned Amiga epics with implemented A530/configuration and retained proposed contracts. |

| [8](2026-10-27-issue-triage-batch-08.md) | #1427–#1814 | 25 | #1794 completed with ROM-driven tape workflow; retained video/controller reference disagreements and quality gates. |

## Remaining plan

Continue at **#1831**, then take the next roughly 25 creation-ordered entries
until the initial queue is exhausted. There are **48** unreviewed entries after
batch 8. Give every batch its own plan/findings file and commit; read back issue
states/edits before recording the outcome. Reuse the isolated checkout and build
cache while the sweep is active, then verify remote retention and remove all
task workspaces, caches and processes.

This is a dated triage record, not an all-system usability or hardware-accuracy
claim. Source revision, test counts, fixture omissions and evidence limits live
in each batch. Findings are being retained in draft docs PR #137 for editing.
