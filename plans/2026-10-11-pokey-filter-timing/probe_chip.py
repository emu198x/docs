"""Run the public POKEY diagnostic without leaving a failing test installed."""

import argparse
import subprocess
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("log", type=Path)
    parser.add_argument("--target-dir", type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    target = source / "crates/atari-pokey/tests/filter_timing_probe.rs"
    probe = Path(__file__).with_name("probe.rs").read_bytes()
    with target.open("xb") as output:
        output.write(probe)
    try:
        command = [
            "cargo",
            "test",
            "-p",
            "atari-pokey",
            "--test",
            "filter_timing_probe",
        ]
        if args.target_dir:
            command.extend(("--target-dir", str(args.target_dir.resolve())))
        command.extend(("--", "--nocapture"))
        with args.log.open("wb") as log:
            result = subprocess.run(
                command, cwd=source, stdout=log, stderr=subprocess.STDOUT, check=False
            )
    finally:
        if target.read_bytes() != probe:
            raise RuntimeError("probe changed concurrently; left intact")
        target.unlink()
    print(f"cargo exit {result.returncode}; output: {args.log}")
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
