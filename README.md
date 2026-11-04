# Guided Matte for Flame — v0.4

Refine a rough matte using colour detail from the original plate. Full RGB
guided filtering based on Rafael Silva's rs_GuidedBlur 1.3 Nuke gizmo and
Guided Image Filtering by He, Sun and Tang (ECCV 2010).

## Current files

- `matchbox/`: the current unencrypted shader, XML, icon and licence texts.
- `publish.py`: copies `matchbox/` to `~/pipeline/flame/matchbox/GuidedMatte/` (`--dry-run` to preview, `--zip` to rebuild the release zip).
- The release zip is not in git; download it from the GitHub Release.
- `SUBMISSION_DESCRIPTION.md`: the approved Matchbook listing text.
- `SUBMISSION_NOTES.md`: exactly which files to upload.
- `build_shaders.py`: regenerates the 11 shader passes and XML in `matchbox`.
- `verify_math.py`: CPU maths and XML consistency checks.
- The original Nuke reference (`rs_GuidedBlur_v1_3.nk`) is not in git; it's on the NAS in `~/pipeline/dev/flame-guided-matte/`.
- `LICENSE.txt` and `THIRD_PARTY_NOTICES.txt`: MIT and upstream BSD notices.

## Publish and load in Flame

Run `python3 publish.py` (try `--dry-run` first). In Flame, add a Matchbox in Batch, browse to `~/pipeline/flame/matchbox/GuidedMatte`, choose GLSL mode and select the
grouped `GuidedMatte.glsl` entry. Flame groups the numbered passes; there is
no separate physical root GLSL file. Keep all passes and the XML together.

Connect the plate to Guide / Plate and a monochrome mask to Rough Matte.
Start with Blur Width 30 and Edge Detail 3.5. Mix blends back towards the
original matte; Clamp Matte optionally limits the filtered result to 0–1.
Use F4 to view the matte. The image output preserves the plate and the matte
output provides the refined mask. Output is 16-bit float; internal statistics
and coefficients use 32-bit float to preserve numerical precision.

The redundant embedded-alpha and matte-preview controls have been removed.

When bypassing the node, set Result to Guide / Plate and OutMatte to Rough
Matte in Flame's bypass selectors. These are Batch settings, not shader
controls; they are not set by this shader's XML. Mix 0 also returns the
original image and matte while the node remains enabled.

## Validation and limitations

All 11 passes and XML compile/package with Flame 2025.2.3 and 2026.2.2 on Mac.
An earlier build also compiled with 2025.2.5. CPU checks cover the coefficient
solve, box averaging, constant mattes, identity width and colour-only edges.
They do not execute the GLSL. Linux, GPU numerical edge cases and visual
cross-version parity remain unverified. No bit-for-bit match to Nuke is claimed.

Blur Width uses a pixel-footprint box kernel with repeated border pixels.
Nuke's size convention and bounding-box handling may differ. Large widths
cost more to render, and strong detail settings can follow grain. Use matching
input/output dimensions and framing. The filter cannot replace accurate roto
where subject and background have indistinguishable colours.

## Sharing

Use the 13 GLSL/XML/PNG files in `matchbox` for Matchbook. See
`SUBMISSION_NOTES.md`. The ZIP includes the standalone licence documents too.
It contains no encrypted MX/LX files or original Nuke script.

New implementation: Nils Crompton — hello@nilscrompton.com.
Rafael Silva is credited as the author of the reference Nuke gizmo.
New contributions use MIT; applicable upstream BSD-2-Clause notices remain
in each shader pass and in `THIRD_PARTY_NOTICES.txt`.

## Development

Regenerate with `python3 build_shaders.py`; verify with `python3 verify_math.py`.
Compile on a Flame workstation with:

```
/opt/Autodesk/flame_2026.2.2/bin/shader_builder -m matchbox/GuidedMatte.*.glsl
```

After changes, refresh the sharing ZIP with `python3 publish.py --zip` and attach it
to a new GitHub Release. Do not include older compiled files.
