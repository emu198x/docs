"""Original SG-1000 cartridge: continuously capture both controller ports."""
from pathlib import Path


def cartridge() -> bytes:
    # DI; IN A,($DC); LD ($C000),A; IN A,($DD); LD ($C001),A;
    # LD A,($C002); INC A; LD ($C002),A; JP $0001.
    code = bytes([
        0xF3, 0xDB, 0xDC, 0x32, 0, 0xC0, 0xDB, 0xDD, 0x32, 1, 0xC0,
        0x3A, 2, 0xC0, 0x3C, 0x32, 2, 0xC0, 0xC3, 1, 0,
    ])
    return code + bytes(32768 - len(code))


if __name__ == "__main__":
    Path("input.sg").write_bytes(cartridge())
