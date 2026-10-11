"""Compile unchanged NES size methods and compare every size-byte encoding."""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def function(source: str, signature: str) -> str:
    """Extract one balanced function body; missing signatures fail the run."""
    start = source.index(signature)
    cursor = source.index("{", start) + 1
    depth = 1
    while depth:
        depth += (source[cursor] == "{") - (source[cursor] == "}")
        cursor += 1
    return source[start:cursor]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path, help="Mesen2 checkout")
    parser.add_argument("production", type=Path, help="Emu198x checkout")
    parser.add_argument("output", type=Path, help="Private build/output directory")
    parser.add_argument("--rustc", default="rustc")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    reference = args.reference / "Core/NES/NesHeader.cpp"
    production = args.production / "crates/format-nintendo-nes-ines/src/format.rs"
    methods = "\n".join(
        function(reference.read_text(), "uint32_t NesHeader::" + name + "(")
        for name in ["GetSizeValue", "GetPrgSize", "GetChrSize"]
    )
    cpp = (
        """#include <cstdint>
#include <cstdio>
struct MessageManager { static void Log(const char*) {} };
enum class RomHeaderVersion { Nes2_0 };
struct NesHeader {
 uint8_t Byte9,PrgCount,ChrCount;
 RomHeaderVersion GetRomHeaderVersion() {return RomHeaderVersion::Nes2_0;}
 uint32_t GetSizeValue(uint32_t,uint32_t); uint32_t GetPrgSize(); uint32_t GetChrSize();
};
"""
        + methods
        + """
int main(){for(unsigned high=0;high<16;high++)for(unsigned low=0;low<256;low++) {
 NesHeader h{uint8_t(high|(high<<4)),uint8_t(low),uint8_t(low)};
 printf("%u,%u,%u,%u\\n",high,low,h.GetPrgSize(),h.GetChrSize());}}
"""
    )
    rust = (
        function(production.read_text(), "fn nes2_rom_size(")
        + """
fn main() {for high in 0..16 {for low in 0..=255 {
 println!("{high},{low},{:?},{:?}",nes2_rom_size(low,high,16384),nes2_rom_size(low,high,8192));}}}
"""
    )
    cpp_path = args.output / "reference_sizes.cpp"
    rust_path = args.output / "production_sizes.rs"
    cpp_path.write_text(cpp)
    rust_path.write_text(rust)
    ref_bin = args.output / "reference_sizes"
    prod_bin = args.output / "production_sizes"
    subprocess.run(
        ["clang++", "-std=c++20", str(cpp_path), "-o", str(ref_bin)], check=True
    )
    subprocess.run([args.rustc, str(rust_path), "-o", str(prod_bin)], check=True)
    ref_output = subprocess.check_output([str(ref_bin)], text=True)
    prod_output = subprocess.check_output([str(prod_bin)], text=True)
    (args.output / "reference-sizes.csv").write_text(ref_output)
    (args.output / "production-sizes.csv").write_text(prod_output)
    ref_rows, prod_rows = ref_output.splitlines(), prod_output.splitlines()
    if len(ref_rows) != 4096 or len(prod_rows) != 4096:
        raise ValueError("Expected 4096 rows from each compiled reader")
    matched = outside_reference = unrepresentable = 0
    for ref, prod in zip(ref_rows, prod_rows, strict=True):
        high, low, prg, chr_size = map(int, ref.split(","))
        rust_high, rust_low, rust_prg, rust_chr = prod.split(",")
        if (high, low) != (int(rust_high), int(rust_low)):
            raise ValueError(f"Header mismatch: {ref!r}, {prod!r}")
        for unit, reference_size, actual in [
            (16384, prg, rust_prg),
            (8192, chr_size, rust_chr),
        ]:
            expected = (
                2 ** (low >> 2) * (2 * (low & 3) + 1)
                if high == 15
                else ((high << 8) | low) * unit
            )
            if expected < 2**32:
                if reference_size != expected or actual != f"Some({reference_size})":
                    raise ValueError(f"Reference mismatch: {ref!r}, {prod!r}")
                matched += 1
            else:
                outside_reference += 1
            expected_result = "None" if expected >= 2**64 else f"Some({expected})"
            if actual != expected_result:
                raise ValueError(f"Integer mismatch: {ref!r}, {prod!r}")
            unrepresentable += expected >= 2**64
    result = {
        "headers": 4096,
        "size_results": 8192,
        "matching_32bit_reference": matched,
        "outside_32bit_reference": outside_reference,
        "rejected_unrepresentable": unrepresentable,
        "reference_sha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
    }
    (args.output / "comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
