"""Compile unchanged XRoar transfer bodies into a register-value-only oracle."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def body(source: str, marker: str) -> str:
    start = source.index(marker) + len(marker)
    depth = 1
    for at in range(start, len(source)):
        depth += (source[at] == "{") - (source[at] == "}")
        if depth == 0:
            return source[start:at]
    raise AssertionError("missing body end")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    args.output.mkdir(exist_ok=False)
    raw = args.source.read_bytes()
    source = raw.decode()
    exg = body(source, "case 0x031e: {")
    tfr = body(source, "case 0x031f: {")
    harness = (
        """#include <stdint.h>
#include <stdio.h>
#if __BYTE_ORDER__ != __ORDER_LITTLE_ENDIAN__
#error "The register alias wrapper requires a little-endian host."
#endif
static uint16_t rd,rx,ry,ru,rs,rpc;
static uint8_t rcc,rdp;
#define REG_D rd
#define REG_A (((uint8_t *)&rd)[1])
#define REG_B (((uint8_t *)&rd)[0])
#define REG_X rx
#define REG_Y ry
#define REG_U ru
#define REG_S rs
#define REG_PC rpc
#define REG_CC rcc
#define REG_DP rdp
#define byte_immediate(cpu) post
#define NVMA_CYCLE ((void)0)
struct Cpu { int nmi_armed; };
"""
        + "static void exg(unsigned post) { struct Cpu c={0}, *cpu=&c;\n"
        + exg
        + "\n}\n"
        + "static void tfr(unsigned post) { struct Cpu c={0}, *cpu=&c;\n"
        + tfr
        + "\n}\n"
        + """
int main(void) {
    const unsigned regs[]={0,1,2,3,4,5,8,9,10,11};
    const uint16_t seeds[][8] = {
        {1,2,3,4,0x1122,0x3344,0x5566,0x7788},
        {0x5a,0xa5,0x69,0x96,0xabcd,0xeffe,0x8421,0x1357},
        {0,0,0,0,0,0,0,0},
        {255,255,255,255,65535,65535,65535,65535}
    };
    puts("opcode post a b dp cc x y u s pc result_a result_b result_dp result_cc result_x result_y result_u result_s result_pc");
    for (unsigned seed=0;seed<4;seed++)
    for (unsigned opcode=0x1e;opcode<=0x1f;opcode++)
    for (unsigned i=0;i<10;i++)
    for (unsigned j=0;j<10;j++) {
        REG_A=seeds[seed][0]; REG_B=seeds[seed][1];
        REG_DP=seeds[seed][2]; REG_CC=seeds[seed][3];
        REG_X=seeds[seed][4]; REG_Y=seeds[seed][5];
        REG_U=seeds[seed][6]; REG_S=seeds[seed][7];
        REG_PC=0x4002;
        unsigned post=(regs[i]<<4)|regs[j];
        printf("%02x %02x",opcode,post);
        for(unsigned k=0;k<8;k++)printf(" %04x",seeds[seed][k]);
        printf(" 4000");
        if(opcode==0x1e)exg(post);else tfr(post);
        printf(" %04x %04x %04x %04x %04x %04x %04x %04x %04x\\n",REG_A,REG_B,REG_DP,REG_CC,REG_X,REG_Y,REG_U,REG_S,REG_PC);
    }
}
"""
    )
    c = args.output / "reference.c"
    c.write_text(harness)
    binary = args.output / "reference"
    subprocess.run(
        ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", str(c), "-o", str(binary)],
        check=True,
    )
    result = subprocess.run(
        [str(binary)], check=True, capture_output=True, text=True
    ).stdout
    lines = result.splitlines()
    assert len(lines) == 801 and all(len(l.split()) == 20 for l in lines[1:])
    (args.output / "transfers.txt").write_text(result)
    (args.output / "reference.json").write_text(
        json.dumps(
            {
                "source_sha256": hashlib.sha256(raw).hexdigest(),
                "wrapper_sha256": hashlib.sha256(c.read_bytes()).hexdigest(),
                "vectors_sha256": hashlib.sha256(result.encode()).hexdigest(),
                "cases": 800,
                "scope": "Unchanged compiled XRoar EXG/TFR switch bodies; named register values only; bus cycles and NMI state not compared.",
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
