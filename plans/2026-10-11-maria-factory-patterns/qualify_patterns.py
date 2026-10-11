"""Inject checked assertions and suppress masks in each pinned factory pattern."""

import argparse
import hashlib
import json
import zipfile
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

from decode_patterns import ARCHIVE_SHA, Program, cover, parse, require_observations


def change(
    program: Program, *, line: int | None = None, suppress: bool = False
) -> Program:
    result = deepcopy(program)
    blocks = [
        result.main,
        result.trailing,
        *[r.statements for r in result.routines.values()],
    ]
    changed = 0
    for block in blocks:
        for index, statement in enumerate(block):
            if (
                suppress
                and statement.kind == "register"
                and statement.register.startswith("M")
            ) or (
                not suppress and statement.kind == "pattern" and statement.line == line
            ):
                block[index] = replace(
                    statement, bits=statement.bits[:41] + "0" + statement.bits[42:]
                )
                changed += 1
    if changed == 0 or (not suppress and changed != 1):
        raise ValueError(f"invalid mutation inventory: {changed}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if hashlib.sha256(args.archive.read_bytes()).hexdigest() != ARCHIVE_SHA:
        raise ValueError("unqualified archive")
    baseline = json.loads(args.baseline.read_text())
    if baseline["archive_sha256"] != ARCHIVE_SHA or len(baseline["results"]) != 4:
        raise ValueError("incomplete or unrelated baseline")
    results = []
    with zipfile.ZipFile(args.archive) as archive:
        for name, expected in baseline["results"].items():
            data = archive.read(name)
            if hashlib.sha256(data).hexdigest() != expected["sha256"]:
                raise ValueError(f"wrong source identity: {name}")
            program = parse(data.decode("ascii"))
            original = cover(program, baseline["initial_directions"])
            require_observations({name: original})
            if original != {
                key: value for key, value in expected.items() if key != "sha256"
            }:
                raise ValueError(f"baseline changed: {name}")
            line = original["first_enabled_nmi_high_line"]
            if not isinstance(line, int):
                raise TypeError(f"no positive observation in {name}")
            injected = cover(change(program, line=line), baseline["initial_directions"])
            if injected["enabled_nmi_low_source_lines"] != [line]:
                raise ValueError(f"injected assertion was not found at line {line}")
            suppressed = cover(
                change(program, suppress=True), baseline["initial_directions"]
            )
            try:
                require_observations({name: suppressed})
            except ValueError as error:
                failure = str(error)
            else:
                raise ValueError(f"masked source unexpectedly passed: {name}")
            results.append(
                {
                    "source": name,
                    "injected_line": line,
                    "injected_candidates": len(injected["enabled_nmi_low_candidates"]),
                    "suppression_failure": failure,
                }
            )
    args.output.write_text(json.dumps(results, indent=2) + "\n")
    print(
        f"PASS: {len(results)} real-source assertion injections and {len(results)} mask-suppression negatives"
    )


if __name__ == "__main__":
    main()
