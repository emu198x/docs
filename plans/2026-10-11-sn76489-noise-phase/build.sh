#!/bin/sh
set -eu
: "${XROAR:?Set XROAR to the recorded reference checkout}"
: "${ARES:?Set ARES to the recorded reference checkout}"
: "${PSG_BUILD:?Set PSG_BUILD to the recorded Cargo debug directory}"
cc -std=c11 -O2 -Wall -Wextra -Werror -ffunction-sections \
  -I "$XROAR" -I "$XROAR/src" -I "$XROAR/portalib" \
  collision.c "$XROAR/src/filter.c" -Wl,-dead_strip -o collision
./collision > collision-regenerated.csv
cmp collision.csv collision-regenerated.csv
c++ -std=c++20 -O2 -I include -I "$ARES/ares" -I "$ARES/nall" \
  -I "$ARES/ares/component/audio/sn76489" ares.cpp -Wl,-dead_strip -o ares
./ares > ares-regenerated.csv
cmp ares.csv ares-regenerated.csv
rustc --edition=2024 probe.rs --extern "ti_sn76489=$PSG_BUILD/libti_sn76489.rlib" \
  -L "dependency=$PSG_BUILD/deps" -o probe
./probe > baseline-regenerated.csv
cmp baseline.csv baseline-regenerated.csv
python3 check.py
