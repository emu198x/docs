# Qualify MARIA factory test patterns

Engineering-frontier research for the remaining #197 NMI phase gate. The
staged correction is approved; its physical assertion timing still needs
evidence. This work changes no production schema or pipeline design.

The [GCC MARIA archive](https://7800.8bitdev.org/images/0/06/GCC_MARIA_Chip_Layout_and_Netlist_Artifacts.zip)
SHA-256 is `849e215c71d13c17ec813f97a23b2078469c4b1e14a36dcd5a9ccf72b5360a48`.
Despite the archive's layout/netlist title, several `.2SC` files are readable
Sentry factory tests. The primary acquisition record retains member hashes
and distinguishes these files from binary test data and layout material.

1. Inspect the standalone-chip pin map and tester setup in
   `MARIAS/MARIAC/REV0/Z5349.2SC.1`, and the readable `MARIAS/MARIAB/ZMAR00`
   through `ZMAR03.2SC.1` patterns. Establish which revisions actually share
   those patterns. Names alone cannot establish equivalence with later
   compiled `.2MD` files.
2. Qualify a bounded source decoder in this plan's adjacent evidence directory.
   Use the [1977 FACTOR manual](https://bitsavers.org/pdf/fairchild/sentry/factor/67095738_FACTOR_Programming_Language_Reference_Manual_197703.pdf),
   sections 6.4.2–6.4.3, and the
   [1983 Fairchild handbook](https://www.bitsavers.org/pdf/fairchild/sentry/quick_reference/Fairchild_Digital_Test_Systems_Quick_Reference_Handbook_1983.pdf),
   printed pages 3-10, 3-11 and 3-15, for directions, masks, local register
   writes, calls, loops and repeats. Unknown syntax must fail. Keep source
   order, executed order and elapsed time distinct. Include synthetic
   direction/mask, repeat and call/return checks and malformed-input negatives.
3. Determine whether executed patterns compare NMI through a DMA shutdown.
   Retain nonzero observation counts and original source locations. Reject
   a deliberately masked or disconnected NMI observation. Resolve timing-set
   strobes, crystal pulses, and mask-write pipeline delays before converting
   pattern positions to native ticks. A 140 ns tester period contains two
   crystal-input pulses in the inspected setup; one row is not one tick.
4. If these sources establish an NMI constraint, reproduce the corresponding
   stimulus in the qualified reference harness and compare the outputs.
   Record what the factory program requires separately from observations of
   FPGA execution. Only then adjudicate the production pulse schedule. If
   no checked interrupt transition survives, record that bounded negative
   result and leave the physical timing gate open.

Do not redistribute the third-party archive or manuals in the public docs
repo. Retain our decoder, synthetic checks, compact derived observations,
source identifiers, hashes and exact reproduction instructions.
