# SMS display-enable phase investigation

Engineering-frontier validation. `render_pixel()` currently lets live display
enable suppress the background while a preselected sprite can still pass
through the fallback branch. This may produce a mixed blanked/sprite line.
Do not change that branch before resolving the reference timing disagreement.

MAME copies display enable per line and accepts early-line writes until an
explicitly unverified cutoff. Genesis Plus GX redraws early line changes but
only partially blanks mid-line for Mega Drive, not SMS. Mesen's SMS pixel
output uses the live rendering-enable bit. Source agreement on steady-state
blanking does not prove the exact response to a mid-line register write.

1. Generate an original guest with an opaque red tile background, green
   sprites and blue backdrop. Change R1.6 during an active line and restore
   later, through real CPU I/O. Include always-enabled and always-blanked
   controls, PAL/NTSC, and delayed-write cases.
2. Run identical cartridges in Emu198x and the unmodified Genesis Plus GX
   reference. Verify completion RAM and quantify each scanline's colour runs.
   Record source revisions, cartridge hashes, inputs and final captures.
3. Inspect primary hardware observations and independent reference code.
   Distinguish a renderer inconsistency from measured silicon timing. Preserve
   unresolved timing explicitly instead of choosing the easiest passing gate.
4. Propose any needed pipeline/state extension only after the evidence is
   concrete. The existing native-clock proposal does not approve adding a
   display-enable latch. No production correction is authorised by this plan.

## Results and disposition

All 24 runs complete: two engines × two regions × six cartridges. Always-on
and always-off active pictures match byte-for-byte (49,152 pixels each), after
checking the documented NTSC/PAL framebuffer geometry. The probe avoids the
unmerged colour-zero bug by using an opaque red background tile. Eight green
sprites cover x=0,32,...,224 on lines 64–71; backdrop is blue.

All eight Emu198x toggle runs show mixed red/blue scanlines at active lines
65 and 81. For delays 0/8/16/24, green pixels surviving beyond the first blue
pixel on line 65 number 32/24/16/0 in NTSC and 32/24/8/0 in PAL. At the final
delay the transition is beyond the sprites; zero is a positive late-write
control. These are observed colour runs, not assumed register-write edges.

For delay 8, the CPU I/O trace sees R1's second byte at active (65,142) NTSC
and (65,160) PAL, with V=64. Sampling occurs after a CPU T state and can trail
the actual write by one pixel. This is consistent with the already documented
stale V count; it is not evidence for changing the CPU's instruction timing.

Genesis Plus GX produces whole blanked lines in every toggle case. The
reference trace forwards its real port handlers, and traced/untraced RAM and
framebuffer bytes match for both regions. Its late-write partial blanking is
implemented only for Mega Drive. MAME's cutoff is explicitly unverified and
its file lists mid-scanline changes as unfinished; Mesen uses live enable in
its pixel path. Neither copying a line latch nor merely suppressing residual
sprites is yet a fully supported timing correction.

**No production change.** The next requirement is a primary hardware capture
or a suitably validated original hardware test that distinguishes the two
behaviours. The six sprite-status timing failures from the previous cartridge
probe also remain open. This does not extend the pending native-clock design.

## Retained evidence and reproduction

[Evidence](2026-10-11-sms-display-blanking/) contains the original Python guest
generator, 24 RAM dumps/captures/logs, two trace pairs, analysis, source hashes
and the exact runners. The runners contain button pulses after frame 200;
these 60-frame runs never reach them. No commercial or third-party test ROM
is bundled. Regenerate each original cartridge with
`python3 make_blanking_guest.py OUTPUT MODE DELAY`, using `on 0`, `off 0`
and `toggle` with 0/8/16/24.

Build runners against the pinned Emu198x rlibs and unmodified Genesis Plus GX
dylib using the procedure in
[the preceding probe](2026-10-11-sms-blanked-sprite-overflow.md#reproduction).
Each runner takes `ROM REGION PREFIX 60`, region `ntsc-u` or `pal`. The
reference trace runner takes the same arguments and traces frame 60; the
Emu198x trace runner takes ROM and region and traces one frame after 59.

`analyse_blanking.py` reads PPMs or retained PNGs, verifies every completion
marker, exact control pixels, expected configuration coverage and produces
`summary.csv`. In an isolated copy, corrupting a completion marker makes it
fail with `AssertionError`; the negative-control log is retained. The generator
reproduces all six cartridges byte-for-byte after formatting. Ruff passes.
Representative transition captures were visually inspected in both regions.

Primary observation record:
`reference/by-topic/vdp-sms/2026-display-blanking-observations.md`.
