# Atari 5200 fixed-owner evidence

Source PR: emu198x/emu198x#2253. Independent original v20 fixtures and their
exact generator are committed in the source repository, under
`test-data/atari/5200-board-owners`.

The initial focused suite passed 80 tests with one existing real-ROM test
ignored; the two added profile/reset/restore tests subsequently passed too.
Sixteen owner invariants cover physical input fitting, native boundaries,
foreign region rejection, parsed media and impossible absent lower-fire
state. The 80-case two-port guest probe checks missing connectors/selectors.
Changing CA021374 to expose four ports makes its physical-port test fail;
the complete negative-control log is retained.

The default native binary ran eight passing tests, including its UI bridge;
twelve tests passed without UI, covering native options plus actual CLI,
script and MCP launches. The retired implicit board fails through the real
headless and MCP executable paths, not only argument parsing.

The private-asset probe ran all three explicit owners through 320 frames of
real BIOS plus Pac-Man: each produced six colours and 90,240 non-background
pixels, then matched the complete next-frame state after restore. These are
execution observations, not qualification of analogue tolerances, VCS
adaptors or every firmware/board fitting. ROM bytes are not distributed.

Verified private inputs:
- Pac-Man SHA-256: `5097b4763eefd8650781698e36b68bc0c9ae0863916312e6fa4364e4da104080`
- BIOS SHA-256: `06b250f18983d058c0f156ce7ee88ae48b6eaf11e6f10f21dccf6ac7ffb6a6af`

The first hosted registry check caught stale generated status pages. They
were regenerated, checked locally and committed; no registry gate changed.
Full applicable hosted CI remains required before merging the source PR.
