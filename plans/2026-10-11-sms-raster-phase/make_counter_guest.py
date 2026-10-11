import sys
from pathlib import Path

reload = int(sys.argv[1])
out = Path(sys.argv[2])
delay = int(sys.argv[3])
assert 0 <= reload <= 255 and 0 <= delay <= 32
rom = bytearray(32768)
rom[:3] = bytes([0xC3, 0, 1])  # JP $0100
# ISR: record V count and status in RAM rings, then alternate backdrop colours.
isr = (
    bytes([0xF5, 0xE5])
    + bytes([0] * delay)
    + bytes(
        [
            0x3E,
            0,
            0xD3,
            0x3F,  # TH output low
            0x3E,
            0x22,
            0xD3,
            0x3F,  # TH input, high: latch in both references
            0xDB,
            0x7F,
            0x32,
            4,
            0xC0,  # capture H first
            0xDB,
            0x7E,
            0x32,
            5,
            0xC0,  # then V
            0x3A,
            0,
            0xC0,
            0x6F,
            0x26,
            0xC1,  # ring index
            0x3A,
            5,
            0xC0,
            0x77,  # V at C100+index
            0x26,
            0xC2,
            0xDB,
            0xBF,
            0x77,  # status/ack at C200+index
            0x26,
            0xC3,
            0x3A,
            4,
            0xC0,
            0x77,  # H at C300+index
            0x7D,
            0x3C,
            0x32,
            0,
            0xC0,  # next ring entry
            0xE1,
            0xF1,
            0xFB,
            0xED,
            0x4D,
        ]
    )
)
rom[0x38 : 0x38 + len(isr)] = isr
c = bytearray([0xF3, 0x31, 0xF0, 0xDF])  # DI; SP=DFF0
# Clear IRQ observation rings; RAM writes through real guest instructions.
c += bytes([0xAF, 0x21, 0, 0xC0, 0x11, 1, 0xC0, 0x01, 0xFF, 3, 0x77, 0xED, 0xB0])


def output(port, value):
    c.extend([0x3E, value, 0xD3, port])


def reg(n, value):
    output(0xBF, value)
    output(0xBF, 0x80 | n)


reg(0, 4)
reg(1, 0)
reg(2, 0x0E)
reg(5, 0x7E)
reg(7, 1)
reg(8, 0)
reg(9, 0)
reg(10, reload)
# Zero 16 KB VRAM. Preserve BC around the CPU-loop decrement test.
output(0xBF, 0)
output(0xBF, 0x40)
c += bytes([0x01, 0, 0x40])
loop = 0x100 + len(c)
c += bytes([0xAF, 0xD3, 0xBE, 0x0B, 0x78, 0xB1, 0xC2, loop & 255, loop >> 8])
# Stop sprite list at first entry.
output(0xBF, 0)
output(0xBF, 0x7F)
output(0xBE, 0xD0)
# Backdrop palette entries 17=red,18=green.
output(0xBF, 17)
output(0xBF, 0xC0)
output(0xBE, 3)
output(0xBE, 12)
reg(1, 0x40)
c += bytes([0xDB, 0xBF])
reg(0, 0x14)
c += bytes([0xED, 0x56, 0xFB])
halt = 0x100 + len(c)
c += bytes([0x76, 0xC3, halt & 255, halt >> 8])
rom[0x100 : 0x100 + len(c)] = c
rom[0x7FF0:0x7FF8] = b"TMR SEGA"
rom[0x7FFF] = 0x4C  # export SMS,32KB
checksum = sum(rom[:0x7FF0]) & 65535
rom[0x7FFA:0x7FFC] = checksum.to_bytes(2, "little")
out.write_bytes(rom)
print(
    f"guest reload={reload} setup_bytes={len(c)} isr_bytes={len(isr)} checksum={checksum:04x}"
)
