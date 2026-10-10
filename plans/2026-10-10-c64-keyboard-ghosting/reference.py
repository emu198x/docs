"""Compile the vendored VICE functions unchanged and record a 2x2 matrix sweep."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vice-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    path = args.vice_source / "src/c64/c64cia1.c"
    source = path.read_text()
    begin = source.index("static void matrix_activate_column(")
    end = source.index("static void read_ciaicr(", begin)
    wrapper = (
        r"""
#include <stdint.h>
#include <stdio.h>
#define CIA_PRA 0
#define CIA_PRB 1
#define CIA_DDRA 2
#define CIA_DDRB 3
#define JOYPORT_1 0
#define JOYPORT_2 1
#define DBGA(x) ((void)0)
#define DBGB(x) ((void)0)
typedef struct { uint8_t c_cia[4], old_pa, old_pb; } cia_context_t;
static int c64keyboard_active = 1;
static uint8_t keyarr[8], rev_keyarr[8], joy[2];
static int keyboard_get_shiftlock(void) { return 0; }
static uint8_t read_joyport_dig(int port) { return joy[port]; }
"""
        + source[begin:end]
        + r"""
int main(void) {
    uint8_t input[14];
    while (fread(input, 1, sizeof input, stdin) == sizeof input) {
        cia_context_t c = {{input[8], input[9], input[10], input[11]}, 0, 0};
        c.old_pa = input[8] | (uint8_t)~input[10];
        c.old_pb = input[9] | (uint8_t)~input[11];
        joy[0] = input[12]; joy[1] = input[13];
        for (int col = 0; col < 8; ++col) {
            rev_keyarr[col] = 0;
            for (int row = 0; row < 8; ++row) {
                keyarr[row] = input[row];
                if (input[row] & (1 << col)) rev_keyarr[col] |= 1 << row;
            }
        }
        putchar(read_ciapa(&c)); putchar(read_ciapb(&c));
    }
    return ferror(stdin) || ferror(stdout);
}
"""
    )
    c_file = args.output / "vice-matrix.c"
    c_file.write_text(wrapper)
    binary = args.output / "vice-matrix"
    subprocess.run(
        [
            "cc",
            "-std=c99",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            str(c_file),
            "-o",
            str(binary),
        ],
        check=True,
    )
    inputs = bytearray()
    for keys in range(16):
        rows = [keys & 3, (keys >> 2) & 3, 0, 0, 0, 0, 0, 0]
        # Per PA0, PA1, PB0, PB1: input, output-low, output-high.
        for states in itertools.product(range(3), repeat=4):
            pra, prb, ddra, ddrb = 255, 255, 0, 0
            for pin, state in enumerate(states):
                bit = 1 << (pin % 2)
                if pin < 2:
                    ddra |= bit if state else 0
                    pra &= ~bit if state == 1 else 255
                else:
                    ddrb |= bit if state else 0
                    prb &= ~bit if state == 1 else 255
            for joy_a in range(4):
                for joy_b in range(4):
                    inputs.extend(
                        [*rows, pra, prb, ddra, ddrb, 255 ^ joy_b, 255 ^ joy_a]
                    )
    result = subprocess.run(
        [str(binary)], input=inputs, capture_output=True, check=True
    )
    assert len(inputs) == 20736 * 14 and len(result.stdout) == 20736 * 2
    fixture = args.output / "vice-matrix-2x2.bin"
    fixture.write_bytes(result.stdout)
    (args.output / "identity.json").write_text(
        json.dumps(
            {
                "cases": 20736,
                "vice_source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "extracted_functions_sha256": hashlib.sha256(
                    source[begin:end].encode()
                ).hexdigest(),
                "harness_sha256": hashlib.sha256(c_file.read_bytes()).hexdigest(),
                "fixture_sha256": hashlib.sha256(result.stdout).hexdigest(),
                "inputs_sha256": hashlib.sha256(inputs).hexdigest(),
                "compiler": subprocess.check_output(
                    ["cc", "--version"], text=True
                ).splitlines()[0],
                "scope": "Ordinary keys, no SHIFT LOCK; no timer outputs; digital pins and VICE contention rules, not an analogue simulation.",
            },
            indent=2,
        )
        + "\n"
    )
    print(f"Recorded {len(result.stdout) // 2} reference cases")


if __name__ == "__main__":
    main()
