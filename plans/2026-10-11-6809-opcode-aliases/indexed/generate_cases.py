"""Generate the complete, bounded MC6809 indexed-RMW diagnostic matrix."""

import itertools
import sys
from pathlib import Path

LOW5 = {
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    8,
    9,
    11,
    12,
    13,
    17,
    19,
    20,
    21,
    22,
    24,
    25,
    27,
    28,
    29,
    31,
}
posts = [p for p in range(256) if p < 128 or p & 31 in LOW5]
assert len(posts) == 220
ops = [0x60, 0x63, 0x64, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x6C, 0x6D, 0x6F]
# A, B, CC, DP, X, Y, U, S
seeds = [
    (0, 0, 0, 0x50, 0x5010, 0x6030, 0x7040, 0x8050),
    (1, 0xFF, 1, 0, 0, 0xFFFF, 0x7FFF, 0x8000),
    (0xFF, 1, 0xFE, 0xFF, 0x4001, 0x4002, 0xFFFF, 0),
    (0x80, 0x7F, 0xFF, 0x55, 0x1234, 0x5678, 0x9ABC, 0xDEF0),
]
rows = []
for op, post, offset, seed, pc in itertools.product(
    ops, posts, [0, 1, 0x7FFF, 0x8000, 0xFFFF], seeds, [0x4000, 0xFFFF]
):
    values = (op, post, offset >> 8, offset & 255, *seed, pc)
    assert len(values) == 13
    rows.append(" ".join(f"{v:04x}" for v in values))
assert len(rows) == len(set(rows)) == 96800
Path(sys.argv[1]).write_text("\n".join(rows) + "\n")
