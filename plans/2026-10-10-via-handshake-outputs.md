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
No production correction has been made for this follow-up yet.
