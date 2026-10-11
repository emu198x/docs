"""Capture Altirra's unchanged settled-period calculation for unlinked timers."""

import argparse
import hashlib
import itertools
import json
import subprocess
from pathlib import Path

SOURCE_HASH = "04cda7768564545e1d8a53271357805d32020a3b3ceef81ca1219b1b69ea82e9"
PREAMBLE = r"""
#include <cstdint>
#include <cstdio>
#include <cstdlib>
using uint8 = uint8_t;
using uint32 = uint32_t;
struct ATPokeyEmulator {
    bool mbFastTimer1 = false, mbFastTimer3 = false;
    bool mbLinkedTimers12 = false, mbLinkedTimers34 = false, mbUse15KHzClock = false;
    bool mbNotifyBiClockChange = false;
    uint8 mSKCTL = 3, mAUDF[4] {};
    uint32 mAUDFP1B[4] {1, 1, 1, 1}, mTimerPeriod[4] {}, mTimerFullPeriod[2] {};
    void (*mpNotifyBiClockChangeFn)() = [] { std::abort(); };
    template<int channel> void RecomputeTimerPeriod();
};
"""
DRIVER = r"""
template<int channel> void capture() {
    for (int mode = 0; mode < 3; ++mode)
    for (int frequency = 0; frequency < 256; ++frequency) {
        ATPokeyEmulator p;
        p.mbFastTimer1 = p.mbFastTimer3 = mode == 2;
        p.mbUse15KHzClock = mode == 1;
        p.mAUDF[channel] = uint8(frequency);
        p.mAUDFP1B[channel] = frequency + 1;
        p.RecomputeTimerPeriod<channel>();
        std::printf("%d %d %d %u\n", channel, mode, frequency, p.mTimerPeriod[channel]);
    }
}
int main() { capture<0>(); capture<1>(); capture<2>(); capture<3>(); }
"""


def verify(text: str) -> int:
    rows = [tuple(map(int, line.split())) for line in text.splitlines()]
    expected = set(itertools.product(range(4), range(3), range(256)))
    if len(rows) != len(expected) or {row[:3] for row in rows} != expected:
        raise ValueError("incomplete period inventory")
    for channel, mode, frequency, period in rows:
        documented = (
            frequency + 4
            if mode == 2 and channel in (0, 2)
            else (frequency + 1) * (114 if mode == 1 else 28)
        )
        if period != documented:
            raise ValueError("reference contradicts documented period")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("scratch", type=Path)
    args = parser.parse_args()
    raw = args.source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_HASH:
        raise ValueError("reference source hash mismatch")
    source = raw.decode().replace("\r\n", "\n")
    start = "template<int channel>\nvoid ATPokeyEmulator::RecomputeTimerPeriod()"
    end = "\nvoid ATPokeyEmulator::RecomputeAllowedDeferredTimers()"
    if source.count(start) != 1 or source.count(end) != 1:
        raise ValueError("ambiguous function boundary")
    function = source[source.index(start) : source.index(end)]
    args.scratch.mkdir(parents=True, exist_ok=True)
    cpp, binary = args.scratch / "period.cpp", args.scratch / "period"
    cpp.write_text(PREAMBLE + function + DRIVER)
    subprocess.run(
        [
            "clang++",
            "-std=c++17",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            str(cpp),
            "-o",
            str(binary),
        ],
        check=True,
    )
    captured = subprocess.check_output([str(binary)], text=True)
    summary = {
        "cases": verify(captured),
        "source_sha256": SOURCE_HASH,
        "function_sha256": hashlib.sha256(function.encode()).hexdigest(),
        "vectors_sha256": hashlib.sha256(captured.encode()).hexdigest(),
    }
    (args.scratch / "periods.txt").write_text(captured)
    (args.scratch / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
