#!/usr/bin/env python3
"""Rescale all environmental preview images so the longest side is at least 160 px.

OpenRA environmental sprites are often small (e.g. 24x14) and the exported frames
contain large amounts of empty transparent padding. Pandoc/pdf shrinks figures to
fit the table cell, so actors like civilians end up microscopic. This script crops
away excess transparent padding and then uses nearest-neighbor upscaling to keep
the pixel-art look crisp.

Usage:
    py rescale_environmental_images.py
"""
import os
from pathlib import Path
from PIL import Image

MIN_SIZE = 160
# Crop to content when the opaque content covers less than this fraction of the frame.
CROP_THRESHOLD = 0.25
# Transparent margin to keep around the content after cropping.
CROP_MARGIN = 2
ROOT = Path("C:/Users/Kmoney/Documents/AI Projects/Cameo Work/Game Sources and Development Reference Materials/OpenRA Manual/images/environmental")


def content_bbox(img):
    """Return the bounding box of non-transparent pixels, or None for fully empty."""
    if img.mode == "P":
        img = img.convert("RGBA")
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    alpha = img.getchannel("A")
    return alpha.getbbox()


def crop_to_content(img):
    """Crop frames that are mostly empty transparent padding, preserving a small margin."""
    if img.mode == "P":
        img = img.convert("RGBA")
    bbox = content_bbox(img)
    if not bbox:
        return img
    cw, ch = bbox[2] - bbox[0], bbox[3] - bbox[1]
    total_area = img.width * img.height
    content_area = cw * ch
    if total_area == 0 or content_area / total_area >= CROP_THRESHOLD:
        return img
    # Add a small margin.
    left = max(0, bbox[0] - CROP_MARGIN)
    top = max(0, bbox[1] - CROP_MARGIN)
    right = min(img.width, bbox[2] + CROP_MARGIN)
    bottom = min(img.height, bbox[3] + CROP_MARGIN)
    return img.crop((left, top, right, bottom))


def rescale(path):
    img = Image.open(path)
    if img.width == 0 or img.height == 0:
        return False

    # Remove transparent padding from frames that are mostly empty; this makes
    # small actors (civilians, some TS structures) fill the preview cell.
    cropped = crop_to_content(img)
    max_dim = max(cropped.width, cropped.height)
    if max_dim >= MIN_SIZE:
        if cropped is img:
            return False
        # Save the cropped version even if it already meets the size target.
        cropped.save(path)
        return True

    scale = MIN_SIZE / max_dim
    new_size = (int(cropped.width * scale), int(cropped.height * scale))
    if cropped.mode == "P":
        cropped = cropped.convert("RGBA")
    cropped = cropped.resize(new_size, Image.NEAREST)
    cropped.save(path)
    return True


def main():
    count = 0
    for mod_dir in ROOT.iterdir():
        if not mod_dir.is_dir():
            continue
        for f in mod_dir.iterdir():
            if f.is_file() and f.name.endswith(".png") and not f.name.endswith("_unit.png"):
                if rescale(f):
                    count += 1
    print(f"Rescaled {count} environmental images to at least {MIN_SIZE}px on the longest side.")


if __name__ == "__main__":
    main()
