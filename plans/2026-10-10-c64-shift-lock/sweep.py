"""Sweep the SHIFT LOCK probe's compiled VICE oracle on PA1/2 and PB1/7."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    inputs = bytearray()
    for locked in (0, 1):
        for keys in range(16):
            rows = [0] * 8
            for pin in range(4):
                if keys & (1 << pin):
                    rows[1 + pin // 2] |= 1 << (1 if pin % 2 == 0 else 7)
            if locked:
                rows[1] |= 0x80
            for states in itertools.product(range(3), repeat=4):
                pra, prb, ddra, ddrb = 255, 255, 0, 0
                for pin, state in enumerate(states):
                    bit = 1 << [1, 2, 1, 7][pin]
                    if pin < 2:
                        ddra |= bit if state else 0
                        pra &= ~bit if state == 1 else 255
                    else:
                        ddrb |= bit if state else 0
                        prb &= ~bit if state == 1 else 255
                # Joysticks have only bits 0..4: PB7 cannot be grounded by one.
                for joy_a in range(4):
                    for joy_b in range(2):
                        inputs.extend(
                            [
                                *rows,
                                pra,
                                prb,
                                ddra,
                                ddrb,
                                255 ^ (joy_b << 1),
                                255 ^ (joy_a << 1),
                                locked,
                            ]
                        )
    result = subprocess.run(
        [str(args.oracle)], input=inputs, capture_output=True, check=True
    )
    assert len(inputs) == 20736 * 15 and len(result.stdout) == 20736 * 2
    fixture = args.output / "vice-shift-lock.bin"
    fixture.write_bytes(result.stdout)
    half = len(result.stdout) // 2
    differences = sum(
        result.stdout[i : i + 2] != result.stdout[half + i : half + i + 2]
        for i in range(0, half, 2)
    )
    assert differences > 0, "Lock flag must affect the oracle"
    (args.output / "identity.json").write_text(
        json.dumps(
            {
                "cases": 20736,
                "lock_changes_output": differences,
                "fixture_sha256": hashlib.sha256(result.stdout).hexdigest(),
                "inputs_sha256": hashlib.sha256(inputs).hexdigest(),
                "oracle_sha256": hashlib.sha256(args.oracle.read_bytes()).hexdigest(),
                "generator_sha256": hashlib.sha256(
                    Path(__file__).read_bytes()
                ).hexdigest(),
            },
            indent=2,
        )
        + "\n"
    )
    print(f"20736 reference pairs; locking changes {differences} pairs")


if __name__ == "__main__":
    main()
