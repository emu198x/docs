# Keep browser player model controls within narrow screens

Lane: engineering-frontier shared tooling. Issue: emu198x/emu198x#2238.
Agreed approach: retain the native dropdown and existing label layout;
allow both flex items and their controls to shrink within the available width.

1. Add `web-player/check-layout.html` and `web-player/check-layout.mjs` using
   the real player template and CSS, with Amiga option names read from the
   runtime's `profiles.rs`. Exercise 320, 390 and 1280 CSS-pixel viewports in
   both themes using Chrome, including native keyboard selection and focus.
   Require document width, control bounds and usable target sizes to pass.
   Prove the narrow-screen assertion fails before editing CSS.
2. Fix only `.model-controls label` and its selects in
   `web-player/src/player.css`. Permit shrinking without hiding overflow,
   changing option names or replacing the native control.
3. Wire the browser regression into `.github/workflows/ci.yml`, document its
   command in `web-player/README.md`, inspect narrow/desktop screenshots, and
   rerun the regression with a deliberate old-CSS negative control.
4. Commit, push and merge after successful CI. Follow the existing producer
   release process for the versioned player package; do not patch a site's
   copied bundle or change its pin ahead of publication. Remove task-owned
   Chrome profiles, screenshots and processes after inspection.

## Verification

Before the fix, the browser regression failed with
`320/light: document overflows to 517px`. The flex label's automatic minimum
width retained the select's intrinsic width; `max-width: 100%` on the select
alone did not account for the label text and gap.

With the label constrained to its container and both flex items allowed to
shrink, all six viewport/theme combinations pass. Document widths are exactly
320, 390 and 1280 pixels. Both controls remain 44 pixels tall and within their
labels. Real Tab input reaches the model selector, its focus ring is visible,
and native character typeahead changes the selected model and emits `change`.
The actual 18 Amiga model names are read from the runtime, including the A501
and GVP A530 options.

The `--negative` control restores the old CSS constraints and fails with the
same 517-pixel overflow. Narrow dark and desktop light screenshots were
inspected. The CSS does not clip overflowing content. macOS native arrow-key
popups cannot be driven through CDP, so the keyboard regression uses native
typeahead, which runs in Blink on every platform.

The existing `check-presentation.mjs` passes at both device pixel ratios and
rejects its corrupt-source negative control. `node --check`, workflow
`actionlint` and `git diff --check` pass.

The site pin remains unchanged until a producer release publishes the fix.

All PR checks passed, including the Linux browser job and all four workspace
test shards. [PR #2298](https://github.com/emu198x/emu198x/pull/2298) merged on
2026-11-04; main retains the change at
`2f8ca932f4e88153b60ba6bfef6cae9794535338`. Issue #2238 remains open for the
versioned release and site-pin follow-through. Task-owned Chrome profiles,
screenshots and processes were removed after verification.
