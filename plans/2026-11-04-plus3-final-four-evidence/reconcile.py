"""Reconcile four fresh verified cases with 99 unchanged prior observations."""

import copy
import json
import sys
import tomllib
from pathlib import Path

IDS = {"cybernoid-plus3", "stormlord-plus3", "tetris-plus3", "dragon-ninja-plus3"}


def reconcile(old: dict, new: dict, previous: dict, fresh: dict) -> dict:
    before = {row["id"]: row for row in old["entry"]}
    after = {row["id"]: row for row in new["entry"]}
    assert len(old["entry"]) == len(new["entry"]) == len(before) == len(after) == 103
    assert before.keys() == after.keys()
    restored = copy.deepcopy(new)
    for row in restored["entry"]:
        if row["id"] in IDS:
            row["boot"]["frame_hash"] = before[row["id"]]["boot"]["frame_hash"]
            row["audio"]["hash"] = before[row["id"]]["audio"]["hash"]
    assert restored == old, "Unexpected definition change"
    observations = fresh["fresh_results"]
    assert len(observations) == 4 and {row["id"] for row in observations} == IDS
    observed = {row["id"]: row for row in observations}
    for row in observations:
        assert row["pass"] and row["snapshot_replay_pass"]
        assert "[PASS] " + row["id"] in row["log"]
        assert "[SNAP-PASS] " + row["id"] in row["log"]
        assert "1 entries run, 0 failure(s)" in row["log"]
        assert len(row["negatives"]) == 2
        assert {control["control"] for control in row["negatives"]} == {
            "old-pair",
            "old-audio",
        }
        for control in row["negatives"]:
            assert control["exit_code"] == 1
            assert "[SNAP-PASS] " + row["id"] in control["log"]
            assert (
                "boot mismatch"
                if control["control"] == "old-pair"
                else "audio mismatch"
            ) in control["log"]
            assert control["observed"] == row["observed"]
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
            actual = observed[identifier]["observed"]
            assert actual == {
                "boot.frame_hash": row["frame_hash"],
                "audio.hash": row["audio_hash"],
            }
            assert actual == {
                "boot.frame_hash": after[identifier]["boot"]["frame_hash"],
                "audio.hash": after[identifier]["audio"]["hash"],
            }
            row["expected_frame"] = actual["boot.frame_hash"]
            row["expected_audio"] = actual["audio.hash"]
            row["frame_matches"] = row["audio_matches"] = True
            row["observation"] = "fresh_production_PASS_and_SNAP_PASS"
            row.pop("seconds", None)
    assert all(row["frame_matches"] and row["audio_matches"] for row in rows)
    return {
        "kind": "combined ledger; not a fresh full sweep",
        "source": "8f7daf62eeb0bf8bedbb6f3e6f4c08b83ae22818",
        "prior_source": "2ae3a51198d9a91fc7c4b04b1babf64c930ee10c",
        "fresh": 4,
        "reused": 99,
        "completed": 103,
        "matching": 103,
        "remaining": [],
        "results": rows,
    }


def main() -> None:
    old, new, previous, fresh, destination = map(Path, sys.argv[1:])
    inputs = (
        tomllib.loads(old.read_text()),
        tomllib.loads(new.read_text()),
        json.loads(previous.read_text()),
        json.loads(fresh.read_text()),
    )
    result = reconcile(*inputs)
    rejected = []
    for label in [
        "empty",
        "missing",
        "duplicate",
        "changed_other_entry",
        "missing_audio_negative",
    ]:
        bad = copy.deepcopy(inputs)
        if label == "empty":
            bad[3]["fresh_results"] = []
        elif label == "missing":
            bad[2]["results"].pop()
        elif label == "duplicate":
            bad[2]["results"][-1] = copy.deepcopy(bad[2]["results"][0])
        elif label == "changed_other_entry":
            bad[1]["entry"][0]["boot"]["wait_frames"] += 1
        else:
            bad[3]["fresh_results"][0]["negatives"].pop()
        try:
            reconcile(*bad)
        except AssertionError:
            rejected.append(label)
        else:
            raise AssertionError(f"Negative control accepted: {label}")
    result["rejected_controls"] = rejected
    destination.write_text(json.dumps(result, indent=2) + "\n")
    print(
        "103 matching; four fresh and 99 reused observations; five invalid inputs rejected"
    )


if __name__ == "__main__":
    main()
