# HMOS-II sprite multicolour timing — issue 1630, item 1

Lane: engineering-frontier accuracy. The issue attributes an extra 44 pixels
in `ss-hires-mc` and `ss-hires-mc-exp` to a 8565/8562 multicolour flag that
updates at dot 6 instead of dot 7. Reproduce that attribution before coding.

1. Audit `crates/mos-vic-ii/src/sprite_sequencer.rs`, its caller in `lib.rs`,
   vendored VICE's `viciisc/vicii-draw-cycle.c` and primary VIC-II references.
   Compare the current testbench images on 6569 and 8565. Retain baseline
   identities and mismatch coordinates; verify the stored 8565 references
   against native VICE if they disagree or have unclear capture provenance.
2. Write a failing chip regression for the reference's exact dot-boundary
   ordering. Select the existing model-specific draw schedule, preserving
   NMOS ordering. Reuse existing stored chip revision and sequencer state if
   sufficient; ask before any new pipeline pattern or snapshot schema.
3. Require the affected sprite images to improve for the explained reason,
   with all other pixels classified. Check the full available 8565 sprite
   reference set and all strict breadbin lanes, machine/runtime snapshots,
   chip tests, Clippy and formatting. No catalogue re-capture by assumption.
4. Commit one bounded fix and evidence. Keep issue 1630 open for its other
   independent items. The full C64 catalogue remains unavailable while the
   external Data volume is disconnected; preserve any merge gate requiring it.

No CPU model, master clock, new dependency, framebuffer geometry or snapshot
change is proposed at this stage. The earlier VIA fix and NTSC phase evidence
remain separate PRs 1689 and 1690.

## Reproduction and bounded correction

The 44-pixel HMOS penalty reproduces. The shared caller also delivers `$D01C`
at dot 0 rather than the reference's dot 7 on NMOS. Correct both existing
per-dot schedules together: NMOS dot 7 clears toggled multicolour flip-flops;
HMOS dot 6 toggles those flip-flops only when the expansion flip-flop is clear.
No additional retained state or schema is needed. This supersedes step 2's
assumption that the current NMOS ordering was already correct.

Native VICE 3.10 matches the four stored hires-to-multicolour images exactly.
The reverse transition's two stored 8565 images are stale by 44 pixels each;
native captures will supply their gate. Compile the vendored draw functions
unchanged into a directed oracle covering both transition directions, eight
sprite X phases and both expansion states. Exercise those 64 sequences on all
five shipping chip models (160 cases, 5,120 output dots).

## Full-machine result and reset

Neither smaller prototype is sufficient. Both were rolled back before shipping.
The dot-only change passes the 160 extracted-reference cases but leaves the
hires-to-MC image unchanged and worsens MC-to-hires with expansion. Delaying the
existing sprite draw by one engine tick makes both `ss-xpos` images exact, but
leaves mode/priority errors and regresses expansion changes. This is evidence
against landing a local latch correction on the present draw schedule.

| PAL program | 6569 before | 6569 dot only | 6569 one-tick prototype | 8565 before | 8565 dot only | 8565 one-tick prototype |
|---|---:|---:|---:|---:|---:|---:|
| ss-hires-mc | 330 | 330 | 319 | 374 | 374 | 363 |
| ss-hires-mc-exp | 1584 | 1144 | 616 | 1628 | 1100 | 572 |
| ss-mc-hires | 396 | 396 | 396 | 440 | 440 | 429 |
| ss-mc-hires-exp | 792 | 1408 | 704 | 836 | 1364 | 660 |
| ss-xpos | 2112 | 2112 | 0 | 2112 | 2112 | 0 |

Counts above use the staged testbench references. The two reverse-direction
8565 references themselves differ from current native VICE by 44 pixels; they
must not be treated as exact current-native goldens.

The 177 `$D01C` store observations in the settled Emu198x frame match the first
complete native monitor frame. This is a **checkpoint-phase comparison**, not
proof that two internal counters have the same bus phase: VICE queues only
addresses in `monitor_watch_push_store_addr`, checks them after the instruction,
and prints the current clock in `mon_breakpoint_check_checkpoint`. Its
`SET_ABS` performs `STORE` before `CLK_INC`. The native stop after the first mode
change reports CPU and VIC cycle 28; the write precedes that final advance.
The engine deliberately labels cycle zero as the previous line's last cycle
(`cpu_line_edge_cycle`), so normalize the two conventions before deriving any
CPU correction. No CPU timing defect has been established by this probe.

## Proposed extension of the existing stages — approval required

Keep the master clock, CPU, fetch chain and framebuffer geometry. Complete the
existing sprite draw pipeline instead of changing register values or shifting
finished images:

1. Trace the register write, native draw input and output cell using explicit
   physical cycle labels. Pin that mapping in a chip test before changing the
   pipeline. The native `cycle_flags_pipe` delays draw metadata, and the
   engine's cell origins must also be normalized; a raw one-tick subtraction
   is not a sufficient model.
2. Queue the existing sprite draw inputs alongside the pending cells: cycle
   identity, display-enable event and fetched sprite data needed by a delayed
   DMA load. Preserve entries across line wrap and retrace, including cycles
   with no visible framebuffer cell. Do not read newer chain data when an
   older queued DMA event reaches the shifter.
3. Reuse the existing saved X-position pipe and latch it after dot 7. Add the
   missing latched expansion and priority bits and update them at dot 6.
   Apply the model-specific `$D01C` rule at dot 6 (HMOS) / dot 7 (NMOS).
   Keep sprite colour selection, priority and collision coverage aligned with
   the same cell's graphics. These coupled stages cover the residual tracked
   in #1681 as well as #1630 item 1.
4. Preserve the additional descriptors/latches in snapshots. Stack this work
   on the approved VIA change (C64 version 19) and use **C64 snapshot version
   20**, rejecting versions 18/19. This avoids assigning incompatible layouts
   the same version. Update the frame-routing identity once the draw contract
   is fixed; do not re-capture catalogue hashes without explaining changes.
5. Require all eight native MC transition captures to be exact, keep the 160
   directed dot cases, run all 34 sprite split comparisons and strict VIC-II
   lanes, and add save/replay cases on both sides of queued DMA loads and mode
   writes. Run the full C64 catalogue before merging; the absent Data volume
   still blocks that gate.

This extends existing stages and their serialized state. It is not an approved
third production prototype yet. The retained rejected patches let us compare
failure modes without preserving either as shipping code.
