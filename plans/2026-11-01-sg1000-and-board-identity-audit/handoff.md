# SG-1000 v6 correction and owner split

Steve approved the independent PAL clocks and v6/v5 policy on 2026-11-01.
The former staged rate regression is committed with its green fix. Source PR
#2222 now includes three fixed owners, native-host pacing/display correction,
v6 writes, exact v5 NTSC/early-II reading and early v5 PAL rejection. The
original v5 fixture bytes are unchanged. Source PR #2222 merged after full CI passed at fe63f9febb2263b99033af5b5bd5101dfcd27e4e;
its merged tree at 194d68dd002e1137573ecee0f01d4036e00e8936 is identical.

The final local selected suite passes 75 tests with seven exclusive direct
tests per owner. One original-cart test remains fixture-ignored. Strict
Clippy/rustdoc, registry (91 machines/34 binaries), generated-status and
fixture/ignore guards pass. A corrupted NTSC continuation fails, then the
restored original passes. The active/inactive screenshot path emits white/
black respectively. Three fresh 120-native-field profile captures have the
expected dimensions and elapsed clocks; these use project-written software.

Docs PR #170 and merged site PR #42 are the companion surfaces. The site has 132 passing tests, 119 built routes and zero accessibility
defects over 103 content routes in two themes (16 redirects checked separately).
The pinned SG browser family can switch into its old PAL clock path, so all SG
embeds are withheld until a corrected module is published. No new historical
software, audio-device, every-PCB or physical-waveform qualification is claimed.

Reference audit #291 is merged; manual/photo originals remain in the private
Reference-PDFs library. Old red probes/metadata receipts are historical evidence;
use the v6 verification/CI/live receipts for the current implementation.

Current CI and live receipts accompany this record. #2144 records the completed
configuration split and the remaining manufactured-board qualification; #2223
is closed by the fix. Release PR #2170 records the browser publication gate.
No further schema approval is outstanding.
