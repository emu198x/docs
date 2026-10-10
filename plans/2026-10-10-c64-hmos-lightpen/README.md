# Light-pen correction evidence

[The plan](../2026-10-10-c64-hmos-lightpen.md) records the two corrected faults
and their verification. The native oracle establishes implementation parity;
it remains two LPX samples per model away from the upstream physical dumps.

- `before-*.bin`, `after-*.bin`, `native-*.bin` contain five 256-byte result
  pages (D011, D012, LPX, LPY, IRQ). No load-address prefix or ROM bytes.
- `native-comparison.json` retains the two physical-dump differences and
  exact native invocation per model. Native logs prove the guest completed.
- `before.log.gz` and `after.log.gz` compare against physical dumps and are
  both red. The latter deliberately retains the two unexplained native /
  physical disagreements. `strict.log.gz` is the final native-parity gate.
- `chip-before.log.gz` proves both directed faults before correction;
  `chip-final.log.gz` checks the fixed boundaries and suppression rule.
- `snapshot.log.gz`, `packages.log.gz`, `clippy-final.log.gz` retain the
  successful runtime replay, package suite and lint results.
- `negative.log.gz` records rejection of a deliberately mutated native fixture
  by its physical-comparison guard. The fixture was restored byte-for-byte.
- `identities.json` pins source/program/ROM identities. `sha256.json` pins
  all retained artifacts.

Run the native reproduction from the source repo, with a new output folder:

```sh
python3 ../docs/plans/2026-10-10-c64-hmos-lightpen/capture.py \
  --output /tmp/lightpen-native \
  --testbench "$HOME/.emu198x/test-suites/c64-vicii" \
  --roms "$HOME/.emu198x/roms/commodore-c64"

EMU198X_STRICT_FIXTURES=1 cargo test -p runtime-commodore-c64 --release \
  --test vicii_testbench light_pen_measurement_matches_native_reference \
  -- --ignored --nocapture
```

The primary hardware-dump observations, their upstream attribution and limits
are preserved privately in the shared reference library's
`by-topic/vic-ii/2026-lightpen-measurement-observations.md`. Input revision and
original capture dates remain unresolved; byte identities are recorded.
