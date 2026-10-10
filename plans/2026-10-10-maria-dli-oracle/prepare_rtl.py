"""Prepare a simulation-only copy for Icarus's split-driver wildcard defect."""

import argparse
import hashlib
import re
from pathlib import Path

COMPARISON = re.compile(
    r"^(assign\s+\w+\[\d+\s*\]\s*=\s*)(\w+)\s*==\?\s*(\d+)'b([01xXzZ?_]+);",
    re.MULTILINE,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--negative-control", action="store_true")
    args = parser.parse_args()
    reference = args.reference.resolve()
    output = args.output.resolve()
    if output.is_relative_to(reference.parent):
        parser.error("output must be outside the reference RTL directory")
    source = reference.read_text()
    patterns: dict[int, list[tuple[str, int, int]]] = {}

    def replace(match: re.Match[str]) -> str:
        prefix, operand, size, bits = match.groups()
        width = int(size)
        bits = bits.replace("_", "").lower().rjust(width, "0")
        if len(bits) != width or (operand, width) not in {("cond", 5), ("cond2", 14)}:
            raise ValueError("unexpected continuous comparator shape")
        mask = int("".join("1" if bit in "01" else "0" for bit in bits), 2)
        value = int("".join("1" if bit == "1" else "0" for bit in bits), 2)
        patterns.setdefault(width, []).append((bits, mask, value))
        return f"{prefix}(({operand} & {width}'h{mask:x}) == {width}'h{value:x});"

    generated, count = COMPARISON.subn(replace, source)
    if count != 55 or {width: len(rows) for width, rows in patterns.items()} != {
        5: 7,
        14: 48,
    }:
        raise ValueError(f"unexpected comparator inventory: {count}")
    output.mkdir(parents=True, exist_ok=True)
    (output / "DMA.masked.sv").write_text(generated)
    checker = ["module comparator_tb;", "integer i, j, count=0, seed=198197;"]
    changed = False
    for width, rows in patterns.items():
        checker.append(f"logic [{width - 1}:0] sample{width};")
        checker.append(f"task check{width}(input logic [{width - 1}:0] operand); begin")
        for bits, mask, value in rows:
            if args.negative_control and not changed:
                mask ^= mask & -mask
                changed = True
            checker.extend(
                [
                    f"if ((operand ==? {width}'b{bits}) !== ((operand & {width}'h{mask:x}) == {width}'h{value:x}))",
                    f'$fatal(1,"comparator mismatch width={width} operand=%b",operand);',
                    "count=count+1;",
                ]
            )
        checker.append("end endtask")
    checker.append("initial begin")
    expected = 0
    for width, rows in patterns.items():
        expected += ((1 << width) + 4096) * len(rows)
        checker.extend(
            [
                f"for(i=0;i<{1 << width};i=i+1) begin sample{width}=i; check{width}(sample{width}); end",
                "for(i=0;i<4096;i=i+1) begin",
                f"for(j=0;j<{width};j=j+1) begin",
                "case($urandom(seed)%4)",
                f"0: sample{width}[j]=0; 1: sample{width}[j]=1;",
                f"2: sample{width}[j]=1'bx; 3: sample{width}[j]=1'bz;",
                "endcase end",
                f"check{width}(sample{width}); end",
            ]
        )
    checker.extend(
        [
            f'if(count!={expected}) $fatal(1,"wrong comparison count");',
            '$display("COMPARISONS=%0d MISMATCHES=0",count);',
            "$finish; end endmodule",
        ]
    )
    (output / "comparator_tb.sv").write_text("\n".join(checker) + "\n")
    print(f"reference_sha256={hashlib.sha256(reference.read_bytes()).hexdigest()}")
    print(f"generated_sha256={hashlib.sha256(generated.encode()).hexdigest()}")
    print(f"continuous_comparators={count} equivalence_checks={expected}")


if __name__ == "__main__":
    main()
