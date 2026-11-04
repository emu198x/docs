"""Reconstruct all eight complete recordings using both production sound versions."""

import hashlib
import json
import math
import os
import struct
import wave
from pathlib import Path

ROOT = Path(
    os.environ.get("EMU198X_FOUR_EVIDENCE_ROOT", str(Path(__file__).resolve().parent))
)
IDS = ["cybernoid-plus3", "stormlord-plus3", "tetris-plus3", "dragon-ninja-plus3"]


def f32(number: float) -> float:
    return struct.unpack("<f", struct.pack("<f", number))[0]


def pcm16(value: float) -> int:
    value = max(-1.0, min(1.0, value))
    if value <= -1.0:
        return -32768
    scaled = f32(value * 32767.0)
    return math.floor(scaled + 0.5) if scaled >= 0 else math.ceil(scaled - 0.5)


report = []
for source in ["original", "current"]:
    for identifier in IDS:
        d = ROOT / "observations" / source / identifier
        old, new = [
            (d / f"replay-{label}.f32").read_bytes()
            for label in ["original", "current"]
        ]
        assert old == new and len(new) == 88200 * 4
        before, after = [
            (d / f"beeper-replay-{label}.f32").read_bytes()
            for label in ["original", "current"]
        ]
        assert before == after and len(after) == 88200 * 4
        output = bytearray()
        for (a,), (b,) in zip(
            struct.iter_unpack("<f", new), struct.iter_unpack("<f", after), strict=True
        ):
            output.extend(struct.pack("<h", pcm16(f32(b + f32(a * 0.5)))))
        with wave.open(str(d / "audio.wav")) as original:
            assert (
                original.getnchannels(),
                original.getsampwidth(),
                original.getframerate(),
                original.getnframes(),
            ) == (1, 2, 44100, 88200)
            actual = original.readframes(88200)
        assert output == actual, (source, identifier, "full mixed PCM mismatch")
        assert (d / "audio.wav").read_bytes() == (
            ROOT / "captures" / source / identifier / "audio.wav"
        ).read_bytes()
        report.append(
            {
                "source": source,
                "id": identifier,
                "samples": 88200,
                "complete_pcm_reconstructed": True,
                "ay_versions_bit_identical": True,
                "speaker_versions_bit_identical": True,
                "speaker_silent_throughout_window": all(
                    v == 0 for (v,) in struct.iter_unpack("<f", after)
                ),
                "pcm_sha256": hashlib.sha256(output).hexdigest(),
            }
        )
assert len(report) == 8
assert pcm16(f32(-0.5 / 32767.0)) == -1 and pcm16(f32(0.5 / 32767.0)) == 1
(ROOT / "audio-reconstruction.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
