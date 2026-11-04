"""Reconcile one fresh Rainbow capture with 102 identified prior observations."""

import copy
import json
import sys
import tomllib
from pathlib import Path

RAINBOW = "rainbow-islands-plus3"


def reconcile(old: dict, new: dict, previous: dict, fresh: dict) -> dict:
    def entries(manifest: dict) -> dict:
        rows = manifest["entry"]
        assert len(rows) == 103
        indexed = {row["id"]: row for row in rows}
        assert len(indexed) == 103
        return indexed

    before, after = entries(old), entries(new)
    assert before.keys() == after.keys()
    restored = copy.deepcopy(new)
    target = next(row for row in restored["entry"] if row["id"] == RAINBOW)
    assert before[RAINBOW]["boot"]["wait_frames"] == 6000
    assert target["boot"]["wait_frames"] == 1755
    target["boot"]["wait_frames"] = 6000
    assert restored == old, "Unexpected catalogue definition change"
    rows = previous["results"]
    assert previous["completed"] == previous["expected"] == len(rows) == 103
    assert {row["id"] for row in rows} == before.keys()
    assert fresh["id"] == RAINBOW
    assert fresh["positive_run"]["exit_code"] == 0
    assert "1 entries run, 0 failure(s)" in fresh["positive_run"]["log"]
    assert fresh["negative_old_waypoint"]["exit_code"] == 1
    assert "boot mismatch" in fresh["negative_old_waypoint"]["log"]
    assert fresh["capture"]["exit_code"] == 0
    output = []
    for original in rows:
        row = copy.deepcopy(original)
        entry = after[row["id"]]
        assert row["status"] == "captured"
        assert row["expected_frame"] == entry["boot"]["frame_hash"]
        assert row["expected_audio"] == entry["audio"]["hash"]
        assert row["frame_matches"] == (row["frame_hash"] == row["expected_frame"])
        assert row["audio_matches"] == (row["audio_hash"] == row["expected_audio"])
        row["observation"] = "reused_previous_sweep"
        if row["id"] == RAINBOW:
            row["frame_hash"] = fresh["observed"]["boot.frame_hash"]
            row["audio_hash"] = fresh["observed"]["audio.hash"]
            row["frame_matches"] = row["frame_hash"] == row["expected_frame"]
            row["audio_matches"] = row["audio_hash"] == row["expected_audio"]
            assert row["frame_matches"] and row["audio_matches"]
            row["seconds"] = fresh["capture"]["seconds"]
            row["observation"] = "fresh_capture"
        output.append(row)
    failures = [
        row["id"]
        for row in output
        if not (row["frame_matches"] and row["audio_matches"])
    ]
    assert len(failures) == 9
    return {
        "kind": "combined ledger; not a fresh full sweep",
        "prior_source": "eed1923b47965069b342194563b0b83849f6a5d5",
        "fresh_source": "9bb16aafbc0a8b62acc825c0ab6e63c003da8009",
        "fresh": 1,
        "reused": 102,
        "completed": 103,
        "matching": 94,
        "remaining": failures,
        "results": output,
    }


def main() -> None:
    old, new, previous, fresh, destination = map(Path, sys.argv[1:])
    arguments = (
        tomllib.loads(old.read_text()),
        tomllib.loads(new.read_text()),
        json.loads(previous.read_text()),
        json.loads(fresh.read_text()),
    )
    report = reconcile(*arguments)
    rejected = []
    for label in ["empty", "missing", "duplicate", "changed_other_entry"]:
        bad = copy.deepcopy(arguments)
        if label == "empty":
            bad[2]["results"] = []
        elif label == "missing":
            bad[2]["results"].pop()
        elif label == "duplicate":
            bad[2]["results"][-1] = copy.deepcopy(bad[2]["results"][0])
        else:
            bad[1]["entry"][0]["boot"]["wait_frames"] += 1
        try:
            reconcile(*bad)
        except AssertionError:
            rejected.append(label)
        else:
            raise AssertionError(f"Negative control accepted: {label}")
    report["rejected_controls"] = rejected
    destination.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: report[key]
                for key in [
                    "kind",
                    "fresh",
                    "reused",
                    "matching",
                    "remaining",
                    "rejected_controls",
                ]
            }
        )
    )


if __name__ == "__main__":
    main()
