# Mega Drive regional board owners

Continue the approved #2144 programme in the engineering-frontier lane using
fixed private machine crates over shared wiring and a closed family dispatcher.

The existing three profiles become owners named `machine-sega-mega-drive-japan`,
`machine-sega-genesis` and `machine-sega-mega-drive-europe`. The shared engine moves
from `machine-sega-mega-drive` to `common-sega-mega-drive`. Retire the aggregate
machine registry ID in favour of the three existing profile IDs as machine IDs;
keep the family runner, profile IDs, aliases and version-2 envelope bytes.
Power Base Converter, pad type and cartridge remain configurations.

1. Capture complete original v2 envelopes and three continued native fields
   (every pixel, timestamp and stereo sample bit) for each market in native and
   Power Base Converter mode under `test-data/sega-mega-drive/board-split-v2/`.
   Use project-written cartridges with live sound, input, RAM and a partial
   field. Verify restoration and a deliberately corrupted fixture before moving
   the engine. Keep the capture recipe in the runtime tests.
2. Move `machine-sega-mega-drive/src/{lib,io,power_base,tests,power_base_tests}.rs`
   into the common crate without changing hardware algorithms or serialized
   fields/order. Add fixed owners and transparent serialization with checked
   state binding. Do not expose mutable raw state or mutable VDP region wiring.
3. Add `runtime-sega-mega-drive/src/machine.rs`; update runtime, input, queries,
   debug, profiles and snapshot modules to use the dispatcher. Validate payload
   region/VDP standard/RAM geometry before changing runtime time or caches.
   Preserve cartridge/PBC reset and switching rules, exact native boundaries,
   held controller state and existing save bytes. Test rejection atomically.
4. Add exclusive direct evidence for each owner: guest video, region-register
   and controller reads, both CPUs and PBC/banking, native partial-field stepping
   and checked state binding. Run common/owner/runtime/runner suites, strict
   Clippy/rustdoc, registry/fixture/docs guards and fleet conformance. Keep native
   68000, Z80, VDP and sound algorithms unchanged.
5. Give all three owners registry rows and regenerate status. Update current
   docs and site exact-player mappings/capture identity/routes; redirect the old
   aggregate page to the existing default Genesis profile. Verify the pinned
   player catalog before embedding. Run site tests/build/accessibility, merge
   after CI, verify live pages and per-board evidence, update #2144, then remove
   task worktrees/caches after verifying commit retention.

Source: Sega's Software Manual, system I/O/version register at `$A10001`, in
`reference/by-system/sega-megadrive/1990-sega-genesis-software-manual.txt` (printed
page 71, revision 02/20/92) specifies independent domestic/overseas and NTSC/PAL
bits. This task separates the three already modelled combinations. It does not
invent board revision, TMSS or sound-chip variants, add SC-3000 support, alter
hardware timing, publish registry packages or add registry dependencies.
