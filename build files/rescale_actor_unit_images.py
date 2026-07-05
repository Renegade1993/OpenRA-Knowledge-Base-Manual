#!/usr/bin/env python3
"""Rescale all actor battlefield-sprite images so the longest side is at least 64 px.

OpenRA's in-world sprites are intentionally small (e.g. 12x16).  Pandoc/pdf render them
at ~0.55 of their natural size, so without upscaling they look like empty placeholders.
This script uses nearest-neighbor upscaling to preserve the pixel-art look.

Usage:
    py rescale_actor_unit_images.py
"""
import os
from pathlib import Path
import numpy as np
from PIL import Image

MIN_SIZE = 192
MIN_ICON_HEIGHT = 96
ROOT = Path("C:/Users/Kmoney/Documents/AI Projects/Cameo Work/Game Sources and Development Reference Materials/OpenRA Manual/images/actors")

# Dune 2000 aircraft sprites are tiny and very wide; pad them to a square before upscaling
# so they fill the PDF table cell height instead of being letter-boxed.
D2K_AIR_UNITS = {"carryall_unit.png", "ornithopter_unit.png"}


def keep_largest_component(img):
    """Keep only the largest connected component of non-transparent pixels.

    D2K building previews include a small concrete bib/foundation tile as a separate
    blob at the bottom-left.  That tile dominates the bounding box and shrinks the
    actual building to ~1/4 of the preview cell.  Removing it (and any other tiny
    detached bits) leaves the main building to fill the cell."""
    alpha = np.array(img.split()[3])
    mask = alpha > 0
    if not mask.any():
        return img
    h, w = mask.shape
    labels = np.zeros((h, w), dtype=int)
    label = 0
    sizes = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and labels[y, x] == 0:
                label += 1
                stack = [(x, y)]
                count = 0
                while stack:
                    cx, cy = stack.pop()
                    if cx < 0 or cx >= w or cy < 0 or cy >= h:
                        continue
                    if not mask[cy, cx] or labels[cy, cx] != 0:
                        continue
                    labels[cy, cx] = label
                    count += 1
                    stack.append((cx + 1, cy))
                    stack.append((cx - 1, cy))
                    stack.append((cx, cy + 1))
                    stack.append((cx, cy - 1))
                sizes.append(count)
    if not sizes:
        return img
    largest = int(np.argmax(sizes)) + 1
    keep = labels == largest
    if keep.all():
        return img
    new_alpha = alpha.copy()
    new_alpha[~keep] = 0
    r, g, b, a = img.split()
    return Image.merge('RGBA', (r, g, b, Image.fromarray(new_alpha)))


def pad_to_square(img):
    w, h = img.size
    side = max(w, h)
    new = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    new.paste(img, ((side - w) // 2, (side - h) // 2))
    return new


def crop_to_bounds(img, margin=2):
    """Trim transparent padding around the visible sprite so the sprite fills
    the preview cell instead of being lost in a sea of empty pixels."""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    alpha = img.split()[3]
    bbox = alpha.getbbox()
    if bbox is None:
        return img
    left, top, right, bottom = bbox
    left = max(0, left - margin)
    top = max(0, top - margin)
    right = min(img.width, right + margin)
    bottom = min(img.height, bottom + margin)
    return img.crop((left, top, right, bottom))


def rescale(path):
    img = Image.open(path)
    if img.width == 0 or img.height == 0:
        return False
    original_size = (img.width, img.height)
    is_d2k = path.parent.name == "d2k"
    img = crop_to_bounds(img)
    if is_d2k:
        img = keep_largest_component(img)
        img = crop_to_bounds(img)
    if is_d2k and path.name in D2K_AIR_UNITS:
        img = pad_to_square(img)
    changed = (img.width, img.height) != original_size
    max_dim = max(img.width, img.height)
    if max_dim < MIN_SIZE:
        scale = MIN_SIZE / max_dim
        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size, Image.NEAREST)
        changed = True
    if changed:
        img.save(path)
    return changed


def fix_truck_icon(img):
    """CNC supply-truck cameo: its background is a mottled grey/white palette.

    The truck body is dark/brown, so we can safely replace the grayscale background
    palette entries and any remaining near-white pixels with opaque black."""
    if img.mode != 'P':
        return img.convert('RGBA')
    arr = np.array(img)
    palette = np.array(img.getpalette()).reshape(-1, 3)
    black_idx = np.where(np.all(palette == [0, 0, 0], axis=1))[0]
    if len(black_idx) == 0:
        palette[0] = [0, 0, 0]
        img.putpalette(palette.flatten().tolist())
        black_idx = 0
    else:
        black_idx = black_idx[0]
    for i in range(256):
        c = palette[i]
        if c[0] == c[1] == c[2]:
            arr[arr == i] = black_idx
    img2 = Image.fromarray(arr, 'P')
    img2.putpalette(img.getpalette())
    img2 = img2.convert('RGBA')
    arr2 = np.array(img2)
    brightness = np.max(arr2[:, :, :3], axis=2)
    fringe = (arr2[:, :, 3] > 0) & (brightness >= 250)
    arr2[fringe] = [0, 0, 0, 255]
    return Image.fromarray(arr2, 'RGBA')


def normalize_icon(path):
    """Resize build-palette cameo icons to the height the PDF table will display them at.

    Some cameo files (e.g. RA's *.icnh.tem files) are stored as large 256x192 canvases
    that have been nearest-neighbour upscaled from the original 64x48 art.  Downsampling
    those back to 96px tall with Lanczos interpolation gives a much smoother result than
    the previous nearest-neighbour upscaling, and the file size is smaller than the raw
    256x192 canvas.  Tiny icons are upsampled to the same 96px height so they are also
    legible in the table."""
    img = Image.open(path)
    if img.width == 0 or img.height == 0:
        return False
    # Only touch the CNC supply truck; the broad background fix broke other cameos.
    if path.parent.name == 'cnc' and path.name == 'truck.png':
        img = fix_truck_icon(img)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    img = crop_to_bounds(img)
    if img.height != MIN_ICON_HEIGHT:
        scale = MIN_ICON_HEIGHT / img.height
        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        # Remove any near-white or dark-grey resampling fringes from the truck only.
        if path.parent.name == 'cnc' and path.name == 'truck.png':
            arr = np.array(img)
            hsv = np.array(img.convert('HSV'))
            hue, sat, val = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
            bright = np.max(arr[:, :, :3], axis=2)
            fringe = (arr[:, :, 3] > 0) & ((bright >= 250) | ((sat < 20) & (val < 120)))
            arr[fringe] = [0, 0, 0, 0]
            img = Image.fromarray(arr, 'RGBA')
    img.save(path)
    return True


def main():
    unit_count = 0
    icon_count = 0
    for mod_dir in ROOT.iterdir():
        if not mod_dir.is_dir():
            continue
        for f in mod_dir.iterdir():
            if not f.is_file() or not f.name.endswith(".png"):
                continue
            if f.name.endswith("_unit.png"):
                if rescale(f):
                    unit_count += 1
            else:
                if normalize_icon(f):
                    icon_count += 1
    print(f"Rescaled {unit_count} unit images to at least {MIN_SIZE}px on the longest side.")
    print(f"Normalized {icon_count} cameo icons to {MIN_ICON_HEIGHT}px tall.")


if __name__ == "__main__":
    main()
