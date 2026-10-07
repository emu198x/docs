# Validate the merged Amiga graphics corrections

Lane: best-in-class Amiga campaign. The user approved the full graphics sweep
before further accuracy changes. Baseline: merged emulator revision
`277957646cf041c343daf503d8d32d3e24e20eeb`, snapshot version 56.

1. Build `emu198x-amiga` from that clean revision. Record source, executable,
   firmware, guest and reference hashes. Reuse the 128-case inventory and
   capture adapter retained in
   `test-data/commodore/amiga/ecs-output-phase/ecs-colour-blanking/regression/`.
2. Capture all 128 guests and compare against all 384 retained reference
   fields. Preserve the registered native (16,2), reference (4,0), 1508x574
   comparison. Verify inventory, ready identities and unchanged input hashes;
   retain captures and per-field results under a new merged-sweep directory.
3. Run both `scripts/verify-amiga-test-kit-video*.sh` gates, the static and
   timed `scripts/verify-amiga-programmable-hblank*.sh` gates, and the runtime
   snapshot integration tests on the same source. Require positive case counts
   and use a deliberately altered image to demonstrate comparison failure.
4. Reproduce any failure and trace it through the existing reference-backed
   chip stages before proposing a correction. Preserve old reference pixels,
   clocks and coordinates. Additional architecture or snapshot schema changes
   require a concrete design and approval.
5. Record actual results, limitations and replay instructions in the code
   evidence directory and this plan. Commit the bounded evidence/fixes with
   normal hooks. The result covers this corpus; it does not establish physical
   hardware conformance or all display-mode combinations.

Broader Paula probes follow graphics closure as a separate bounded task.

## Result

The clean merged revision passes all 128 graphics guests: 384 retained
reference-field comparisons and 332,387,328 RGB samples, with zero differences.
All three previous palette-XOR failures are exact. Each static guest supplied
one fresh settled native image, compared against three adjacent reference
fields; this is not a claim of three new native captures per guest.

Both Test Kit lanes pass all six patterns. Static blanking passes fourteen
cases, timed blanking passes ten, and all 59 snapshot tests pass with no
ignored snapshot tests. Input/reference hashes match the preceding sweep;
the freshly built executable and all inputs remain unchanged during capture.

The self-contained `ecs-output-phase/merged-sweep/` evidence archive retains
the 128 guests, native images/logs and all reference fields. Its full replay
reproduces every exact comparison. Negative controls reject a changed PNG,
the same PNG with its hash updated, and an empty inventory. No reference
pixels, crop coordinates, clocks, snapshots or production code changed.

The broad graphics rerun is complete at the registered software-evidence
boundary. The next independent accuracy investigation is Paula's unmeasured
period-write/minimum-period/modulation behaviour. Wider display combinations,
NTSC and physical-hardware calibration remain separate evidence gaps.
