"""Conservative pattern coverage, not a Sentry clock or physical-chip simulator.

Only the full 60-pin source syntax in the four pinned ZMAR*.2SC.1 members is
accepted. The main prefix may include unexecuted padding. MATCH bodies are
covered once with unknown multiplicity; they must have no register writes.
The host end address, compiled-memory layout and strobe pipeline are not
modelled, so output positions must never be converted to elapsed time.
"""

import argparse
import hashlib
import json
import re
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ARCHIVE_SHA = "849e215c71d13c17ec813f97a23b2078469c4b1e14a36dcd5a9ccf72b5360a48"
PREFIX = "GCC_MARIA_Chip_Layout_and_Netlist_Artifacts/MARIAS/MARIAB/"


@dataclass(frozen=True)
class Statement:
    kind: str
    line: int
    bits: str = ""
    register: str = ""
    direction: str = "D1"
    mask: str = "M1"
    timing: str = "TS1"
    repeat: int = 1
    call: str = ""


@dataclass
class Routine:
    mode: str
    repeat: int
    statements: list[Statement]


@dataclass
class Program:
    main: list[Statement]
    routines: dict[str, Routine]
    trailing: list[Statement]
    commands: int


def pattern(value: str) -> str:
    bits = value.replace(" ", "")
    if len(bits) != 60 or set(bits) - {"0", "1"}:
        raise ValueError("expected exactly 60 binary pin values")
    return bits


def parse(source: str) -> Program:
    program = Program([], {}, [], 0)
    direction, mask, timing = "D1", "M1", "TS1"
    current = program.main
    active = ""
    offset = 0
    for raw in source.split(";")[:-1]:
        start = offset + len(raw) - len(raw.lstrip())
        line = source.count("\n", 0, start) + 1
        offset += len(raw) + 1
        command = " ".join(raw.split())
        if not command:
            raise ValueError(f"empty statement at line {line}")
        program.commands += 1
        if match := re.fullmatch(r"ENABLE (.+)", command):
            for option in match[1].replace(" ", "").split(","):
                if option in {"D1", "D2"}:
                    direction = option
                elif option in {"M1", "M2"}:
                    mask = option
                elif option in {"TS1", "TS2", "TS3", "TS4"}:
                    timing = option
                elif option != "I1":
                    raise ValueError(f"unsupported selection {option} at line {line}")
            continue
        if match := re.fullmatch(r"LSUBR (\w+) (NORMAL|MATCH) (\d+)", command):
            name, mode, repeat = match.groups()
            if active or name in program.routines or int(repeat) < 1:
                raise ValueError(f"invalid routine {name} at line {line}")
            routine = Routine(mode, int(repeat), [])
            program.routines[name] = routine
            current = routine.statements
            active = name
            continue
        if match := re.fullmatch(r"LSET ([DM][12]) ([01 ]+)", command):
            current.append(Statement("register", line, pattern(match[2]), match[1]))
            continue
        if match := re.fullmatch(
            r"SET F ([01 ]+?)(?: ?-(LCALL) (\w+)| ?-(LEND))?", command
        ):
            bits, _, call, end = match.groups()
            current.append(
                Statement(
                    "pattern",
                    line,
                    pattern(bits),
                    direction=direction,
                    mask=mask,
                    timing=timing,
                    call=call or "",
                )
            )
            if end:
                if not active:
                    raise ValueError(f"return outside a routine at line {line}")
                active = ""
                current = program.trailing
            continue
        if match := re.fullmatch(r"SET FC NORMAL (\d+) ([01 ]+)", command):
            if int(match[1]) < 1:
                raise ValueError(f"invalid repeat at line {line}")
            current.append(
                Statement(
                    "pattern",
                    line,
                    pattern(match[2]),
                    direction=direction,
                    mask=mask,
                    timing=timing,
                    repeat=int(match[1]),
                )
            )
            continue
        raise ValueError(f"unsupported statement at line {line}: {command}")
    if source.split(";")[-1].strip() or active:
        raise ValueError("unterminated statement or routine")
    for statement in (
        program.main
        + program.trailing
        + [s for r in program.routines.values() for s in r.statements]
    ):
        if statement.call and statement.call not in program.routines:
            raise ValueError(
                f"missing routine {statement.call} at line {statement.line}"
            )
    return program


