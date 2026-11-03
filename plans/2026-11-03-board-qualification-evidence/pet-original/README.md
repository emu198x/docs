# Original PET 2001 assembly 320008 qualification

Source PR [#2267](https://github.com/emu198x/emu198x/pull/2267) adds the 8 KiB
owner after restoring the missing second onboard PIA. PET v6 rejects v5;
legacy specimens stay immutable. Both original C000 firmware revisions are
identified by complete SHA-256 in the strict source tests before assembly.
No firmware or ROM-bearing state is included here.

The retained old-decoder control fails the focused second-PIA tests; the
corrected guest/IRQ/restore tests pass. Full PET suites, Clippy, CLI tests,
optimized CLI build and registry checks pass. The strict ROM log records
both BASIC-1 boot/arithmetic cases and 63 printable contacts plus Space.
Those cases also run the original PRG pointer path and exact continuation.

`pet-original-cli.json` identifies the actual CLI binary and assembled socket
map. Its complete native RGBA frame equals the runtime boot frame. See the
four runtime captures for the initial and revised C000 ROMs.

`pet-original-vice/command.json`, monitor script and logs retain the VICE 3.10
run with ROM patches disabled. `verification.json` compares all 1,000 screen
bytes and all 64,000 active monochrome pixels with zero differences. Host
palette and presentation borders are excluded. The 09 C000 revision was used
for this independent run. The retained-board receipt reports fresh complete
screen/pixel comparisons for 3032, 4032 and 8032 against their existing VICE
references, also with zero differences.

External IEEE devices, shared PIA pulse/handshake phases, cassette, other
original assemblies and complete CRTC personalities remain separate work.
