"""Build an original MMC5 observation cartridge with installed cc65 tools."""

import argparse
import hashlib
import subprocess
from pathlib import Path

# Original five-column glyphs, seven rows each, placed in the low bitplane.
GLYPHS = {
    "0": "0E11131519110E",
    "1": "040C040404040E",
    "2": "0E11010204081F",
    "3": "1E01010E01011E",
    "4": "02060A121F0202",
    "5": "1F10101E01011E",
    "6": "0E10101E11110E",
    "7": "1F010204080808",
    "8": "0E11110E11110E",
    "9": "0E11110F01010E",
    "A": "0E11111F111111",
    "B": "1E11111E11111E",
    "C": "0E11101010110E",
    "D": "1E11111111111E",
    "E": "1F10101E10101F",
    "F": "1F10101E101010",
    "G": "0E11101711110F",
    "H": "1111111F111111",
    "I": "0E04040404040E",
    "J": "0702020212120C",
    "K": "11121418141211",
    "L": "1010101010101F",
    "M": "111B1515111111",
    "N": "11191915131311",
    "O": "0E11111111110E",
    "P": "1E11111E101010",
    "Q": "0E11111115120D",
    "R": "1E11111E141211",
    "S": "0F10100E01011E",
    "T": "1F040404040404",
    "U": "1111111111110E",
    "V": "11111111110A04",
    "W": "11111115151B11",
    "X": "11110A040A1111",
    "Y": "11110A04040404",
    "Z": "1F01020408101F",
    ":": "00040400040400",
    "-": "0000001F000000",
    "/": "01010204081010",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source = Path(__file__).resolve().parent
    args.output.mkdir(parents=True, exist_ok=True)
    obj = args.output / "observe.o"
    prg_file = args.output / "observe.prg"
    subprocess.run(["ca65", str(source / "observe.s"), "-o", str(obj)], check=True)
    subprocess.run(
        [
            "ld65",
            "-C",
            str(source / "observe.cfg"),
            str(obj),
            "-o",
            str(prg_file),
            "-Ln",
            str(args.output / "observe.labels"),
        ],
        check=True,
    )
    prg = prg_file.read_bytes()
    if len(prg) != 8192:
        raise ValueError(f"Expected one 8 KiB PRG window, got {len(prg)}")

    font = bytearray(8192)
    for char, rows in GLYPHS.items():
        pixels = bytes.fromhex(rows)
        if len(pixels) != 7 or any(row > 31 for row in pixels):
            raise ValueError(f"Invalid glyph {char}")
        offset = ord(char) * 16
        font[offset : offset + 7] = bytes(row << 2 for row in pixels)
    chr_rom = font * 32
    for page in range(256):
        chr_rom[page * 1024] = page
        chr_rom[page * 1024 + 1] = page ^ 255
    header = b"NES\x1a" + bytes([2, 32, 0x50, 0]) + bytes(8)
    image = header + bytes([255]) * 24576 + prg + chr_rom
    output = args.output / "mmc5-chr-observe.nes"
    output.write_bytes(image)
    print(f"{hashlib.sha256(image).hexdigest()}  {output}")


if __name__ == "__main__":
    main()
