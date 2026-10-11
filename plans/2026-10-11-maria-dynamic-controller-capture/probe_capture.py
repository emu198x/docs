"""Exercise actual IRQ controller pass banks without the staged truth-table loop."""

import argparse
import copy
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parent.parent
        / "2026-10-11-maria-halt-generator-handoff"
    ),
)
sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent / "2026-10-11-maria-interrupt-circuit"),
)
from layout_network import Union, extract, require, routing_groups
from probe_handoff import Pad, check_case, circuits, run_case
from summarize import summarize
from trace_circuit import PLA, check_ports, expected_row, g, load_cells, top_routing


def controller_network(cells: dict, feedback: bool = False) -> dict:
    network = extract(g.geometry(cells[PLA]))
    require(len(network["devices"]) == 89, "unexpected controller inventory")
    aliases = {
        "pla_vdd/1": "vdd",
        "pla_vss/1": "vss",
        "pla_clkin/1": "ph2",
        "pla_clk/1": "ph1",
    }
    aliases.update({f"pla_in{i}/1": f"in{i}" for i in range(1, 6)})
    aliases.update({f"pla_out{i}/1": f"out{i}" for i in range(1, 6)})
    network["labels"] = {
        k: ["irq/" + aliases[name] for name in names]
        for k, names in network["labels"].items()
    }
    labels = {
        name.split("/")[-1]: int(n)
        for n, names in network["labels"].items()
        for name in names
    }
    for phase in ["ph1", "ph2"]:
        gates = [d for d in network["devices"] if d["gate"] == labels[phase]]
        require(
            len(gates) == 5 and all(d["implant"] == 3 for d in gates),
            "unexpected controller bank",
        )
    for i in range(1, 6):
        require(
            sum(
                d["gate"] == labels["ph2"] and labels[f"in{i}"] in d["terminals"]
                for d in network["devices"]
            )
            == 1,
            "input does not have one phase-2 gate",
        )
    if feedback:
        rects, names, _ = top_routing(cells)
        check_ports(routing_groups(rects, names)[0])
        union = Union(max(labels.values()) + 1)
        for out, inp in [("out1", "in5"), ("out2", "in4")]:
            union.join([labels[out], labels[inp]])
        joined = {}
        for n, names in network["labels"].items():
            joined.setdefault(str(union.find(int(n))), []).extend(names)
        network["labels"] = joined
        for d in network["devices"]:
            d["gate"] = union.find(d["gate"])
            d["terminals"] = sorted(union.find(n) for n in d["terminals"])
    output = next(n for n, names in network["labels"].items() if "irq/out5" in names)
    network["labels"][output].append("irq/pad")
    return network


def outputs(circuit: Pad) -> list[int]:
    return [circuit.values[circuit.node(f"out{i}")] for i in range(1, 6)]


def expected(bits: tuple[int, ...]) -> list[int]:
    r = expected_row(bits[4] + 2 * bits[3], bits[2], bits[1], bits[0])
    return [r["next"] & 1, r["next"] >> 1, r["enable"], r["set"], r["reset"]]


def transfer_checks(network: dict) -> dict:
    bits = list(itertools.product([0, 1], repeat=5))
    count = 0
    for before, after in itertools.product(bits, repeat=2):
        c = Pad(network)
        a = {f"in{i + 1}": b for i, b in enumerate(before)}
        b = {f"in{i + 1}": v for i, v in enumerate(after)}
        c.settle({"ph1": 0, "ph2": 1, **a})
        c.settle({"ph1": 0, "ph2": 0, **a})
        c.settle({"ph1": 1, "ph2": 0, **a})
        require(outputs(c) == expected(before), "initial dynamic transfer mismatch")
        c.settle({"ph1": 0, "ph2": 0, **a})
        c.settle({"ph1": 0, "ph2": 1, **b})
        require(outputs(c) == expected(before), "output changed during input capture")
        c.settle({"ph1": 0, "ph2": 0, **b})
        changed = {k: 1 - v for k, v in b.items()}
        c.settle({"ph1": 0, "ph2": 0, **changed})
        c.settle({"ph1": 1, "ph2": 0, **changed})
        require(outputs(c) == expected(after), "closed input bank failed to hold")
        c.settle({"ph1": 0, "ph2": 0, **changed})
        require(outputs(c) == expected(after), "closed output bank failed to hold")
        count += 1
    require(count == 1024, "incomplete controller transition sweep")
    return {"transitions": count, "sampled_inputs": 5, "output_gates": 5}


