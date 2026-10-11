#!/bin/sh
set -eu
: "${MEMU:?Path to the read-only MEMU checkout}"
: "${EMU198X:?Path to the Emu198x source checkout}"
cc -std=c11 -O2 -Wall -Wextra -Werror -DLSB_FIRST \
  -I "$MEMU/src/memu" -I "$MEMU/src/Z80" \
  memu_ctc_probe.c "$MEMU/src/memu/ctc.c" -o /tmp/198x-memu-ctc-probe
/tmp/198x-memu-ctc-probe > /tmp/198x-memu-ctc.csv
cmp memu-ctc.csv /tmp/198x-memu-ctc.csv
cd "$EMU198X"
cargo test -p machine-memotech-mtx --test vdp_ctc_interrupt -- --nocapture
cargo test -p machine-memotech-mtx -p runtime-memotech-mtx -p zilog-z80-ctc
cargo clippy -p machine-memotech-mtx -p runtime-memotech-mtx -p zilog-z80-ctc --all-targets -- -D warnings
