# Inspect the MARIA layout's interrupt circuit

Engineering-frontier research for #197. The factory-pattern scan found no
positive enabled-NMI timing oracle. The archive also contains `MARIAPAL.GDS`.
Its README describes a proprietary format, but a preliminary record walk
matches the record framing in Calma's *GDSII Stream Format, Release 5.1*,
August 1984, printed page 6. Verify this before interpreting circuit behaviour.

Archive SHA-256:
`849e215c71d13c17ec813f97a23b2078469c4b1e14a36dcd5a9ccf72b5360a48`.
Member `MARIAS/GDS/MARIAPAL.GDS` SHA-256:
`9e9d9c2cff62357dadf9ef434a045efdfcc3014ae0f38bea6fb392b3e0df8db7`.
Originals stay read-only and outside the public docs repo.

1. In `2026-10-11-maria-layout-evidence/inspect_layout.py`, validate the record
   chain from byte 2, identify the partial initial structure, and retain only
   complete named structures. Reject malformed lengths/types and missing
   structure ends. Do not invent the absent library header, units or name.
   Record the leading fragment and trailing bytes separately.
2. Inventory labels and geometry in `VCELL_VCELL_GINGER$LOE_RSYNC_LY`, which
   contains `dlireq`, `haltclk` and `intf`, and its complete dependency closure.
   Render its native coordinates and explicitly numbered layers to a local
   image using the already-installed Matplotlib. Validate known geometry,
   missing/truncated records and nonzero inventories before trusting the view.
3. Establish layer meanings and relevant connectivity from the artefact and
   primary documentation before deriving a circuit. A text label near a shape
   is not proof of an electrical connection. Record revision uncertainty:
   the filename alone does not prove identity with production PAL silicon.
4. If the standalone interrupt path can be recovered, compare its topology
   and phase relationships with the hybrid schematic and qualified FPGA
   traces. Keep geometry recovery, circuit inference and simulated behaviour
   separate. Production NMI timing changes only after that evidence gate.

Sources: [GCC MARIA archive](https://7800.8bitdev.org/images/0/06/GCC_MARIA_Chip_Layout_and_Netlist_Artifacts.zip)
and [Calma's 1984 format manual](https://www.bitsavers.org/pdf/calma/GDS_II_Stream_Format_5.1_Aug84.pdf).
No production code, dependency, schema or pipeline design change is involved.

## Recovery result

The pinned member is 3,915,776 bytes. A chain beginning at byte 2 contains
326,054 records through ENDLIB at byte 3,915,404. It includes 563 complete
named cells. The first complete cell begins at byte 53,584, after 4,215
records in an opening fragment. The 368 trailing bytes are recorded and
excluded. The missing library header, units and first cell name stay unknown.

The target interrupt-related cell is flat, with 1,050 polygons and 45 text
elements on layers 1–7. It has no subcell dependencies. Its labels include
`intset`, `intrst`, `intq`, `intqf`, `intf`, `dlireq`, `haltclk`, `halt`,
`ph1`, `ph2` and `pckedge`. The local render was inspected: it shows a
coherent layout with distinct supply rails and labelled signal anchors.
Labels are drawn at their stored coordinates using a readable fixed font;
text magnification, presentation and rotation are not reproduced. No
connectivity or transistor interpretation has been performed.

Four synthetic tests cover record framing, complete-cell extraction,
malformed/truncated input, coordinates and text. All pass. Corrupting the
first complete structure's data-type byte fails with:

```text
unsupported record 05/0 at byte 53584
```

Ruff lint and format checks pass. The own code and summary are retained;
third-party geometry and the rendered layout stay in the local research
workspace. This is a recovered source for further analysis, not an NMI
schedule or a production-silicon identity claim.

## Reproduction

The render uses Matplotlib already installed in the research environment.
The record/geometry tests and summary generation use only the standard library.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s plans/2026-10-11-maria-layout-evidence -v
MPLCONFIGDIR=/path/to/temp-mpl-cache python3 \
  plans/2026-10-11-maria-layout-evidence/inspect_layout.py \
  /path/to/layout-artifacts.zip /path/to/summary.json \
  --render /path/to/rsync-layout.png
```

Omit `--render` for the standard-library-only inventory. The parser is bounded
to the observed record types and this flat target. Referenced-cell geometry
fails explicitly until reference transforms are modelled; it is not silently
omitted from a view.
