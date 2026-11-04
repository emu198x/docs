"""Verify the complete catalogue boundary before publishing new expectations."""

import argparse
import json
from pathlib import Path
from typing import Any

GAMES = ("robocop", "out-run", "where-time-stood-still")
QUALIFIED = {f"{game}-{board}" for game in GAMES for board in ("plus2a", "plus2b")}
REMAINING = {
    f"{game}-plus3"
    for game in (
        "chase-hq",
        "rainbow-islands",
        "cybernoid",
        "stormlord",
        "starglider-2",
        "lotus-esprit",
        "tetris",
        "robocop",
        "where-time-stood-still",
        "dragon-ninja",
    )
}


def complete(report: dict[str, Any]) -> dict[str, Any]:
    rows = report["results"]
    if report["completed"] != 103 or report["expected"] != 103:
        raise ValueError("incomplete capture")
    ids = [row["id"] for row in rows]
    if len(ids) != 103 or len(set(ids)) != 103:
        raise ValueError("missing or duplicate capture")
    if report["errors"] or any(row["status"] != "captured" for row in rows):
        raise ValueError("capture errors are not hash disagreements")
    return {row["id"]: row for row in rows}


def compare(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    old, new = complete(previous), complete(current)
    assert set(old) == set(new)
    assert QUALIFIED <= set(new) and REMAINING <= set(new)
    changed_expectations = set()
    for id_, row in new.items():
        before = old[id_]
        assert row["expected_frame"] == before["expected_frame"], id_
        # This includes the unrelated 48K keyboard change on current main.
        assert row["frame_hash"] == before["frame_hash"], id_
        assert row["audio_hash"] == before["audio_hash"], id_
        if row["expected_audio"] != before["expected_audio"]:
            changed_expectations.add(id_)
            assert not before["audio_matches"] and row["audio_matches"], id_
        assert row["frame_matches"] == (row["frame_hash"] == row["expected_frame"])
        assert row["audio_matches"] == (row["audio_hash"] == row["expected_audio"])
    assert changed_expectations == QUALIFIED
    failed = {
        id_
        for id_, row in new.items()
        if not (row["frame_matches"] and row["audio_matches"])
    }
    assert failed == REMAINING
    assert {row["id"] for row in current["changed"]} == failed
    assert len(current["changed"]) == len(failed)
    return {
        "entries": len(new),
        "matching_pairs": len(new) - len(failed),
        "capture_errors": 0,
        "qualified_ids": sorted(changed_expectations),
        "remaining_ids": sorted(failed),
        "unchanged_observed_frame_audio_pairs": len(new),
        "frame_disagreements": sum(not row["frame_matches"] for row in new.values()),
        "audio_disagreements": sum(not row["audio_matches"] for row in new.values()),
    }


def self_test() -> None:
    report = {
        "completed": 103,
        "expected": 103,
        "errors": [],
        "results": [{"id": str(i), "status": "captured"} for i in range(103)],
    }
    assert len(complete(report)) == 103
    for bad in (
        report | {"completed": 102},
        report | {"results": []},
        report | {"results": report["results"][:-1] + [report["results"][0]]},
        report | {"errors": ["timeout"]},
    ):
        try:
            complete(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("incomplete, duplicate or failed run accepted")
    print("Complete coverage accepted; incomplete/empty/duplicate/error runs rejected.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--current", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if args.previous is None or args.current is None or args.output is None:
        parser.error("--previous, --current and --output are required")
    result = compare(
        json.loads(args.previous.read_text()), json.loads(args.current.read_text())
    )
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
