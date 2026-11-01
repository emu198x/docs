# SG-1000 v6 correction and owner split

Steve approved the independent PAL clocks and v6/v5 policy on 2026-11-01.
The former staged rate regression is committed with its green fix. Source PR
#2222 now includes three fixed owners, native-host pacing/display correction,
v6 writes, exact v5 NTSC/early-II reading and early v5 PAL rejection. The
original v5 fixture bytes are unchanged. It is ready for review; read current
CI conclusions and tested/merged heads before merging.

The final local selected suite passes 75 tests with seven exclusive direct
tests per owner. One original-cart test remains fixture-ignored. Strict
Clippy/rustdoc, registry (91 machines/34 binaries), generated-status and
fixture/ignore guards pass. A corrupted NTSC continuation fails, then the
restored original passes. The active/inactive screenshot path emits white/
black respectively. Three fresh 120-native-field profile captures have the
expected dimensions and elapsed clocks; these use project-written software.

Docs PR #170 and the site branch docs/sg1000-board-pages are the companion
surfaces. The site has 132 passing tests, 119 built routes and zero accessibility
defects over 103 content routes in two themes (16 redirects checked separately).
The pinned SG browser family can switch into its old PAL clock path, so all SG
embeds are withheld until a corrected module is published. No new historical
software, audio-device, every-PCB or physical-waveform qualification is claimed.

Reference audit #291 is merged; manual/photo originals remain in the private
Reference-PDFs library. Old red probes/metadata receipts are historical evidence;
use the v6 verification/CI/live receipts for the current implementation.

Finish the exact-head CI/merge checks, publish and verify all live routes,
update #2144/#2223 with final evidence, then inspect remote retention and remove
all three task worktrees and caches. Preserve the primary checkouts and the
unrelated locked worktrees. No further schema approval is outstanding.
