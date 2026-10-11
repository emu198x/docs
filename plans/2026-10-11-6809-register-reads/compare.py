"""Compare the 3,264 register-instruction diagnostic cases without hiding limits."""

import itertools
import json
import sys
from collections import Counter
from pathlib import Path

OPCODES = [0x12, 0x1B, 0x19, 0x1A, 0x1C, 0x1D, 0x3A, 0x3D] + [
    base + low
    for base in (0x40, 0x50)
    for low in (0, 1, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 15)
]
VALUES = [0, 1, 9, 0x10, 0x7F, 0x80, 0xFE, 0xFF]
FLAGS = [0, 1, 0xFE, 0xFF]
PCS = [0x4000, 0xFFFE, 0xFFFF]


def compare(reference: Path, actual: Path) -> dict:
    refs = reference.read_text().splitlines()
    results = actual.read_text().splitlines()
    header = "opcode value cc pc cycles a b result_cc result_pc memory result_x trace"
    if not refs or refs[0] != header or not results or results[0] != header + " halted":
        raise ValueError("missing or wrong header")
    expected_keys = list(itertools.product(OPCODES, VALUES, FLAGS, PCS))
    if len(refs) != len(results) or len(refs) != len(expected_keys) + 1:
        raise ValueError("missing diagnostic rows")
    counts = Counter(cases=0, qualified_cases=0, qualified_mismatches=0)
    by_opcode = {}
    examples = {}
    for key, ref, result in zip(expected_keys, refs[1:], results[1:], strict=True):
        expected, observed = ref.split(), result.split()
        if len(expected) != 12 or len(observed) != 13:
            raise ValueError("wrong result arity")
        if (
            tuple(int(v, 16) for v in expected[:4]) != key
            or observed[:4] != expected[:4]
        ):
            raise ValueError("wrong, duplicate or out-of-order input key")
        for fields in (expected, observed):
            if len(fields[11].split(",")) != int(fields[4]):
                raise ValueError("cycle/event count disagreement")
        opcode = key[0]
        counts["cases"] += 1
        cohort = by_opcode.setdefault(f"{opcode:02x}", Counter(cases=0))
        cohort["cases"] += 1
        differences = []
        for label, first, last in [
            ("cycles", 4, 5),
            ("registers", 5, 9),
            ("memory", 9, 10),
            ("x", 10, 11),
            ("bus", 11, 12),
        ]:
            if observed[first:last] != expected[first:last]:
                counts[label] += 1
                cohort[label] += 1
                differences.append(label)
        if observed[-1] != "false":
            counts["halted"] += 1
            differences.append("halted")
        if differences:
            examples.setdefault(f"{opcode:02x}", {"expected": ref, "actual": result})
        qualified = opcode not in (0x4D, 0x5D)
        if qualified:
            counts["qualified_cases"] += 1
            ev, av = expected[4:].copy(), observed[4:-1].copy()
            if opcode == 0x19:
                ev[3] = f"{int(ev[3], 16) & ~2:02x}"
                av[3] = f"{int(av[3], 16) & ~2:02x}"
            if ev != av or observed[-1] != "false":
                counts["qualified_mismatches"] += 1
    return {"counts": counts, "by_opcode": by_opcode, "examples": examples}


if __name__ == "__main__":
    print(json.dumps(compare(Path(sys.argv[1]), Path(sys.argv[2])), indent=2))