def replay(network: dict, latch: dict, case: dict, cache: dict | None = None) -> dict:
    irq, nmi = Pad(network), Pad(latch)
    previous = {"in1": 0, "in2": 0, "in3": 0}
    events = []
    old_nmi = 1
    comparisons = 0

    def settle(tag: str, c: Pad, inputs: dict) -> int:
        if cache is None:
            return c.settle(inputs)
        key = (tag, tuple(sorted(c.values.items())), tuple(sorted(inputs.items())))
        if key not in cache:
            result = c.settle(inputs)
            cache[key] = (result, dict(c.values))
        result, state = cache[key]
        c.values = dict(state)
        return result

    for row in case["rows"]:
        step, ph2 = row["step"], row["ph2"]
        # Separate closing, input changes and opening; no overlapping banks.
        settle("irq", irq, {"ph1": 0, "ph2": 0, **previous})
        previous = {
            "in1": row["edge"],
            "in2": row["halt"],
            "in3": case["dli"] if step >= 48 else 0,
        }
        settle("irq", irq, {"ph1": 0, "ph2": 0, **previous})
        settle("irq", irq, {"ph1": 1 - ph2, "ph2": ph2, **previous})
        out = outputs(irq)
        level = settle(
            "nmi",
            nmi,
            {"ph2": ph2, "intset": out[3], "intrst": out[4], "menblf": int(step < 24)},
        )
        if step >= 32:
            require(
                level == row["nmi"],
                f"dynamic NMI differs from staged model at step {step}",
            )
            comparisons += 1
            if level != old_nmi:
                events.append([step, level])
        old_nmi = level
    require(comparisons == 208, "incomplete dynamic replay")
    require(
        [v for _, v in events] == [0, 1] * case["dli"], "wrong dynamic pulse inventory"
    )
    return {"comparisons": comparisons, "events": events}


def full_replay(parts: dict, network: dict, matrix: Path) -> dict:
    cases = json.loads(matrix.read_text())["cases"]
    baseline = summarize(cases)
    staged_cache, dynamic_cache = {}, {}
    observations, pulses, uncached = 0, 0, 0
    for index, saved in enumerate(cases):
        case = run_case(
            parts,
            saved["initial_slow"],
            saved["final_slow"],
            saved["reset_step"],
            saved["mode_change"],
            saved["return_delay"],
            saved["dli"],
            saved["request"],
            saved["slow_order"],
            staged_cache,
        )
        require(
            check_case(case) == saved,
            "regenerated baseline differs from retained matrix",
        )
        result = replay(network, parts["nmi"], case, dynamic_cache)
        if (
            saved["reset_step"] == 100
            and saved["mode_change"] in [96, 100, 124, 140]
            and saved["return_delay"] == 0
            and saved["dli"] == 1
        ):
            require(
                result == replay(network, parts["nmi"], case),
                "cached dynamic replay differs",
            )
            uncached += 1
        observations += result["comparisons"]
        pulses += len(result["events"]) // 2
        if (index + 1) % 4096 == 0:
            print(
                json.dumps({"completed": index + 1, "observations": observations}),
                flush=True,
            )
    require(
        observations == 32832 * 208 and pulses == 16416 and uncached == 40,
        "incomplete full dynamic replay",
    )
    return {
        "cases": len(cases),
        "comparisons": observations,
        "pulses": pulses,
        "uncached_trace_checks": uncached,
        "baseline_matrix_sha256": baseline["matrix_sha256"],
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--matrix", type=Path)
    args = p.parse_args()
    cells = load_cells(args.archive)
    parts = circuits(cells)
    network = controller_network(cells)
    result = transfer_checks(network)
    result.update(archive_sha256=g.ARCHIVE_SHA, member_sha256=g.MEMBER_SHA)
    broken = copy.deepcopy(network)
    m = Pad(broken)
    edge_gates = [
        d
        for d in broken["devices"]
        if d["gate"] == m.node("ph2") and m.node("in1") in d["terminals"]
    ]
    require(len(edge_gates) == 1, "ambiguous clock-edge sample gate")
    edge_gates[0]["gate"] = m.node("vdd")
    try:
        transfer_checks(broken)
    except ValueError as error:
        require(
            str(error) == "closed input bank failed to hold",
            "wrong live-edge negative: " + str(error),
        )
        result["live_edge_negative"] = str(error)
    else:
        raise ValueError("live clock edge passed capture checks")
    broken = copy.deepcopy(network)
    m = Pad(broken)
    gates = [d for d in broken["devices"] if d["gate"] == m.node("ph1")]
    require(len(gates) == 5, "ambiguous output-bank negative")
    for gate in gates:
        gate["gate"] = m.node("vdd")
    try:
        transfer_checks(broken)
    except ValueError as error:
        require(
            str(error) == "output changed during input capture",
            "wrong output-bank negative: " + str(error),
        )
        result["open_output_negative"] = str(error)
    else:
        raise ValueError("open output bank passed capture checks")
    feedback = controller_network(cells, feedback=True)
    samples = []
    for a, b in [(0, 0), (0, 1), (1, 0), (1, 1)]:
        case = run_case(parts, a, b, 100, 100, 0, 1)
        samples.append(
            {"initial_slow": a, "final_slow": b, **replay(feedback, parts["nmi"], case)}
        )
    result["samples"] = samples
    if args.matrix:
        result["full_replay"] = full_replay(parts, feedback, args.matrix)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
