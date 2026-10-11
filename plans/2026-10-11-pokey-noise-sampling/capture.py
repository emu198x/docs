"""Execute Altirra's unchanged noise-output transfer with exhaustive inputs."""

import argparse
import hashlib
import itertools
import json
import subprocess
from pathlib import Path

SOURCE_HASH = "d79effe1aa9967e50bb189ebec6fd1cb850e29e63d78ae878695409da9b29aa6"
START = "template<int activeChannel, uint8 audcn, bool outputAffectsSignal, bool T_UsePoly9>\nstd::pair<uint32 *, const uint32 *> ATPokeyRenderer::FireTimer("
END = "\nvoid ATPokeyRenderer::ProcessOutputEdges("

PREAMBLE = r"""
#include <cstdint>
#include <cstdio>
#include <utility>
using uint8 = uint8_t;
using uint32 = uint32_t;
using uintptr = uintptr_t;
#define VDRESTRICT
struct ATPokeyRenderer {
    uint8 mNoiseFlipFlops = 0;
    struct {
        uintptr mPoly4Offset, mPoly5Offset, mPoly9Offset, mPoly17Offset;
    } mPolyState;
    template<int activeChannel, uint8 audcn, bool outputAffectsSignal, bool T_UsePoly9>
    std::pair<uint32 *, const uint32 *> FireTimer(
        uint32 *dst, const uint32 *src, uint32 timeBase, uint32 timeLimit);
};
"""

DRIVER = r"""
template<int channel, int mode, bool poly9>
void capture() {
    for (int bits = 0; bits < 16; ++bits) {
        uint8 data[4] = {uint8(bits), uint8(bits), uint8(bits), uint8(bits)};
        for (int previous = 0; previous < 2; ++previous) {
            for (int fire = 0; fire < 2; ++fire) {
                ATPokeyRenderer renderer;
                renderer.mNoiseFlipFlops = uint8(previous << channel);
                const uintptr base = reinterpret_cast<uintptr>(data);
                renderer.mPolyState = {base, base, base, base};
                uint32 input[2] = {fire ? 0u : UINT32_MAX, UINT32_MAX};
                uint32 output[2] = {UINT32_MAX, UINT32_MAX};
                const auto result = renderer.FireTimer<channel, mode << 5, true, poly9>(
                    output, input, 0, 1);
                const auto count = result.first - output;
                if (result.second - input != fire || count < 0 || count > 1 ||
                    (count && output[0] != channel) ||
                    (renderer.mNoiseFlipFlops & ~(1 << channel))) {
                    std::fputs("invalid reference event inventory\n", stderr);
                    std::exit(2);
                }
                const int next = (renderer.mNoiseFlipFlops >> channel) & 1;
                std::printf("%d %d %d %d %d %d %d %td\n",
                    channel, mode, int(poly9), bits, previous, fire, next, count);
            }
        }
    }
}
template<int channel, bool poly9>
void modes() {
    capture<channel, 0, poly9>(); capture<channel, 1, poly9>();
    capture<channel, 2, poly9>(); capture<channel, 3, poly9>();
    capture<channel, 4, poly9>(); capture<channel, 5, poly9>();
    capture<channel, 6, poly9>(); capture<channel, 7, poly9>();
}
int main() {
    modes<0, false>(); modes<1, false>(); modes<2, false>(); modes<3, false>();
    modes<0, true>(); modes<1, true>(); modes<2, true>(); modes<3, true>();
}
"""


def verify(rows: list[tuple[int, ...]]) -> dict[str, int]:
    expected = set(
        itertools.product(range(4), range(8), range(2), range(16), range(2), range(2))
    )
    if len(rows) != len(expected) or {r[:6] for r in rows} != expected:
        raise ValueError("incomplete or duplicate reference inputs")
    updates = 0
    held = 0
    for channel, mode, poly9, bits, previous, fire, next_state, events in rows:
        clocked = fire and (mode & 4 or bits & 4)
        if not clocked:
            expected_state = previous
            held += 1
        elif mode & 1:
            expected_state = 1 - previous
        else:
            selected_bit = 3 if mode & 2 else (1 if poly9 else 0)
            expected_state = (bits >> selected_bit) & 1
        if next_state != expected_state:
            raise ValueError(
                f"reference transfer disagrees with documented selection: {channel, mode, bits}"
            )
        if events != int(next_state != previous):
            raise ValueError("reference event count disagrees with output change")
        updates += events
    return {"cases": len(rows), "changes": updates, "held_without_clock": held}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("scratch", type=Path)
    parser.add_argument("vectors", type=Path)
    parser.add_argument("summary", type=Path)
    args = parser.parse_args()
    raw = args.source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SOURCE_HASH:
        raise ValueError("reference source hash mismatch")
    source = raw.decode().replace("\r\n", "\n")
    if source.count(START) != 1 or source.count(END) != 1:
        raise ValueError("reference function boundary mismatch")
    function = source[source.index(START) : source.index(END)]
    args.scratch.mkdir(parents=True, exist_ok=True)
    cpp = args.scratch / "capture.cpp"
    binary = args.scratch / "capture"
    cpp.write_text("#include <cstdlib>\n" + PREAMBLE + function + DRIVER)
    subprocess.run(
        [
            "clang++",
            "-std=c++17",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-O2",
            str(cpp),
            "-o",
            str(binary),
        ],
        check=True,
    )
    capture = subprocess.run([str(binary)], check=True, text=True, capture_output=True)
    rows = [tuple(map(int, line.split())) for line in capture.stdout.splitlines()]
    result: dict[str, int | str] = dict(verify(rows))
    args.vectors.parent.mkdir(parents=True, exist_ok=True)
    args.vectors.write_text(
        "# channel mode poly9 bits previous fire next events\n" + capture.stdout
    )
    result.update(
        {
            "source_sha256": digest,
            "function_sha256": hashlib.sha256(function.encode()).hexdigest(),
            "vectors_sha256": hashlib.sha256(args.vectors.read_bytes()).hexdigest(),
        }
    )
    args.summary.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
