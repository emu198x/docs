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

| [9](2026-10-27-issue-triage-batch-09.md) | #1831–#2007 | 25 | #1983 completed; separated shipped controller fixes from remaining physical research and extraction gates. |

| [10](2026-10-27-issue-triage-batch-10.md) | #2032–#2149 | 23 | #2032 completed; #2060 consolidated into #2138; concrete runner/firmware/input bugs and rule-34 splits retained. |

## Sweep complete

All **248** initial issues have a disposition across ten batches: nine batches
of 25 and one of 23. The frozen open-at-start queue has 246 entries; #86/#88
had already closed in batch 1. Repository plus issue number is the identity,
including docs #2 and site #6. New arrivals are outside this sweep.

Nine verified completions: flagship #86, #88, #244, #286, #499, #1794, #1983
and #2032, plus docs #2. Two superseded/duplicate scopes were consolidated:
#105 into #1284 and #2060 into #2138. Existing source, dated retained evidence,
fresh tests and missing physical/browser/OS qualification are distinguished in
each batch. Detailed original requirements remain alongside current corrections.

Two small source fixes merged after complete CI: #2167 rejects unsupported MTX
media instead of reporting a successful no-op; #2168 records the Ace gray level
as an uncalibrated presentation default. #261 remains open for actual file
loading. The new bounded Einstein DSK probe promoted #277 to a bug: two malformed
inputs panic and a missing sector payload is silently accepted.

## Next bounded work

Address the confirmed bugs before broader features. #277 needs complete parser
bounds/payload/geometry handling; agree any dependency migration first. Other
small candidates include C64 MCP PRG startup #1858, CoCo firmware/text input
#2134/#2135, native-UI audit scope #2137 and the source-backed A2000 prose
correction #2147. Larger timing/schema/host work retains its explicit design and
evidence gates. Family extraction #1999 waits for the measured shell-stability
window (starting no earlier than 27 October) and publication prerequisites.

This is a dated triage record, not an all-system usability or hardware-accuracy
claim. Findings remain in **draft docs PR #137** for editing. The [final positive state read and finite-queue reconciliation](2026-10-27-issue-triage-final-states.json) are retained beside this index.
