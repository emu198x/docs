# Prepared hardware reference verification

`verify.py` compiles the unchanged upstream `makeref.c`, runs it on all four
physical PRG dumps, and compares every output byte against the native fixtures
and the references embedded in the R04 guest. It also runs the converter again
on each prepared payload with its PRG header restored, checking pass-through.

```sh
python3 verify.py --testbench "$HOME/.emu198x/test-suites/c64-vicii" \
  --source /path/to/Emu198x/emu198x --output /tmp/lightpen-preparation
```

`comparison.json` records all input hashes, changed bytes, embedded addresses
and pass-through results. `compiler.log` preserves the unmodified upstream C
source's unused-parameter warning. The compiler exits successfully.

`tests.log.gz` contains the complete Emu198x/native/prepared-hardware comparison
and the converter-parity test. `negative.log.gz` records rejection of a mutated
native fixture; `restored.log.gz` verifies the restored fixture. No golden
binary or raw physical dump was changed. `sha256.json` identifies this evidence.
