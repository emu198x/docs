"""Validate native transient images, controls and exact source-bit predictions."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import itertools
import json
from pathlib import Path

from bank_transient import SCENARIOS, guest, pixels
from capture import MODELS, digest


def verify(data: dict, root: Path) -> dict:
    names = [m[0] for m in MODELS]
    expected = {
        f"{model}-{pair[0]}-{pair[1]}-marker{marker:02x}-glue{glue}"
        for model, (pair, marker), glue in itertools.product(names, SCENARIOS, (0, 1))
    }
    captures = data["captures"]
    assert len(captures) == 70 and {r["stem"] for r in captures} == expected
    for row in captures:
        assert digest(root / (row["stem"] + ".png")) == row["image_sha256"]
    indexed = {r["stem"]: r for r in captures}
    keys = [(r["model"], tuple(r["pair"]), r["marker"]) for r in data["comparisons"]]
    # Explicit flattening prevents accidentally comparing differently-shaped tuples.
    assert len(keys) == 35 and set(keys) == {
        (m, p, v) for m, (p, v) in itertools.product(names, SCENARIOS)
    }
    for row in data["comparisons"]:
        model, pair, marker = row["model"], row["pair"], row["marker"]
        images = []
        for glue in (0, 1):
            stem = f"{model}-{pair[0]}-{pair[1]}-marker{marker:02x}-glue{glue}"
            assert (
                indexed[stem]["program_sha256"]
                == hashlib.sha256(guest(tuple(pair), marker)).hexdigest()
            )
            size, image = pixels(root / (stem + ".png"))
            assert size == (384, 272 if model in ("pal", "c64c") else 247)
            assert list(size) == row["size"]
            assert len({image[i : i + 3] for i in range(0, len(image), 3)}) >= 2
            images.append(image)
        changed = [
            i // 3
            for i in range(0, len(images[0]), 3)
            if images[0][i : i + 3] != images[1][i : i + 3]
        ]
        assert changed == row["pixel_indices"] and len(changed) == row["differences"]
        assert bool(changed) == (pair == [1, 2]), (model, pair, marker, len(changed))
    effects = []
    for model in names:
        images = {
            g: {
                m: pixels(root / f"{model}-1-2-marker{m:02x}-glue{g}.png")[1]
                for m in (0, 85, 170, 255)
            }
            for g in (0, 1)
        }
        assert all(v == images[0][0] for v in images[0].values()), (
            "discrete glue must ignore bank 3"
        )
        black, white = images[1][0], images[1][255]
        mask = [
            i // 3
            for i in range(0, len(black), 3)
            if black[i : i + 3] != white[i : i + 3]
        ]
        assert len(mask) > 0, "custom glue must fetch the unselected bank's character"
        for marker in (85, 170):
            actual = images[1][marker]
            for i in range(0, len(actual), 3):
                bit = (marker >> (7 - ((i // 3) % 384) % 8)) & 1
                expected_rgb = (white if bit else black)[i : i + 3]
                assert actual[i : i + 3] == expected_rgb, (model, marker, i // 3)
        effects.append(
            {"model": model, "bank3_pixels": len(mask), "marker_prediction_errors": 0}
        )
    return {
        "captures": 70,
        "paired_comparisons": 35,
        "no_transient_controls": 15,
        "effects": effects,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    raw = (args.root / "comparison.json.gz").read_bytes()
    print(json.dumps(verify(json.loads(gzip.decompress(raw)), args.root), indent=2))


if __name__ == "__main__":
    main()
