# Publish outstanding releases

Lane: engineering-frontier release work. User authorised publication of all
outstanding ready releases on 2026-11-05.

1. Audit open release PRs and registry versions across the active tooling
   siblings. Preserve unrelated branches, drafts and workspaces.
2. Review Emu198x release PR #2303 against main: only generated suite version,
   lockfile and changelog changes; require all checks green on the exact head.
   Merge through the normal rebase policy and verify its tag/source identity.
3. Dispatch the existing Emu198x crate publisher for positively absent versions.
   Follow publication and inspect the actual registry archive and checksum.
4. Follow the tagged native release through archive and installation
   qualification, Homebrew publication and automatic npm publication. Verify
   public assets/checksums and npm build revision/integrity against the tag.
5. Record public versions, immutable source/run identities and evidence here;
   push the record and remove task-owned downloads and temporary output.

Use existing publication workflows, independent library versions and suite
version policy. Do not merge unrelated development PRs or retarget released tags.

## Release audit and source verification

No open release PRs exist in Play198x, Format198x, Build198x, Asm198x,
Isa198x, Debug198x or AMOS. Their existing releases remain published.
The registry audit checked 104 candidate manifests: 99 current versions are
already published. The absent Asm verdict-corpus is explicitly non-shipping
in its manifest; Build198x ships its CLI via existing GitHub archives (0.2.13
already released). AMOS parser 0.1.0 is separate from its already published
highlighting previews and has no prepared Rust release. These are not pending
publication jobs. Emu198x positively discovers its publishable members and
has two absent versions: ESP-AT modem and Game Boy PPU.

Release PR #2303 passed all checks on `70ec0d8b206fd223865f276c0cd1d6d9ecc257aa`.
Its only changes are the suite version, changelog and 262 lockfile package
versions (0.48.2 to 0.48.3); package dependencies and checksums are unchanged.
Merged as `32c46c10f2b4777ad63d4d12f1ac9b65451c731c`. Both trees equal
`3c782928e3ad767b83350ab1d3ba48da33dcc0ac`; tag v0.48.3 points to that merge.

Crate publication run: 42040725827. Tagged release run: 42040767564.
Cancelled duplicate main packaging run 42040726194; the complete tagged
release qualification remains enabled.

Crate publication run 42040725827 succeeded. Downloaded both new `.crate`
archives directly from the registry; their SHA-256 values match the registry
metadata, and each `src/lib.rs` is byte-identical to tag v0.48.3. The PPU
archive positively contains the final-line LY correction. Exact hashes and
publication times are in `2026-11-05-publish-outstanding-crates.json`.
Published: emu198x-esp-at-modem 0.48.3 and emu198x-nintendo-game-boy-ppu 0.1.1.
All other discovered current Emu198x library versions were already present.
