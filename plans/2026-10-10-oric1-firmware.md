# Separate Oric-1 and Atmos firmware selection

Lane: engineering-frontier accuracy. Investigate issue #345 through the
existing shared firmware resolver before changing profiles or firmware IDs.

## Confirmed evidence

Source `44bdba6c` boots the MAME-identified BASIC 1.0 and 1.1 images to Ready
through `OricRuntime`. A directory containing only BASIC 1.1 as `oric.rom`
also boots it when `build_variant` is asked for `Model::Oric1`: the screen
says `ORIC EXTENDED BASIC V1.1`. The wrong-model probe exits 1.

The images come from the author's
[Oricutron v1.2 archive](https://www.petergordon.org.uk/oricutron/files/Oricutron_win32_v12.zip).
Their SHA-1 values match the independent MAME manifest in
`emulators/multi-system/mame/src/mame/tangerine/oric.cpp`:

| Image | SHA-1 |
|---|---|
| `basic10.rom` | `333116e6884d85aaa4dfc7578a91cceeea66d016` |
| `basic11b.rom` | `9451a1a09d8f75944dbd6f91193fc360f1de80ac` |

Keyboard-entered `PRINT ASC(STR$(1))` returns 2 on BASIC 1.0 and 32 on
BASIC 1.1. The *Oric-1 Companion*, STR$ entry (canonical extract under
`reference/by-system/oric/linsac-the-oric-1-companion.docling/`), documents
the unwanted initial control character for nonnegative values. Preserve
this ROM behaviour rather than patching it in the emulator.

The behaviour probe checks complete command echo, the ROM-specific numeric
result, absence of ERROR and a second Ready prompt. Substituting BASIC 1.1
for the Oric-1 image fails with `ROM-specific STR$ result must match`, exit
101. The normal two-ROM run exits 0. Probes, logs and identities are in the
[evidence folder](2026-10-10-oric1-firmware/); firmware is excluded.

## Proposed correction — awaiting agreement

1. Add `Model::firmware_id()` and a distinct `oric1-rom` requirement for
   Oric-1. Retain the current `oric-rom` ID and exported `BIOS_FIRMWARE_ID`
   for Atmos. Runtime lookup and error reporting use the selected model's
   ID. No hash allowlist: explicit custom/localised firmware remains valid.
2. Oric-1 searches `oric-1.rom`, `oric1.rom`, then `basic10.rom`, using
   `EMU198X_ORIC1_ROM` for a file override. It no longer borrows `oric.rom`
   or `EMU198X_ORIC_ROM`. Atmos retains its existing filename/environment
   conventions, with `basic11b.rom` as a model-specific candidate.
3. Preserve bare `--rom PATH` regardless of argument order. Defer CLI ROM
   specifications until the final model is known, then use the existing
   shared `FirmwareOverrides::add_spec` and resolver. Explicit `ID=PATH`
   stays tied to its named ID; reject an ID for the wrong model. Apply the
   same resolved overrides to UI, headless and MCP startup.
4. Update profile/help text and tests, including both model/ROM argument
   orders, generic-only rejection for Oric-1, missing/bad explicit paths,
   model-specific environment overrides, both-firmware directories,
   explicit custom firmware and model switching. Retain live snapshots;
   no format or version change is needed.
5. Add strict, model-specific real-ROM tests for exact banner, Ready and
   the STR$ result, with wrong-ROM negative controls. Run affected runtime,
   launcher and machine tests, Clippy/format and CI before merging. Close
   #345 only after the profile and real-ROM requirements pass.

This changes the Oric-1 firmware contract: callers supplying a
`FirmwareSet` or `--rom ID=PATH` must use `oric1-rom`, and a generic-only
directory now reports missing Oric-1 firmware. These are intentional
compatibility breaks that require agreement under AGENTS.md.

Alternatives considered: only change filename lookup while keeping a
shared firmware ID (leaves API-level model ambiguity); classify/route
firmware by known hashes (rejects or ambiguously handles modified images).
The distinct existing-profile requirement is the recommended bounded fix.

## Investigation

1. Verify BASIC 1.0 and 1.1 images from the Oricutron author's v1.2 release
   against the independent MAME ROM manifest. Keep firmware outside Git;
   retain the source URL, archive hash and individual image hashes.
2. Boot both images through `OricRuntime` and observe actual TEXT RAM. Exercise
   the normal `build_variant` resolver with a directory containing only a
   generic `oric.rom`, then with explicit model-specific files. A request for
   Oric-1 must not silently select Atmos firmware.
3. Identify a reproducible ROM-specific BASIC behaviour, using original
   firmware execution and primary documentation. Preserve its behaviour;
   do not teach the renderer BASIC workspace addresses.
4. Record a bounded design in the existing profile/runtime/launcher paths,
   including migration of public firmware IDs and explicit ROM overrides.
   Agree any breaking contract change before implementation. Add resolver
   regressions and strict real-ROM boot/behaviour checks after agreement.

## Scope under review

`crates/runtime-oric-atmos/src/{profiles,runtime,lib}.rs`,
`crates/emu198x-oric-atmos/src/app.rs`, existing runtime tests and
`crates/machine-oric-atmos/tests/bios_boot.rs`. Both 48K-class models have
64 KB physical DRAM; correct stale profile labels in the same change.
No CPU, ULA, renderer, chip pipeline or snapshot layout change is proposed.

The shared-launcher decision is binding: use the existing `FirmwareSource`,
`FirmwareRequirement`, `FirmwareSet` and variant builder. Do not add a
machine-specific resolver or hard-code ROM workspace variables in hardware.

## Reproduction commands

The retained probes use `/private/tmp/oric-firmware-audit` for their private
fixtures and output. Place the two hash-verified ROMs there. From the source
repository:

```sh
cargo build --release -p runtime-oric-atmos -p emu198x-shell -p machine-oric-atmos
rustc --edition=2024 -C opt-level=3 -C lto=thin \
  ../docs/plans/2026-10-10-oric1-firmware/probe.rs \
  -L dependency=target/release/deps \
  --extern runtime_oric_atmos=target/release/libruntime_oric_atmos.rlib \
  --extern emu198x_shell=target/release/libemu198x_shell.rlib \
  -o /private/tmp/oric-firmware-audit/probe
env -u EMU198X_ORIC_ROM -u EMU198X_ORIC_ROM_DIR \
  /private/tmp/oric-firmware-audit/probe
rustc --edition=2024 -C opt-level=3 -C lto=thin \
  ../docs/plans/2026-10-10-oric1-firmware/behaviour.rs \
  -L dependency=target/release/deps \
  --extern machine_oric_atmos=target/release/libmachine_oric_atmos.rlib \
  -o /private/tmp/oric-firmware-audit/behaviour
/private/tmp/oric-firmware-audit/behaviour
/private/tmp/oric-firmware-audit/behaviour --wrong-rom
```

Expected exits on the recorded source: 1, 0, 101 for the three probe runs.
The profile probe deliberately demonstrates the current bug; after the fix,
replace its assumption that generic-only lookup succeeds with a regression
requiring a missing-firmware error for Oric-1 and a working Atmos boot.
