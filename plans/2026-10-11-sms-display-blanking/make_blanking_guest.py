"""Original SMS guest: opaque background and sprites across a display-disable write."""

import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("output", type=Path)
parser.add_argument("mode", choices=["toggle", "on", "off"])
parser.add_argument("delay", type=int)
args = parser.parse_args()
assert 0 <= args.delay <= 24
rom = bytearray(32768)
rom[:3] = bytes([0xC3, 0, 1])
c = bytearray([0xF3, 0x31, 0xF0, 0xDF])  # DI; SP=$DFF0


def output(port: int, value: int) -> None:
    c.extend([0x3E, value, 0xD3, port])


def reg(index: int, value: int) -> None:
    output(0xBF, value)
    output(0xBF, 0x80 | index)


def addr(address: int, command: int) -> None:
    output(0xBF, address & 255)
    output(0xBF, (address >> 8) | command)


def wait_v(value: int) -> None:
    loop = 0x100 + len(c)
    c.extend([0xDB, 0x7E, 0xFE, value, 0xC2, loop & 255, loop >> 8])


for index, value in [
    (0, 4),
    (1, 0),
    (2, 0x0E),
    (3, 0xFF),
    (4, 7),
    (5, 0xFF),
    (6, 3),
    (7, 1),
    (8, 0),
    (9, 0),
    (10, 255),
]:
    reg(index, value)
addr(0, 0x40)
c.extend([0x01, 0, 0x40])  # BC=$4000
loop = 0x100 + len(c)
c.extend([0xAF, 0xD3, 0xBE, 0x0B, 0x78, 0xB1, 0xC2, loop & 255, loop >> 8])
addr(0, 0x40)
for byte in [255, 0, 0, 0] * 8 + [0, 255, 0, 0] * 8:
    output(0xBE, byte)
addr(0x3F00, 0x40)
for byte in [63] * 8 + [0xD0]:
    output(0xBE, byte)
addr(0x3F80, 0x40)
for x in range(0, 256, 32):
    output(0xBE, x)
    output(0xBE, 1)
addr(0, 0xC0)
for index in range(32):
    output(0xBE, {1: 3, 17: 0x30, 18: 0x0C}.get(index, 0))
c.extend([0x3E, 0xA5, 0x32, 0, 0xC0, 0xAF, 0x32, 1, 0xC0])
reg(1, 0 if args.mode == "off" else 0x40)
repeat = 0x100 + len(c)
wait_v(32)
wait_v(64)
c.extend([0] * args.delay)
if args.mode == "toggle":
    reg(1, 0)
wait_v(80)
if args.mode == "toggle":
    reg(1, 0x40)
c.extend([0x3A, 1, 0xC0, 0x3C, 0x32, 1, 0xC0, 0xC3, repeat & 255, repeat >> 8])
assert len(c) < 0x3000
rom[0x100 : 0x100 + len(c)] = c
rom[0x7FF0:0x7FF8] = b"TMR SEGA"
rom[0x7FFF] = 0x4C
checksum = sum(rom[:0x7FF0]) & 65535
rom[0x7FFA:0x7FFC] = checksum.to_bytes(2, "little")
args.output.write_bytes(rom)
print(
    f"mode={args.mode} delay={args.delay} code_bytes={len(c)} checksum={checksum:04x}"
)
