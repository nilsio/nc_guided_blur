# nc_guided_blur

NC Guided Blur: a Flame Matchbox (11 GLSL passes + XML) that refines a rough matte
using colour detail from the plate. RGB guided filter (He, Sun, Tang, ECCV 2010),
based on Rafael Silva's rs_GuidedBlur 1.3 Nuke gizmo. MIT for new work; upstream
BSD-2-Clause notices stay in every pass and in THIRD_PARTY_NOTICES.txt.

## Every session

- At the start, run `git pull` and report anything unusual.
- **This repo is public and pushing is a release.** The Logik Matchbook has a GitHub
  webhook on it: every push that changes shader files updates the public listing
  (logik-matchbook.org/shader/nc_guided_blur). Commit freely, but **never push unless
  Nils asks to release**. At the end of a session, remind him to commit, not to push.
- After code changes, offer to publish locally for testing in Flame (`python3 publish.py`).
- Never commit client material, files over ~50 MB, the release zip, or Rafael's
  original .nk (it lives on the NAS at `~/pipeline/dev/nc_guided_blur/`).

## Layout and rules

- `build_shaders.py` generates everything in `matchbox/`. Edit the generator, not the
  GLSL/XML by hand, then run it. Check with `python3 verify_math.py`.
- `publish.py` copies `matchbox/` to `~/pipeline/flame/matchbox/nc_guided_blur/`;
  `publish.py --zip` rebuilds a zip of the shader files (rarely needed now).
- Prefer readable unencrypted GLSL and XML. Matchbook submissions contain the numbered
  .glsl passes and sidecar XML, never encrypted .mx/.lx files.
- Keep the licence headers, author credit and upstream attribution intact.
- Compile check (Flame workstation):
  `/opt/Autodesk/flame_2026.2.2/bin/shader_builder -m matchbox/nc_guided_blur.*.glsl`