def cover(
    program: Program, initial_directions: dict[str, str] | None = None
) -> dict[str, object]:
    registers: dict[str, str] = dict(initial_directions or {})
    inventory: Counter[str] = Counter()
    candidates: list[dict[str, object]] = []
    active_low_lines: set[int] = set()
    matched: set[str] = set()
    called: set[str] = set()
    first_checked_high: int | None = None
    steps = 0

    def walk(
        statements: list[Statement], stack: tuple[str, ...], uncertain: bool
    ) -> None:
        nonlocal steps, first_checked_high
        for statement in statements:
            steps += 1
            if steps > 1_000_000:
                raise ValueError("coverage step limit exceeded")
            if statement.kind == "register":
                if uncertain:
                    raise ValueError("MATCH register mutation requires a runtime model")
                registers[statement.register] = statement.bits
                inventory["register_writes"] += 1
                continue
            try:
                directions, masks = (
                    registers[statement.direction],
                    registers[statement.mask],
                )
            except KeyError as error:
                raise ValueError(
                    f"undefined register at line {statement.line}: {error}"
                ) from error
            for _ in range(statement.repeat):
                inventory["pattern_visits"] += 1
                if inventory["pattern_visits"] > 1_000_000:
                    raise ValueError("pattern visit limit exceeded")
                if uncertain:
                    inventory["match_body_visits_unknown_multiplicity"] += 1
                # Tester pins are one-based. IMASK ignores inputs. MEN must
                # itself be driven high before this can be an enabled NMI.
                checked = masks[41] == "1" and directions[41] == "0"
                enabled = directions[40] == "1" and statement.bits[40] == "1"
                if checked:
                    inventory["checked_nmi_patterns"] += 1
                    inventory[
                        "checked_nmi_low"
                        if statement.bits[41] == "0"
                        else "checked_nmi_high"
                    ] += 1
                if enabled:
                    inventory["men_high_patterns"] += 1
                    if statement.bits[41] == "0":
                        inventory["men_high_raw_nmi_low_patterns"] += 1
                if enabled and checked:
                    inventory["enabled_checked_nmi_patterns"] += 1
                    if statement.bits[41] == "1" and first_checked_high is None:
                        first_checked_high = statement.line
                    if statement.bits[41] == "0":
                        active_low_lines.add(statement.line)
                        candidates.append(
                            {
                                "line": statement.line,
                                "timing": statement.timing,
                                "call_stack": list(stack),
                                "match_uncertain": uncertain,
                                "halt": statement.bits[37],
                                "pclk0": statement.bits[35],
                            }
                        )
                if statement.call:
                    name = statement.call
                    if name in stack:
                        raise ValueError(f"recursive routine {name}")
                    called.add(name)
                    routine = program.routines[name]
                    is_match = routine.mode == "MATCH"
                    if is_match:
                        matched.add(name)
                    for _ in range(1 if is_match else routine.repeat):
                        walk(routine.statements, (*stack, name), uncertain or is_match)

    walk(program.main, (), False)
    return {
        "inventory": dict(sorted(inventory.items())),
        "called_routines": sorted(called),
        "match_routines": sorted(matched),
        "stored_commands": program.commands,
        "first_enabled_nmi_high_line": first_checked_high,
        "stored_main_instructions": len(program.main),
        "stored_routines": len(program.routines),
        "unexecuted_inter_routine_instructions": len(program.trailing),
        "enabled_nmi_low_source_lines": sorted(active_low_lines),
        "enabled_nmi_low_candidates": candidates,
    }


def require_observations(results: dict[str, dict[str, object]]) -> None:
    for name, result in results.items():
        if result["inventory"].get("enabled_checked_nmi_patterns", 0) == 0:
            raise ValueError(f"missing enabled-NMI observations: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if hashlib.sha256(args.archive.read_bytes()).hexdigest() != ARCHIVE_SHA:
        raise ValueError("unqualified factory archive")
    results = {}
    with zipfile.ZipFile(args.archive) as archive:
        host_name = PREFIX + "ZMARIA.2SC.3"
        host = archive.read(host_name)
        initial = {}
        for register, prefix in [("D1", "DA"), ("D2", "DB")]:
            matches = re.findall(
                r"SET " + prefix + r"\*\s*((?:\(24:1\)|\(8:0\))[^;]+);",
                host.decode("ascii"),
            )
            if len(matches) != 1:
                raise ValueError(f"ambiguous initial {register} in host source")
            expanded = re.sub(
                r"\((\d+):([01]+)\)", lambda m: m[2] * int(m[1]), matches[0]
            )
            initial[register] = pattern(" ".join(expanded.split()))
        for number in range(4):
            name = f"{PREFIX}ZMAR0{number}.2SC.1"
            data = archive.read(name)
            result = cover(parse(data.decode("ascii")), initial)
            result["sha256"] = hashlib.sha256(data).hexdigest()
            results[name] = result
    if len(results) != 4:
        raise ValueError("incomplete source inventory")
    require_observations(results)
    args.output.write_text(
        json.dumps(
            {
                "scope": "stored main prefix and called bodies; MATCH multiplicity, host end address and elapsed time unmodelled",
                "assumptions": "IMASK enabled, raw positive-logic pattern values; no inversion or clock-strobe interpretation",
                "archive_sha256": ARCHIVE_SHA,
                "host_source": host_name,
                "host_sha256": hashlib.sha256(host).hexdigest(),
                "initial_directions": initial,
                "results": results,
            },
            indent=2,
        )
        + "\n"
    )
    for name, result in results.items():
        print(
            Path(name).name,
            result["inventory"],
            "candidate lines",
            result["enabled_nmi_low_source_lines"],
        )


if __name__ == "__main__":
    main()
