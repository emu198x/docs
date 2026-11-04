"""Verify complete paired observations; publish summaries, never music data."""

import collections
import csv
import hashlib
import json
import math
import os
import struct
import tomllib
import wave
from pathlib import Path

ROOT = Path(
    os.environ.get("EMU198X_AUDIO_EVIDENCE_ROOT", str(Path(__file__).resolve().parent))
)
IDS = [
    "chase-hq-plus3",
    "starglider-2-plus3",
    "lotus-esprit-plus3",
    "robocop-plus3",
    "where-time-stood-still-plus3",
]


def read(path: Path) -> dict:
    return tomllib.loads(path.read_text())


def stream(path: Path, tag: str = "AY_EDGE") -> list[tuple]:
    frame = 0
    rows = []
    for line in path.read_text().splitlines():
        if line == "AY_NATIVE_FRAME":
            frame += 1
        elif line.startswith(tag + " "):
            values = tuple(map(int, line.split()[1:]))
            rows.append((frame * 354540 + values[0], *values[1:]))
    assert rows
    return rows


def commands(rows: list[tuple]) -> list[tuple]:
    return [row[1:] for row in rows]


def require_prefix(a: list[tuple], b: list[tuple]) -> int:
    count = min(len(a), len(b))
    assert count > 10000, "incomplete/nonempty command requirement"
    assert a[:count] == b[:count], "command stream changed"
    return count


def pcm(path: Path) -> bytes:
    with wave.open(str(path)) as source:
        assert (
            source.getnchannels(),
            source.getsampwidth(),
            source.getframerate(),
            source.getnframes(),
        ) == (1, 2, 44100, 88200)
        return source.readframes(88200)


def quantize(data: bytes) -> bytes:
    assert len(data) == 88200 * 4
    result = bytearray()
    f32 = lambda value: struct.unpack("<f", struct.pack("<f", value))[0]
    for (value,) in struct.iter_unpack("<f", data):
        value = f32(f32(value * 0.5) * 32767.0)
        result.extend(struct.pack("<h", math.floor(value + 0.5)))
    return bytes(result)


