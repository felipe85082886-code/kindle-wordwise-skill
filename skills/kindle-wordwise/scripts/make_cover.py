#!/usr/bin/env python3
"""Produce two ASIN-keyed JPEG cover files. Optional dependency: Pillow."""
import argparse
import re
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cover', type=Path, required=True)
    p.add_argument('--asin', required=True)
    p.add_argument('--output-root', type=Path, required=True)
    a = p.parse_args()
    if not re.fullmatch(r'B[0-9A-Z]{9}', a.asin):
        p.error('ASIN must match the final book identity')
    try:
        from PIL import Image, ImageOps
    except ImportError:
        p.exit(1, 'Pillow is required for this optional helper.\n')
    with Image.open(a.cover) as original:
        cover = ImageOps.exif_transpose(original).convert('RGBA')
        background = Image.new('RGBA', cover.size, 'white')
        cover = Image.alpha_composite(background, cover).convert('RGB')
        cover.thumbnail((374, 500), Image.Resampling.LANCZOS)
        name = f'thumbnail_{a.asin}_EBOK_portrait.jpg'
        for folder in ('system/thumbnails', 'amazon-cover-bug'):
            path = a.output_root / folder / name
            path.parent.mkdir(parents=True, exist_ok=True)
            cover.save(path, 'JPEG', quality=90)
            print(path)


if __name__ == '__main__':
    main()
