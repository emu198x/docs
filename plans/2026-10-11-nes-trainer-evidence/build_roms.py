"""Original guests copy the cartridge trainer through the CPU bus."""

import json
from pathlib import Path


def build(mapper: int, nes2: bool, battery: bool, trainer: bool) -> bytes:
    header = bytearray(b"NES\x1a" + bytes(12))
    header[4:8] = bytes(
        [
            2,
            1,
            ((mapper << 4) & 255) | battery * 2 | trainer * 4,
            (mapper & 240) | nes2 * 8,
        ]
    )
    if nes2:
        header[10] = 0x70 if battery else 7
    program = bytearray([0x78, 0xD8, 0xA2, 0xFF, 0x9A])

    def write(address: int, value: int) -> None:
        program.extend([0xA9, value, 0x8D, address & 255, address >> 8])

    write(0x00FF, 0)
    write(0x2000, 0)
    write(0x2001, 0)
    write(0x4015, 0)
    if mapper == 4:
        write(0xA001, 0x80)
    if mapper == 68:
        write(0xF000, 0x10)
    for page in range(2):
        program.extend(
            [0xA2, 0, 0xBD, 0, 0x70 + page, 0x9D, 0, 4 + page, 0xE8, 0xD0, 0xF7]
        )
    write(0x00FF, 0xA5)
    stop = 0xE000 + len(program)
    program.extend([0x4C, stop & 255, stop >> 8])
    prg = bytearray(32768)
    prg[24576 : 24576 + len(program)] = program
    prg[-4:-2] = bytes([0, 0xE0])
    payload = bytes((i * 37 + 11) & 255 for i in range(512)) if trainer else b""
    return header + payload + prg + bytes(8192)


def main() -> None:
    root = Path(__file__).resolve().parent / "roms"
    root.mkdir(exist_ok=True)
    rows = []
    for mapper in [0, 1, 3, 4, 5, 34, 68]:
        for nes2 in [False, True]:
            for battery in [False, True]:
                for trainer in [False, True]:
                    name = f"m{mapper}-n{int(nes2)}-b{int(battery)}-t{int(trainer)}.nes"
                    (root / name).write_bytes(build(mapper, nes2, battery, trainer))
                    rows.append(
                        {
                            "file": name,
                            "mapper": mapper,
                            "nes2": nes2,
                            "battery": battery,
                            "trainer": trainer,
                        }
                    )
    (root / "cases.json").write_text(json.dumps(rows, indent=2) + "\n")


if __name__ == "__main__":
    main()
