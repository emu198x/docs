# Correct shared VIA handshake output behaviour

Lane: engineering-frontier accuracy. Follow-up from the 1541/1571 alternate
port-read correction, kept separate from source PR 1696.

## Observed discrepancy

The retained public-pin probe reports 12 mismatches in 18 observations and
exits 1. It covers CA2/CB2 handshake and pulse modes, direct read, direct
write and board-override reads. These are logical transition observations,
not measurements of sub-cycle pulse phase.

The core currently makes a handshake output high when software accesses
the port and low when the active CA1/CB1 edge arrives. The documented
sequence is the reverse. Port A's direct and board-override reads also
fail to generate a pulse in pulse mode. Port B reads must not initiate an
output handshake; they currently share the state-changing acknowledgement
helper with writes. The probe's B-read controls and both write-pulse
controls pass their immediate-level expectations.

Primary source: MOS 6522 preliminary datasheet, November 1977, the
Peripheral A/B Handshake sections and PCR control tables in
`../../reference/by-topic/via-6522/mos-6522-preliminary-nov-1977/mos-6522-preliminary-nov-1977.md`.
CA2 mode 100 goes low on ORA read/write and high on active CA1; mode 101
pulses on ORA read/write. CB2's corresponding initiation is ORB write only.
The existing VICE reference corroborates this in `viacore_store`,
`viacore_read` and `viacore_signal`; its pulse comments explicitly warn
about coarse timing, so those callbacks alone cannot establish exact
pulse width or phase.

## Bounded implementation plan

1. Add red chip regressions in `crates/mos-via-6522/src/lib.rs`: both
   edge polarities, direct/polled edge delivery, normal versus alternate
   port reads, override reads, B-read non-trigger controls and output
   transitions. Verify they fail for the documented reason before editing.
2. Use the existing handshake and pulse latches. Separate interrupt
   acknowledgement from B-write output initiation and restore the correct
   access/active-edge polarity. Keep the current saved-state layout; stop
   for a concrete design review if a genuinely new timing stage is needed.
3. Consult the primary waveform figures and observe existing write pulses
   through a consumer's master-clock path before making any claim about
   exact read-pulse timing. Do not infer a range from one sample.
4. Run the VIA suite and every affected consumer suite, then relevant
   firmware/drive and snapshot checks. Retain the pin probe's before/after
   rows and source identities. Keep this as one separate production commit.

The retained probe links a fresh VIA build from clean source commit
`05de4cf9`. Its exact source/library hashes and compiler command are in
`identity.json`; `build.log` retains the library build result.
The correction uses these existing latches; completed validation is recorded below.

## Waveform and consumer check

The original November 1977 scan was recovered from the Zimmers `6522.zip`
archive (24 GIF pages). Page 5, Figures 3 and 4, shows an active-low pulse
lasting one complete Phi2 period. It also distinguishes the sub-cycle
launch edge of reads and writes. The current core observes whole Phi2
periods; this correction will verify the period and handshake sequencing
at that existing observation granularity, without claiming half-cycle pin
phase accuracy. VICE's immediate pulse callbacks are not a phase oracle.

Add a master-clock regression in `crates/machine-acorn-atom/src/lib.rs`:
a synthetic CPU program writes and reads normal/alternate ORA addresses;
record every CA2 sample and the Centronics bytes. Existing Atom writes
already reach the printer with one sampled low period. The read correction
must use the same existing pulse latch and deliver one additional strobe,
while alternate accesses deliver none. Chip tests separately cover both
CA1/CB1 polarities and edge-delivery paths. No API or save-state field is
added or changed by this bounded correction.

## Regression evidence

Before correction, the chip checks fail with `normal access 1 must assert
CA2` and `access must assert handshake: B=false, rising=false,
polled=false, access=0`. The master-clock printer guest emits `[72, 74]`
instead of `[72, 72, 74]`, proving its normal ORA read loses a real strobe.
The Port B pulse-read control already passes and remains a control.

After correction, all focused chip/machine checks pass and the retained
public-pin probe improves from 12/18 mismatches to 0/18. The Atom test
observes exactly three isolated low clocks on normal port accesses and
three Centronics bytes. Alternate accesses add no strobe. The snapshot
regression in `crates/runtime-acorn-atom/src/snapshot.rs` saves at 32
instruction boundaries across pulse and handshake mode and checks future
printer bytes and full state after each continued instruction. It passes.
All affected-target Clippy checks pass with warnings denied.

The 554 ordinary consumer tests and all doctests pass on source commit
`08045934`. Real-firmware checks and the full C64 catalogue remain merge
gates. Expected catalogue hashes will not be changed to make
a discrepancy pass. No public API, data field or snapshot version changed.


## Strict and final-head checks

All 36 explicitly selected strict checks pass: 31 real-firmware checks,
the VIC-I reference survey and its negative control, and three real-ROM
1541/1571 disk round trips. All nine commands exit 0. The exact commands
and terminal output are retained; diagnostic dump generators are not
selected as regression tests.

Final source head is `092f61c4`. The only revision after the 554-test run
removes an unproven PCR-rewrite assumption from the snapshot test:
handshake mode now receives no acknowledgement and must retain its first
low strobe; pulse mode emits three. All 32 snapshot positions pass again,
as do affected Clippy and formatting. The final successful catalogue build
is byte-identical to the binary already running the three catalogue shards
(SHA-256 `1904eb9aa594d15c3416f6ab112f6161d4b54fd7ba89e08e2c441a59a9fa7268`).

The complete 554-test consumer suite and all doctests subsequently pass
again on final head `092f61c4`; `final-suites.log.gz` retains the terminal
result. There are 115 explicitly ignored fixture/diagnostic cases in this
ordinary run; the separately retained strict commands select their stated
firmware, survey and drive regressions.

## Complete C64 catalogue

All three shard commands exit 0. Every one of the manifest's 13 entry IDs
occurs exactly once in the ordinary PASS results and exactly once in the
SNAP-PASS results, checked against the manifest's round-robin assignment.
All expected frame and audio hashes remain unchanged, including the
1541/1571/1581, tape, cartridge and G64 paths. The terminal logs, commands,
manifest hash and binary hash are retained in `catalogue-result.json` and
the three `production-shard-*` records. No private media or firmware is
included. CI remains the final source merge gate.