def main() -> None:
    report = {}
    for identifier in IDS:
        paths = [
            ROOT / "observations" / label / identifier
            for label in ["original", "current"]
        ]
        audits = [read(p / "audit.toml") for p in paths]
        states = [read(p / "before-ay.toml")["inner"] for p in paths]
        for path, audit in zip(paths, audits, strict=True):
            assert audit["id"] == identifier and len(audit["fields"]) == 100
            assert [f["field"] for f in audit["fields"]] == list(range(100))
            continuation = sorted(
                read(path / "continuation.toml").values(), key=lambda f: f["field"]
            )
            assert len(continuation) == 400 and [
                f["field"] for f in continuation
            ] == list(range(100, 500))
            assert audit["end_time"] - audit["start_time"] == 35454000
            assert all(
                b["time"] - a["time"] == 354540
                for a, b in zip(audit["fields"], audit["fields"][1:])
            )
        delta = audits[1]["start_time"] - audits[0]["start_time"]
        assert delta == 354540
        assert (states[0]["prescaler"] + delta // 10) % 8 == states[1]["prescaler"]
        assert (states[0]["sample_error"] + (delta // 10) * 44100) % 1773447 == states[
            1
        ]["sample_error"]
        rows = [stream(path / "observer.log") for path in paths]
        sequences = [commands(row) for row in rows]
        muted_extra = 0
        if identifier == "starglider-2-plus3":
            assert len([x for x in sequences[0] if x[0] == 52630]) == 2048
            assert len([x for x in sequences[1] if x[0] == 52630]) == 2052
            assert sequences[1][2050:2054] == [
                (52630, 8, 0),
                (52630, 9, 0),
                (52630, 10, 0),
                (52630, 7, 56),
            ]
            assert sequences[0][2046:2050] == sequences[1][2050:2054]
            sequences[1] = sequences[1][:2050] + sequences[1][2054:]
            muted_extra = 4
        count = require_prefix(*sequences)
        pc = collections.Counter(row[1] for row in rows[1]).most_common(1)[0][0]
        music = [[row for row in data if row[1] == pc] for data in rows]
        assert commands(music[0])[: len(music[1])] == commands(music[1])
        edges = collections.Counter(b[0] - a[0] for a, b in zip(*music))
        replay = []
        for path in paths:
            old, new = [
                (path / f"replay-{label}.f32").read_bytes()
                for label in ["original", "current"]
            ]
            assert old == new and len(old) == 88200 * 4, (
                "AY versions differ for identical timed input"
            )
            reconstructed = quantize(new)
            actual = pcm(path / "audio.wav")
            exact = reconstructed == actual
            if identifier not in ["chase-hq-plus3", "where-time-stood-still-plus3"]:
                assert exact, (identifier, "PCM reconstruction differs")
            replay.append(
                {
                    "same_f32_on_both_versions": True,
                    "samples": 88200,
                    "f32_sha256": hashlib.sha256(new).hexdigest(),
                    "complete_pcm_reconstructed": exact,
                }
            )
        independent = []
        reference = ROOT / "reference" / identifier / "ay.tsv"
        refs = list(csv.DictReader(reference.open(), delimiter="\t"))

        def pack(writes: list[dict]) -> bytes:
            return b"".join(
                struct.pack("<HBB", int(w["pc"]), int(w["register"]), int(w["value"]))
                for w in writes
            )

        haystack = pack(refs)
        for audit in audits:
            writes = [w for field in audit["fields"] for w in field["writes"]]
            needle = pack(writes)
            assert needle
            position = haystack.find(needle)
            matched = position >= 0 and position % 4 == 0
            if identifier in IDS[:3]:
                assert matched, (identifier, "independent commands differ")
            independent.append(
                {
                    "complete_command_window_matches": matched,
                    "commands": len(writes),
                    "reference_start_seconds": float(refs[position // 4]["time"])
                    if matched
                    else None,
                }
            )
        report[identifier] = {
            "frame_hash_unchanged": audits[0]["boot_hash"] == audits[1]["boot_hash"],
            "old_audio_hash": audits[0]["audio_hash"],
            "current_audio_hash": audits[1]["audio_hash"],
            "capture_start_delta_ticks": delta,
            "music_pc": pc,
            "first_music_write_old_ticks": music[0][0][0],
            "first_music_write_current_ticks": music[1][0][0],
            "music_start_frame_delta": (music[1][0][0] // 354540)
            - (music[0][0][0] // 354540),
            "whole_command_prefix": count,
            "muted_startup_extra": muted_extra,
            "music_commands_compared": len(music[1]),
            "write_edge_deltas": dict(sorted(edges.items())),
            "global_prescaler_and_sample_error_predicted": True,
            "replay": replay,
            "reference": independent,
        }
        assert report[identifier]["frame_hash_unchanged"]
    mixed = json.loads((ROOT / "mixed-pcm-reconstruction.json").read_text())
    assert len(mixed) == 4 and all(
        row["complete_pcm_reconstructed"] and row["samples"] == 88200 for row in mixed
    )
    test = [(i,) for i in range(12000)]
    assert require_prefix(test, test) == 12000
    for left, right in [
        ([], []),
        (test, test[:-11000]),
        (test, test[:6000] + [(-1,)] + test[6001:]),
    ]:
        try:
            require_prefix(left, right)
        except AssertionError:
            pass
        else:
            raise AssertionError("bad evidence accepted")
    (ROOT / "analysis.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: {
                    k: value[k]
                    for k in [
                        "music_start_frame_delta",
                        "whole_command_prefix",
                        "muted_startup_extra",
                        "replay",
                        "reference",
                    ]
                }
                for key, value in report.items()
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
