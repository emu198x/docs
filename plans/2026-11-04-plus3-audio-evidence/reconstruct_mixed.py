"""Reconstruct complete mixed PCM using observed commands and production mixers."""

import hashlib
import json
import math
import os
import struct
from pathlib import Path

import analyse

ROOT = Path(
    os.environ.get("EMU198X_AUDIO_EVIDENCE_ROOT", str(Path(__file__).resolve().parent))
)


def f32(number: float) -> float:
    return struct.unpack("<f", struct.pack("<f", number))[0]


def pcm16(value: float) -> int:
    value = max(-1.0, min(1.0, value))
    if value <= -1.0:
        return -32768
    scaled = f32(value * 32767.0)
    # Rust f32::round uses ties away from zero, including negative half-ties.
    return math.floor(scaled + 0.5) if scaled >= 0 else math.ceil(scaled - 0.5)


def main() -> None:
    assert pcm16(f32(-0.5 / 32767.0)) == -1
    assert pcm16(f32(0.5 / 32767.0)) == 1
    report = []
    for label in ["original", "current"]:
        for name in ["chase-hq-plus3", "where-time-stood-still-plus3"]:
            directory = ROOT / "fe-control/observations" / label / name
            old, new = [
                (directory / f"beeper-replay-{version}.f32").read_bytes()
                for version in ["original", "current"]
            ]
            assert old == new and len(old) == 88200 * 4
            ay = (
                ROOT / "observations" / label / name / "replay-current.f32"
            ).read_bytes()
            output = bytearray()
            for (a,), (b,) in zip(
                struct.iter_unpack("<f", ay), struct.iter_unpack("<f", new), strict=True
            ):
                output.extend(struct.pack("<h", pcm16(f32(b + f32(a * 0.5)))))
            actual = analyse.pcm(directory / "audio.wav")
            assert (directory / "audio.wav").read_bytes() == (
                ROOT / "observations" / label / name / "audio.wav"
            ).read_bytes()
            assert output == actual, (label, name, "PCM reconstruction differs")
            report.append(
                {
                    "producer": label,
                    "id": name,
                    "complete_pcm_reconstructed": True,
                    "samples": 88200,
                    "pcm_sha256": hashlib.sha256(output).hexdigest(),
                    "beeper_versions_bit_identical": True,
                }
            )
    (ROOT / "mixed-pcm-reconstruction.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report))


if __name__ == "__main__":
    main()
