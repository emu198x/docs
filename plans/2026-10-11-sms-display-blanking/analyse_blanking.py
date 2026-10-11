"""Verify the active-picture controls and measure both engines' blanking transitions."""

import csv
from collections import Counter
from pathlib import Path

from PIL import Image

root = Path(__file__).resolve().parent
red, green, blue = (255, 0, 0), (0, 255, 0), (0, 0, 255)
rows = []
for region in ["ntsc-u", "pal"]:
    pictures = {}
    for engine in ["emu", "reference"]:
        for guest in ["on", "off", "toggle0", "toggle8", "toggle16", "toggle24"]:
            prefix = root / f"{engine}-{region}-{guest}"
            ram = prefix.with_suffix(".ram").read_bytes()
            assert len(ram) == 8192 and ram[0] == 0xA5 and ram[1] >= 40
            image_path = prefix.with_suffix(".ppm")
            if not image_path.exists():
                image_path = prefix.with_suffix(".png")
            original = Image.open(image_path)
            original.save(prefix.with_suffix(".png"))
            # VdpRegion::border_left/border_top at 192 lines, checked against
            # exact framebuffer dimensions and the full always-on reference.
            if engine == "emu":
                x, y, w, h = (
                    (12, 25, 280, 240) if region == "ntsc-u" else (10, 51, 277, 288)
                )
                assert original.size == (w, h)
                picture = original.crop((x, y, x + 256, y + 192))
            else:
                assert original.size == (256, 192)
                picture = original
            pixels = list(picture.get_flattened_data())
            assert set(pixels) <= {red, green, blue}
            pictures[(engine, guest)] = pixels
            if guest == "off":
                assert pixels == [blue] * (256 * 192)
            if guest == "on":
                assert Counter(pixels) == Counter({red: 48640, green: 512})
            if guest.startswith("toggle"):
                mixed = [
                    y
                    for y in range(192)
                    if blue in pixels[y * 256 : (y + 1) * 256]
                    and red in pixels[y * 256 : (y + 1) * 256]
                ]
                for line in mixed:
                    row = pixels[line * 256 : (line + 1) * 256]
                    first_blue = row.index(blue)
                    late_green = sum(pixel == green for pixel in row[first_blue:])
                    rows.append(
                        {
                            "engine": engine,
                            "region": region,
                            "delay": int(guest[6:]),
                            "line": line,
                            "first_blue": first_blue,
                            "green_after_blue": late_green,
                        }
                    )
                if engine == "reference":
                    assert not mixed
                    rows.append(
                        {
                            "engine": engine,
                            "region": region,
                            "delay": int(guest[6:]),
                            "line": "none",
                            "first_blue": "none",
                            "green_after_blue": 0,
                        }
                    )
                else:
                    assert len(mixed) == 2, (region, guest, mixed)
    for guest in ["on", "off"]:
        assert pictures[("emu", guest)] == pictures[("reference", guest)], (
            region,
            guest,
        )
assert len(rows) == 24
with (root / "summary.csv").open("w") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0])
    writer.writeheader()
    writer.writerows(rows)
for row in rows:
    print(row)
print("24 completed runs; both 49,152-pixel controls match in both regions")
