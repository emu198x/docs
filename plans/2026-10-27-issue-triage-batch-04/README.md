# Einstein malformed DSK reproducer

Source: Emu198x `2e90d5986286f637380ea287bca9e7363df3be7b`.

`einstein_dsk.rs` uses only the public `machine_tatung_einstein::Einstein`
API and synthetic bytes. In a disposable checkout at that revision, place it
at `crates/machine-tatung-einstein/tests/triage_dsk.rs`, then run:

```sh
cargo test --locked -p machine-tatung-einstein --test triage_dsk -- --nocapture
```

The valid one-track EDSK control parses. Three bounded mutations expose two
panics and one false acceptance; the final assertion exits 101. No large
allocation/OOM case is attempted. The retained original run used an external
Cargo harness with a path dependency on this same crate; every non-harness
package version/source/checksum was verified against that checkout's lockfile.
The raw log includes the caught panics and the final intended failing assertion.
This is evidence for #277, not a production fix or a passing accuracy gate.
