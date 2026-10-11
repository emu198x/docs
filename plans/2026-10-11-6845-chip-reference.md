# Source-backed 6845 chip knowledge

Lane: engineering-frontier accuracy. This closes the documentation gap in
[issue #168](https://github.com/emu198x/emu198x/issues/168), not the remaining
interlace/skew implementation work in #166.

The shared primary library already holds MC6845 and HD6845R/S source metadata.
The private emulator chip entry exists but lacks the requested manufacturer
citations/register map and has outdated readback claims. No production change or
new dependency is needed to complete that documentation task.

1. Reacquire/verify the Motorola PDF against its existing sidecar hash. The
   standalone Hitachi URL returns 403, so use a separately hashed copy of the
   manufacturer's 1987 data book and record its distinct page numbering. Visually
   inspect register maps, address/raster timing, sync, R8 and cursor diagrams.
   Add a concise curated `198x/reference/by-topic/crtc-6845/6845-registers-and-signals.md`
   citing exact manufacturer pages; retain bulk sources locally.
2. Inspect `crates/motorola-6845/src/lib.rs` at current source main and its
   BBC/PET call sites. Distinguish implemented behaviour, intended equations
   and missing functionality; do not label comments as runtime evidence.
3. Correct `Emu198x/emu198x/knowledge/chips/motorola-6845.md`, index/log entries and
   explicit scoped private recovery copies under `198x/knowledge/private/`.
   Do not capture unrelated working knowledge changes.
4. Publish the implementation/reference boundary in the docs repo, with source
   commit and page citations. Verify relative links, exact recovery bytes and
   the issue's two acceptance items. Run focused chip checks only where they
   support implementation claims; no broad test run for prose edits.
5. Commit private reference/knowledge changes in the umbrella without pushing
   its unrelated divergent work. Commit/push/merge the public documentation
   separately, verify the merged tree, then close #168 with the evidence.

Any newly discovered chip behaviour defect gets its own reproduced, bounded
correction; it must not be concealed by documenting the desired behaviour as
though the implementation already achieved it.
