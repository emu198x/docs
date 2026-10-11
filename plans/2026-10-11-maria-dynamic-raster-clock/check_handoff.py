"""Recheck all handoffs using the twelve corrected clock transition inputs."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parent.parent
        / "2026-10-11-maria-dynamic-controller-capture"
    ),
)
from probe_capture import (
    check_case,
    circuits,
    controller_network,
    load_cells,
    replay,
    require,
    run_case,
    summarize,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("clock_comparison", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    before = json.loads(args.before.read_text())["cases"]
    after = json.loads(args.after.read_text())["cases"]
    old, new = summarize(before), summarize(after)
    failures = json.loads(args.clock_comparison.read_text())["failures"]
    affected = {
        (r["initial_slow"], r["final_slow"], r["change"], r["order"]) for r in failures
    }
    require(len(affected) == 12, "incomplete affected clock inventory")
    fields = [
        "initial_slow",
        "final_slow",
        "reset_step",
        "mode_change",
        "return_delay",
        "dli",
        "request",
        "slow_order",
    ]
    cells = load_cells(args.archive)
    parts = circuits(cells)
    network = controller_network(cells, feedback=True)
    staged_cache, dynamic_cache = {}, {}
    selected = changed = nmi_changed = observations = pulses = 0
    for a, b in zip(before, after, strict=True):
        require(all(a[k] == b[k] for k in fields), "handoff inputs changed")
        key = (b["initial_slow"], b["final_slow"], b["mode_change"], b["slow_order"])
        if a != b:
            require(key in affected, "unrelated handoff changed")
            changed += 1
            nmi_changed += int(a["nmi_edges"] != b["nmi_edges"])
        if key not in affected:
            continue
        case = run_case(
            parts,
            b["initial_slow"],
            b["final_slow"],
            b["reset_step"],
            b["mode_change"],
            b["return_delay"],
            b["dli"],
            b["request"],
            b["slow_order"],
            staged_cache,
        )
        require(check_case(case) == b, "corrected handoff regeneration differs")
        result = replay(network, parts["nmi"], case, dynamic_cache)
        observations += result["comparisons"]
        pulses += len(result["events"]) // 2
        selected += 1
    require(
        selected == 1728 and observations == 1728 * 208 and pulses == 864,
        "incomplete corrected dynamic replay",
    )
    require(
        changed > 0 and nmi_changed > 0, "sampling correction changed no observations"
    )
    result = {
        "baseline_matrix_sha256": old["matrix_sha256"],
        "corrected_matrix_sha256": new["matrix_sha256"],
        "total_cases": len(after),
        "changed_cases": changed,
        "changed_nmi_cases": nmi_changed,
        "dynamic_replay_cases": selected,
        "dynamic_replay_observations": observations,
        "dynamic_replay_pulses": pulses,
        "unrelated_cases_unchanged": len(after) - selected,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
