"""Build an isolated VICE observer, preserving the unmodified baseline binary."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], cwd: Path, log: Path) -> None:
    with log.open("w") as output:
        subprocess.run(
            command, cwd=cwd, stdout=output, stderr=subprocess.STDOUT, check=True
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--instrument-existing", action="store_true")
    args = parser.parse_args()
    reference, output = args.reference.resolve(), args.output.resolve()
    source = output / "source"
    assert not output.is_relative_to(reference), "do not build inside the reference"
    evidence = Path(__file__).resolve().parent
    pinned = json.loads((evidence / "fetch-trace-baseline.json").read_text())["build"][
        "source_sha256"
    ]
    patch = evidence / "fetch_trace.patch"
    if not args.instrument_existing:
        output.mkdir(exist_ok=False)
        shutil.copytree(reference, source, ignore=shutil.ignore_patterns(".git"))
        run(
            ["./configure", "--enable-headlessui", "--disable-html-docs"],
            source,
            output / "configure.log",
        )
        run(["make", "-j8", "-C", "src"], source, output / "build-baseline.log")
        shutil.copy2(source / "src/x64sc", output / "x64sc-baseline")
    assert source.resolve() != reference and (output / "x64sc-baseline").is_file()
    touched = [
        "src/viciisc/vicii-fetch.c",
        "src/viciisc/vicii-fetch.h",
        "src/viciisc/vicii-cycle.c",
    ]
    for rel in touched:
        assert (source / rel).read_bytes() == (reference / rel).read_bytes(), rel
        if rel in pinned:
            assert digest(source / rel) == pinned[rel], "unexpected reference revision"
    run(
        ["patch", "--dry-run", "-p1", "-i", str(patch)],
        source,
        output / "patch-check.log",
    )
    run(["patch", "-p1", "-i", str(patch)], source, output / "patch.log")
    run(
        ["make", "-j8", "-C", "src/viciisc"], source, output / "build-observer-chip.log"
    )
    run(["make", "-j8", "-C", "src", "x64sc"], source, output / "build-observer.log")
    shutil.copy2(source / "src/x64sc", output / "x64sc-trace")
    manifest = {
        "patch_sha256": digest(patch),
        "baseline_sha256": digest(output / "x64sc-baseline"),
        "observer_sha256": digest(output / "x64sc-trace"),
        "sources": {
            rel: {"before": digest(reference / rel), "after": digest(source / rel)}
            for rel in touched
        },
    }
    (output / "observer-build.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
