"""Check every captured guest byte and reproduce the generated ROM hashes."""

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path


def verify() -> None:
    root = Path(__file__).resolve().parent
    report = json.loads((root / "mesen-results.json").read_text())
    assert len(report["cases"]) == 4
    assert [row["mode"] for row in report["cases"]] == list(range(4))
    with tempfile.TemporaryDirectory() as scratch:
        temp = Path(scratch)
        binary = temp / "generate"
        subprocess.run(
            ["rustc", "--edition=2024", str(root / "generate.rs"), "-o", str(binary)],
            check=True,
        )
        subprocess.run([str(binary), str(temp / "roms")], check=True)
        for row, pages in zip(
            report["cases"], [[0, 0], [1, 1], [0, 1], [0, 0]], strict=True
        ):
            mode = row["mode"]
            rom = temp / "roms" / f"mode{mode}.nes"
            assert hashlib.sha256(rom.read_bytes()).hexdigest() == row["rom_sha256"]
            expected = bytearray()
            for i in range(2048):
                physical = pages[i // 1024] * 1024 + i % 1024
                expected.append((physical & 255) ^ ((physical // 256) * 17))
            for repeat in range(2):
                observed = bytes.fromhex(
                    (root / f"mesen-mode{mode}-{repeat}.txt").read_text()
                )
                assert len(observed) == 2048
                assert observed == expected, (mode, repeat)
    print("4 modes, 2048 bytes each, 2 captures each: exact; 4 ROM hashes reproduced")


if __name__ == "__main__":
    verify()
