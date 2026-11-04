"""Check bounded AY observations without publishing game data or recordings."""

import argparse
import collections
import json
import re
import tomllib
from pathlib import Path
from typing import Any

GAMES = ("robocop", "out-run", "where-time-stood-still")
EXPECTED = {
    "before": ("d175d0946abcd29d", "56e8f046d843cf21", "72247e53c91f6a20"),
    "current": ("75dc5b625c861ae6", "b9409931fe776915", "520fd8f8ff2724d4"),
}


def matching_fields(
    a: list[dict[str, Any]], b: list[dict[str, Any]], shift: int
) -> int:
    if len(a) != 100 or len(b) != 100:
        raise ValueError("exactly 100 complete fields required")
    pairs = [
        (f["writes"], b[i + shift]["writes"])
        for i, f in enumerate(a)
        if 0 <= i + shift < len(b)
    ]
    if not pairs or any(not left or not right for left, right in pairs):
        raise ValueError("empty command observation")
    return sum(left == right for left, right in pairs)


def edges(path: Path) -> list[tuple[int, int, int, int, int]]:
    field = -1
    rows = []
    for line in path.read_text().splitlines():
        if line.startswith("AY_FIELD "):
            field = int(line.split()[1])
        elif line.startswith("AY_EDGE "):
            hc, pc, register, value = map(int, line.split()[1:])
            if not 0 <= field < 100:
                raise ValueError("write outside bounded fields")
            rows.append((field, hc, pc, register, value))
    return rows


def read(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text())


def analyse(root: Path) -> dict[str, Any]:
    report = {}
    for index, game in enumerate(GAMES):
        old_path, new_path = root / "before" / game, root / "current" / game
        old, new = read(old_path / "audit.toml"), read(new_path / "audit.toml")
        for label, audit in (("before", old), ("current", new)):
            assert audit["audio_hash"] == "xxh64:" + EXPECTED[label][index]
            assert audit["id"] == game + "-plus2a"
            assert audit["end_time"] - audit["start_time"] == 35_454_000
        assert old["boot_hash"] == new["boot_hash"]
        delta = new["start_time"] - old["start_time"]
        assert delta == 354_540
        a, b = (
            read(old_path / "before-ay.toml")["inner"],
            read(new_path / "before-ay.toml")["inner"],
        )
        clocks = delta // 10
        assert (a["prescaler"] + clocks) % 8 == b["prescaler"]
        assert (a["sample_error"] + clocks * a["sample_rate"]) % a["ay_clock_hz"] == b[
            "sample_error"
        ]
        bridge = None
        if game == "out-run":
            # Compare observed writes with stored state using AY 0.6.1's
            # existing write_data register masks, not raw bus high bits.
            first = new["fields"][0]["writes"]
            assert sorted(w["register"] for w in first) == list(range(13))
            masks = {1: 15, 3: 15, 5: 15, 6: 31, 8: 31, 9: 31, 10: 31}
            bridge = all(
                a["regs"][w["register"]] == w["value"] & masks.get(w["register"], 255)
                for w in first
            )
            assert bridge, "Out Run initial field does not match old register image"
        shift = 1 if game == "out-run" else 0
        count = matching_fields(old["fields"], new["fields"], shift)
        assert count == 100 - shift, f"{game}: command stream differs"
        aa, bb = edges(old_path / "observer.log"), edges(new_path / "observer.log")
        expected_writes = {
            "robocop": 1200,
            "out-run": 1300,
            "where-time-stood-still": 1100,
        }[game]
        assert len(aa) == len(bb) == expected_writes
        aa = [r for r in aa if r[0] + shift < 100]
        bb = [r for r in bb if r[0] >= shift]
        assert len(aa) == len(bb) > 0
        assert all(
            (x[0] + shift, x[2:]) == (y[0], y[2:]) for x, y in zip(aa, bb, strict=True)
        )
        differences = collections.Counter(
            y[1] - x[1] for x, y in zip(aa, bb, strict=True)
        )
        assert any(delta != 0 for delta in differences)
        delayed_path = root / "before-delayed" / game
        delayed = read(delayed_path / "audit.toml")
        delayed_state = read(delayed_path / "before-ay.toml")["inner"]
        assert delayed["start_time"] == new["start_time"]
        # This is a rejected hypothesis, not a successful exact-audio control.
        assert delayed["audio_hash"] != new["audio_hash"]
        zero_path = root / "before-stages" / game
        zero = read(zero_path / "audit.toml")
        assert zero == old, "zero-delay observer must retain every ordinary result"
        log = (zero_path / "observer.log").read_text()
        assert re.search(r"^AUDIT_BOOT 55 19499700$", log, re.MULTILINE)
        report[game] = {
            "frame_hash": new["boot_hash"],
            "old_audio_hash": old["audio_hash"],
            "qualified_audio_hash": new["audio_hash"],
            "start_time_delta": delta,
            "duration": new["end_time"] - new["start_time"],
            "extra_ay_input_clocks": clocks,
            "sample_error_prediction_matches": True,
            "prescaler_prediction_matches": True,
            "command_field_shift": shift,
            "first_field_matches_old_stored_registers": bridge,
            "matching_fields": count,
            "compared_commands": len(aa),
            "write_edge_deltas_master_ticks": dict(sorted(differences.items())),
            "old_one_field_delay_audio_hash": delayed["audio_hash"],
            "delayed_initial_chip_difference_fields": [
                k for k in delayed_state if delayed_state[k] != b[k] and k != "samples"
            ],
            "zero_delay_control_matches": True,
        }
    assert len(report) == 3
    return report


def self_test() -> None:
    fields = [{"writes": [{"pc": 1, "register": 2, "value": i}]} for i in range(100)]
    assert matching_fields(fields, fields, 0) == 100
    changed = json.loads(json.dumps(fields))
    changed[50]["writes"][0]["value"] = -1
    assert matching_fields(fields, changed, 0) == 99
    for bad in ([], [{"writes": []}] * 100):
        try:
            matching_fields(bad, bad, 0)
        except ValueError:
            pass
        else:
            raise AssertionError("missing observations accepted")
    print(
        "Complete observations accepted; changed command and empty observations rejected."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if args.observations is None or args.output is None:
        parser.error("--observations and --output are required")
    result = analyse(args.observations)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Qualified {len(result)} complete command comparisons and causal controls.")


if __name__ == "__main__":
    main()
