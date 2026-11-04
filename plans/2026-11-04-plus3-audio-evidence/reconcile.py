"""Combine five fresh production passes with 98 unchanged prior observations."""

import copy
import json
import sys
import tomllib
from pathlib import Path

IDS = {
    "chase-hq-plus3",
    "starglider-2-plus3",
    "lotus-esprit-plus3",
    "robocop-plus3",
    "where-time-stood-still-plus3",
}


def reconcile(
    old: dict, new: dict, previous: dict, fresh: dict, analysis: dict
) -> dict:
    before = {row["id"]: row for row in old["entry"]}
    after = {row["id"]: row for row in new["entry"]}
    assert len(old["entry"]) == len(new["entry"]) == len(before) == len(after) == 103
    assert before.keys() == after.keys()
    restored = copy.deepcopy(new)
    for row in restored["entry"]:
        if row["id"] in IDS:
            identifier = row["id"]
            assert row["audio"]["hash"] == analysis[identifier]["current_audio_hash"]
            assert (
                before[identifier]["audio"]["hash"]
                == analysis[identifier]["old_audio_hash"]
            )
            row["audio"]["hash"] = before[identifier]["audio"]["hash"]
    assert restored == old, "Unexpected catalogue definition change"
    observations = fresh["fresh_results"]
    assert len(observations) == 5 and {row["id"] for row in observations} == IDS
    assert fresh["negative_stale_manifest"]["exit_code"] == 1
    assert "audio mismatch" in fresh["negative_stale_manifest"]["log"]
    for row in observations:
        assert row["pass"] and row["snapshot_replay_pass"]
        for text in [
            "[PASS] " + row["id"],
            "[SNAP-PASS] " + row["id"],
            "1 entries run, 0 failure(s)",
        ]:
            assert text in row["log"]
    rows = copy.deepcopy(previous["results"])
    assert len(rows) == 103 and {row["id"] for row in rows} == before.keys()
    for row in rows:
        identifier = row["id"]
        assert row["status"] == "captured"
        assert row["expected_frame"] == before[identifier]["boot"]["frame_hash"]
        assert row["expected_audio"] == before[identifier]["audio"]["hash"]
        assert row["frame_matches"] == (row["frame_hash"] == row["expected_frame"])
        assert row["audio_matches"] == (row["audio_hash"] == row["expected_audio"])
        row["observation"] = "reused_prior_observation"
        if identifier in IDS:
            assert row["frame_matches"]
            assert row["audio_hash"] == analysis[identifier]["current_audio_hash"]
            row["expected_audio"] = after[identifier]["audio"]["hash"]
            row["audio_matches"] = True
            row["observation"] = "fresh_production_PASS_and_SNAP_PASS"
            row.pop("seconds", None)
    remaining = [
        row["id"] for row in rows if not (row["frame_matches"] and row["audio_matches"])
    ]
    assert set(remaining) == {
        "cybernoid-plus3",
        "stormlord-plus3",
        "tetris-plus3",
        "dragon-ninja-plus3",
    }
    return {
        "kind": "combined ledger; not a fresh full sweep",
        "source": "7537577e8b7a86f5840089aedaa783038fc4304e",
        "prior_source": "1abe54f1b49f23a43853ce161fde022dcc228cea",
        "fresh": 5,
        "reused": 98,
        "completed": 103,
        "matching": 99,
        "remaining": remaining,
        "results": rows,
    }


def main() -> None:
    old, new, previous, fresh, analysis, output = map(Path, sys.argv[1:])
    inputs = (
        tomllib.loads(old.read_text()),
        tomllib.loads(new.read_text()),
        json.loads(previous.read_text()),
        json.loads(fresh.read_text()),
        json.loads(analysis.read_text()),
    )
    result = reconcile(*inputs)
    for label in ["empty", "missing", "duplicate", "changed_other_entry"]:
        bad = copy.deepcopy(inputs)
        if label == "empty":
            bad[3]["fresh_results"] = []
        elif label == "missing":
            bad[2]["results"].pop()
        elif label == "duplicate":
            bad[2]["results"][-1] = copy.deepcopy(bad[2]["results"][0])
        else:
            bad[1]["entry"][0]["boot"]["wait_frames"] += 1
        try:
            reconcile(*bad)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"Negative control accepted: {label}")
    result["rejected_controls"] = [
        "empty",
        "missing",
        "duplicate",
        "changed_other_entry",
    ]
    output.write_text(json.dumps(result, indent=2) + "\n")
    print("99 matching, four retained failures; five fresh plus 98 reused observations")


if __name__ == "__main__":
    main()
