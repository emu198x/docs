# Light-pen hardware reference normalization

Lane: engineering-frontier accuracy. The remaining two samples reported by the
previous light-pen investigation are an input-version mismatch, not an observed
hardware/reference disagreement after applying the upstream preparation step.

1. Compile the staged testbench's unchanged `makeref.c`, as its Makefile does,
   and convert all four physical `.prg` dumps. Verify every output byte against
   native VICE and the references embedded in the staged R04 guest.
2. Make the runtime regression apply that documented pre-R03 correction before
   the independent hardware comparison. Retain raw input identities and avoid
   normalizing dumps that do not meet the upstream guard. Add converter parity
   and current-dump pass-through checks; prove mutation still fails the gate.
3. Correct the shared observation record, source fixture provenance, campaign
   notes and PR1692 description. Preserve original raw observations in evidence,
   but remove the now-resolved claim of an unexplained two-sample discrepancy.
4. Commit this bounded verification correction. No production chip, snapshot,
   catalogue hash or reference-emulator code changes. PR1692 still requires its
   full catalogue gate while the external media volume is unavailable.


## Result

The unchanged converter prints `pre r03 dump, correcting` on all four input
files. It changes only offsets 766 and 767, adding four to each. Every output
byte matches the corresponding native VICE capture and the prepared reference
embedded in the staged R04 guest. A second conversion, with a PRG header
restored, leaves the already-prepared payload unchanged and prints no correction.

| Chip | Prepared bytes | Embedded guest address |
|---|---:|---:|
| 6569 | 1280 | `$18D4` |
| 8565 | 1280 | `$31F3` |
| 6567R8 | 1280 | `$0EC3` |
| 8562R4 | 1280 | `$22E0` |

The regression now applies that preparation before the hardware comparison.
Its independent native capture, prepared physical dump and actual measurement
agree in all 5,120 bytes. A fast fixture test checks the conversion, embedded
reference and pass-through guard on all four models. Mutating one native
fixture byte makes that test fail with exit 101; the original hash is restored
and the test passes again. No production implementation or golden binary
changed for this correction.

The initial raw comparisons were valid byte measurements but used the wrong
reference preparation for the guest revision. They do not establish an
unexplained physical timing difference. The shared curated observation record
and PR1692 description have been corrected accordingly.
