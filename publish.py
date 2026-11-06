#!/usr/bin/env python3
"""Publish the NC Guided Blur Matchbox.

Default: copy matchbox/* to ~/pipeline/flame/matchbox/nc_guided_blur/ (where Flame
browses for Matchbox shaders). Files in the destination that are not in
matchbox/ are reported but never deleted.

--zip: rebuild nc_guided_blur_unencrypted.zip (matchbox files + SUBMISSION_NOTES.md)
for a GitHub Release / Matchbook. The zip is gitignored.

Usage: python3 publish.py [--dry-run] [--dest DIR] [--zip]
"""
import argparse
import filecmp
import os
import shutil
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "matchbox")
DEFAULT_DEST = os.path.join(os.path.expanduser("~"), "pipeline", "flame", "matchbox", "nc_guided_blur")
ZIP = os.path.join(HERE, "nc_guided_blur_unencrypted.zip")


def files():
    return sorted(f for f in os.listdir(SRC) if not f.startswith("."))


def publish(dest, dry):
    tag = "[dry run] " if dry else ""
    if not os.path.isdir(os.path.dirname(dest)) and not dry:
        os.makedirs(os.path.dirname(dest))
    changed = 0
    for name in files():
        src, dst = os.path.join(SRC, name), os.path.join(dest, name)
        if os.path.exists(dst) and filecmp.cmp(src, dst, shallow=False):
            continue
        print("%s%s %s" % (tag, "update" if os.path.exists(dst) else "add", dst))
        changed += 1
        if not dry:
            os.makedirs(dest, exist_ok=True)
            shutil.copy2(src, dst)
    if os.path.isdir(dest):
        for extra in sorted(set(os.listdir(dest)) - set(files())):
            if not extra.startswith("."):
                print("note: %s is not in matchbox/ (left alone)" % os.path.join(dest, extra))
    print("%s%d file(s) %s" % (tag, changed, "would change" if dry else "changed"))


def build_zip(dry):
    names = [os.path.join(SRC, f) for f in files()] + [os.path.join(HERE, "SUBMISSION_NOTES.md")]
    print("%srebuild %s with %d files" % ("[dry run] " if dry else "", ZIP, len(names)))
    if dry:
        return
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in names:
            zf.write(path, os.path.basename(path))


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--dest", default=os.environ.get("NC_MATCHBOX_DEST", DEFAULT_DEST))
    p.add_argument("--zip", action="store_true", help="rebuild the release zip instead")
    a = p.parse_args()
    if not os.path.isdir(SRC):
        sys.exit("matchbox/ not found")
    build_zip(a.dry_run) if a.zip else publish(a.dest, a.dry_run)


if __name__ == "__main__":
    main()
