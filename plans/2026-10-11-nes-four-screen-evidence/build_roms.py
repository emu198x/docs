"""Generate original guest programs that exercise all four nametable pages."""

import json
import sys
from pathlib import Path


def cartridge(mapper: int, nes2: bool, four: bool, mirror: int) -> bytes:
    program = bytearray([0x78, 0xD8, 0xA2, 0xFF, 0x9A])  # SEI/CLD/LDX/TXS

    def write(addr: int, value: int) -> None:
        program.extend([0xA9, value, 0x8D, addr & 255, addr >> 8])

    def address(addr: int) -> None:
        program.extend([0x2C, 2, 0x20])  # BIT PPUSTATUS resets write toggle
        write(0x2006, addr >> 8)
        write(0x2006, addr & 255)

    write(0x2000, 0)
    write(0x2001, 0)
    write(0x4015, 0)
    program.extend([0x2C, 2, 0x20])
    program.extend([0x2C, 2, 0x20, 0x10, 0xFB] * 2)  # wait two fresh VBLANKs
    write(0xA000, mirror)
    for page, value in enumerate([17, 34, 51, 68]):
        address(0x2000 + page * 1024)
        write(0x2007, value)
    for page in range(4):
        address(0x2000 + page * 1024)
        program.extend([0xAD, 7, 0x20, 0xAD, 7, 0x20])  # discard, then read buffer
        program.extend([0x8D, page, 4])  # STA $0400+page
    write(0x04F1, 0xA5)
    stop = 0xE000 + len(program)
    program.extend([0x4C, stop & 255, stop >> 8])
    prg = bytearray(32768)
    prg[24576 : 24576 + len(program)] = program
    prg[-4:-2] = bytes([0, 0xE0])
    header = (
        b"NES\x1a"
        + bytes([2, 1, (mapper << 4) | 1 | (8 if four else 0), 8 if nes2 else 0])
        + bytes(8)
    )
    return header + prg + bytes(8192)


def main() -> None:
    output = Path(sys.argv[1])
    output.mkdir(parents=True, exist_ok=True)
    cases = []
    for mapper in [0, 4]:
        for nes2 in [False, True]:
            for four in [False, True]:
                for mirror in [0, 1]:
                    name = (
                        f"m{mapper}-nes2{int(nes2)}-four{int(four)}-mirror{mirror}.nes"
                    )
                    (output / name).write_bytes(cartridge(mapper, nes2, four, mirror))
                    expected = (
                        [17, 34, 51, 68]
                        if four
                        else (
                            [34, 34, 68, 68]
                            if mapper == 4 and mirror
                            else [51, 68, 51, 68]
                        )
                    )
                    cases.append(
                        {
                            "file": name,
                            "mapper": mapper,
                            "nes2": nes2,
                            "four_screen": four,
                            "mirror_write": mirror,
                            "expected": expected,
                        }
                    )
    (output / "cases.json").write_text(json.dumps(cases, indent=2) + "\n")


if __name__ == "__main__":
    main()
