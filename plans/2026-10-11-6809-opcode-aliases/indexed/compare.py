"""Compare complete indexed-RMW outputs, rejecting missing or malformed coverage."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

OPCODES = {
    "0060",
    "0063",
    "0064",
    "0066",
    "0067",
    "0068",
    "0069",
    "006a",
    "006c",
    "006d",
    "006f",
}
KINDS = (
    "halted",
    "cycle_count",
    "registers",
    "bus_trace",
    "write_effects",
    "write_timing",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def parse(line: str) -> tuple[str, list[str], list[str], str]:
    parts = [p.strip() for p in line.split("|")]
    require(len(parts) == 4, "expected four output sections")
    key, result, trace, halt = parts
    inputs = key.split()
    require(
        len(inputs) == 13 and all(re.fullmatch("[0-9a-f]{4}", x) for x in inputs),
        "invalid input key",
    )
    require(all(int(x, 16) <= 255 for x in inputs[:8]), "input byte out of range")
    fields = result.split()
    require(len(fields) == 10 and halt in {"0", "1"}, "invalid result fields")
    require(fields[0].isdigit(), "invalid cycle count")
    require(
        all(re.fullmatch("[0-9a-f]{2}", x) for x in fields[1:5]),
        "invalid byte register",
    )
    require(
        all(re.fullmatch("[0-9a-f]{4}", x) for x in fields[5:]), "invalid word register"
    )
    events = trace.split(",")
    require(
        len(events) == int(fields[0]) and 1 <= len(events) <= 32,
        "cycle/event count disagreement",
    )
    require(
        all(re.fullmatch("[rw][0-9a-f]{4}:[0-9a-f]{2}", e) for e in events),
        "invalid bus event",
    )
    return key, fields, events, halt


def compare(inputs: Path, reference: Path, actual: Path) -> dict:
    counts: Counter[str] = Counter(dict.fromkeys((*KINDS, "cases", "exact"), 0))
    by_opcode: dict[str, Counter[str]] = {}
    examples: dict[str, dict] = {}
    write_deltas: Counter[int] = Counter()
    seen: set[str] = set()
    with inputs.open() as cases, reference.open() as refs, actual.open() as results:
        for case, ref, result in zip(cases, refs, results, strict=True):
            ek, ev, et, eh = parse(ref)
            ak, av, at, ah = parse(result)
            require(ek == ak == case.strip(), "input/output key mismatch")
            require(ek not in seen, "duplicate input")
            seen.add(ek)
            require(eh == "0", "reference halted")
            opcode = ek.split()[0]
            require(opcode in OPCODES, "unexpected opcode")
            ewrite = [(i, e) for i, e in enumerate(et) if e[0] == "w"]
            awrite = [(i, e) for i, e in enumerate(at) if e[0] == "w"]
            require(
                len(ewrite) == (0 if opcode == "006d" else 1),
                "wrong reference write count",
            )
            if len(ewrite) == len(awrite) == 1:
                write_deltas[awrite[0][0] - ewrite[0][0]] += 1
            cohort = by_opcode.setdefault(opcode, Counter())
            failures = []
            for kind, differs in [
                ("halted", ah != "0"),
                ("cycle_count", ev[0] != av[0]),
                ("registers", ev[1:] != av[1:]),
                ("bus_trace", et != at),
                ("write_effects", [e for _, e in ewrite] != [e for _, e in awrite]),
                ("write_timing", ewrite != awrite),
            ]:
                if differs:
                    counts[kind] += 1
                    cohort[kind] += 1
                    failures.append(kind)
                    examples.setdefault(
                        kind,
                        {
                            "input": ek,
                            "reference": ref.strip(),
                            "actual": result.strip(),
                        },
                    )
            counts["cases"] += 1
            cohort["cases"] += 1
            if not failures:
                counts["exact"] += 1
                cohort["exact"] += 1
    require(len(seen) == counts["cases"] == 96800, "incomplete case coverage")
    require(
        set(by_opcode) == OPCODES
        and all(c["cases"] == 8800 for c in by_opcode.values()),
        "incomplete opcode coverage",
    )
    return {
        "counts": counts,
        "by_opcode": by_opcode,
        "write_cycle_delta_actual_minus_reference": write_deltas,
        "first_examples": examples,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    d = args.directory
    summary = compare(d / "cases.txt", d / "reference.txt", d / "before.txt")
    (d / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
