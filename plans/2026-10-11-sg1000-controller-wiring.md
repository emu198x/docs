# SG-1000 controller wiring and system distillation

Lane: engineering-frontier accuracy. Issue #227 requests a schema-bound
system distillation. Source review found a real controller decode defect:
`io_read` returns controller 1 for even ports and controller 2 for odd ports.
The home console instead places player 2 up/down in even-port bits 6/7 and
its other four controls in odd-port bits 0-3.

The shared primary library already records the home-console map, with
community provenance. Nicole Express's physical SG-1000 II experiment and
reproduced Enri schematic distinguish it from the arcade/PPI map. Ares and
MAME implement the same two-byte packing; Genesis Plus GX agrees. Do not
carry the SC-3000 PPI map or arcade table into the home console.

## Bounded correction

Keep the existing controller fields and their six-bit active-low helper.
Assemble the two CPU-visible bytes in the existing `Sg1000::io_read` branches.
Preserve the unused odd-port high bits as high, the full $C0-$FF aliases and
all non-controller decoding. This requires no new state, dependencies,
clock/stage changes or snapshot version change.

## Work and verification

1. Record the source interpretation under `reference/by-system/sega-sg-1000/`.
2. Add original Z80 guest regressions in
   `crates/machine-sega-sg-1000/tests/controller_wiring.rs`. Check all 4,096
   two-controller states, both regions and all low-byte aliases, plus input
   changes and save/restore. Require baseline failures and canonical controls.
3. Run the same original cartridge on installed MAME, capturing actual guest
   RAM through Lua and manipulating only host input fields. Verify the input
   set, execution completion and expected output rather than treating launch
   as evidence. MAME's alias extent differs; compare its canonical $DC/$DD
   ports separately from alias tests supported by the hardware schematic/Ares.
4. Correct the two read branches and module comments. Run machine/runtime
   tests, Clippy and formatting. Publish exact-head CI before merge.
5. Write `knowledge/systems/sega-sg-1000/overview.md` under the current schema,
   citing source functions, primary-library provenance, the SC-3000 catalogue
   entry and explicit unsupported variants. Capture only these additions in
   the private umbrella; update public system docs only where verified.
6. Close #227 once its documentary acceptance criteria and the source fix's
   merge gates are fulfilled; leave separate SC-3000/mapper issues open.

## Results

The original guest regression fails before the fix for 8,064 of 8,192
PAL/NTSC input states. All 128 states with player two released are controls.
Each state checks all 64 $C0-$FF aliases. Snapshot/input-transition coverage
also fails before the correction and passes afterwards.

The installed full MAME 0.289 SG-1000 runs a separate original cartridge,
reading canonical $DC/$DD and incrementing a guest RAM marker. All 4,096
host input combinations are verified at MAME's input ports, and all observed
guest byte pairs agree with the hardware table. The same cartridge in
Emu198x has 4,032 baseline mismatches and zero corrected mismatches. The
capture verifier checks every state, both bytes, input values and execution
markers; it rejects truncated captures and regenerated-ROM hash differences.

Affected suites: 25 passes, zero failures, one explicit commercial-cartridge
fixture ignore. That fixture is unavailable in the default media/Downloads
locations, so no commercial-gameplay claim is made. All-target Clippy and
formatting pass. Exact source head `6aeae61fce121dff9a7fa1f22eb699436c67f85b`
is committed/pushed; CI and merge verification remain pending.

The private distillation, index/log and reviewed source note are committed in
local umbrella `24b4fbcc` (not pushed). The current schema uses
`knowledge/systems/sega-sg-1000/overview.md`, rather than the issue's old
flat-file suggestion. It cites the library, machine functions, runtime
profiles/snapshots and the SC-3000 canonical-catalogue entry.

The distillation found a separate PAL audio clock mismatch: runtime profiles
use 3,579,545 CPU T-states/second while the PAL PSG constructor uses 3,546,893.
This is recorded accurately and left for a separate probe/correction; no
clock value changed in the controller fix.


The source was rebased over the verified Sord M5 merge, with affected tests
and Clippy rerun. Controller code is unchanged from the captured revision.
See [the complete capture bundle](2026-10-11-sg1000-controller-evidence/README.md).
