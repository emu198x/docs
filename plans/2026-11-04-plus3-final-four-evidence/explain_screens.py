"""Account for picture differences using complete observed guest screen writes."""

import hashlib
import json
import os
import sys
import tomllib
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(
    os.environ.get("EMU198X_FOUR_EVIDENCE_ROOT", str(Path(__file__).resolve().parent))
)
sys.path.insert(0, str(ROOT / "prior/image-evidence-utility"))
from image_evidence import read_rgba

IDS = ["cybernoid-plus3", "stormlord-plus3", "tetris-plus3", "dragon-ninja-plus3"]


def read_cpu_window(memory: dict, pc: int) -> bytes:
    assert memory["paging_1ffd"] & 1 == 0 and pc >= 0x4008
    bank = 5 if pc < 0x8000 else 2 if pc < 0xC000 else memory["paging_7ffd"] & 7
    return bytes(memory["ram"][bank][(pc & 16383) - 8 : (pc & 16383) + 8])


report = {}
for identifier in IDS:
    data = []
    memories = []
    screens = []
    all_writes = []
    for label in ["original", "current"]:
        directory = ROOT / "observations" / label / identifier
        audit = tomllib.loads((directory / "audit.toml").read_text())
        continuation = sorted(
            tomllib.loads((directory / "continuation.toml").read_text()).values(),
            key=lambda f: f["field"],
        )
        fields = audit["fields"] + continuation
        assert len(fields) == 500
        assert [f["field"] for f in fields] == list(range(500))
        writes = [w for field in fields for w in field["screen_writes"]]
        assert writes
        all_writes.extend(writes)
        data.append(fields)
        memory = tomllib.loads((directory / "boot-memory.toml").read_text())
        memories.append(memory)
        bank = 7 if memory["paging_7ffd"] & 8 else 5
        screens.append(bytes(memory["ram"][bank][:6912]))
    addresses = {w["addr"] for w in all_writes}
    pcs = sorted({w["pc"] for w in all_writes})
    changed = {
        i + 0x4000 for i, (a, b) in enumerate(zip(*screens, strict=True)) if a != b
    }
    assert changed <= addresses, (
        identifier,
        "screen changes outside guest-write range",
        changed - addresses,
    )
    influence = set()
    for address in addresses:
        offset = address - 0x4000
        if offset < 6144:
            y = ((offset >> 8) & 7) | ((offset >> 2) & 0x38) | ((offset >> 5) & 0xC0)
            x = (offset & 31) * 8
            influence.update((48 + x + bit, 48 + y) for bit in range(8))
        else:
            y = ((address - 0x5800) // 32) * 8
            x = ((address - 0x5800) % 32) * 8
            influence.update(
                (48 + x + bit, 48 + y + line) for line in range(8) for bit in range(8)
            )
    images = [
        read_rgba(ROOT / "captures" / label / identifier / "frame.png", 352, 296)
        for label in ["original", "current"]
    ]
    changes = {
        (i % 352, i // 352)
        for i in range(352 * 296)
        if images[0][4 * i : 4 * i + 4] != images[1][4 * i : 4 * i + 4]
    }
    assert changes <= influence, (
        identifier,
        "pixels changed outside observed guest activity",
    )
    same_code = []
    changed_code = []
    neighboring = []
    for pc in pcs:
        a, b = [read_cpu_window(m, pc) for m in memories]
        assert a[6:8] == b[6:8], (identifier, pc, "writer instruction suffix changed")
        for offset, (old, new) in enumerate(zip(a, b, strict=True)):
            if old != new:
                neighboring.append(
                    {
                        "writer_pc": pc,
                        "relative_byte": offset - 8,
                        "old": old,
                        "current": new,
                    }
                )
        if a == b:
            same_code.append(pc)
        else:
            changed_code.append(pc)
    old_hashes, new_hashes = [{f["frame_hash"] for f in fields} for fields in data]
    scores = []
    for shift in range(-499, 500):
        pairs = [
            (f["frame_hash"], data[1][i + shift]["frame_hash"])
            for i, f in enumerate(data[0])
            if 0 <= i + shift < 500
        ]
        count = sum(a == b for a, b in pairs)
        if count:
            scores.append((count, len(pairs), shift))
    result = {
        "observed_fields_per_producer": 500,
        "guest_screen_writes": len(all_writes),
        "distinct_written_bytes": len(addresses),
        "changed_boundary_screen_bytes": len(changed),
        "every_changed_byte_written_by_original_program": True,
        "changed_pixels": len(changes),
        "pixels_in_observed_guest_write_footprint": len(influence),
        "unchanged_pixels_outside_footprint": 352 * 296 - len(influence),
        "unchanged_active_pixels_outside_footprint": 256 * 192 - len(influence),
        "every_changed_pixel_in_guest_write_footprint": True,
        "identical_writer_code_windows": same_code,
        "different_writer_code_windows": changed_code,
        "all_writer_instruction_suffixes_identical": True,
        "neighboring_state_changes_in_wide_windows": neighboring,
        "current_fields_exactly_observed_in_old_timeline": sum(
            f["frame_hash"] in old_hashes for f in data[1]
        ),
        "old_fields_exactly_observed_in_current_timeline": sum(
            f["frame_hash"] in new_hashes for f in data[0]
        ),
        "best_constant_field_alignment": sorted(scores, reverse=True)[:3],
        "boundary_screen_sha256": [hashlib.sha256(s).hexdigest() for s in screens],
    }
    report[identifier] = result
    print(
        identifier,
        {
            k: result[k]
            for k in [
                "changed_boundary_screen_bytes",
                "changed_pixels",
                "unchanged_active_pixels_outside_footprint",
                "different_writer_code_windows",
                "current_fields_exactly_observed_in_old_timeline",
            ]
        },
        flush=True,
    )
(ROOT / "screen-explanation.json").write_text(json.dumps(report, indent=2) + "\n")
