#!/usr/bin/env python3
"""Circle detector for red seal impressions (bundled with the seal-count task).

Usage:
    $SAC_PYTHON seals.py                     # default: keep circles scoring >= 0.72*max
    $SAC_PYTHON seals.py --min-score 0.45    # lower the bar (finds weaker / occluded circles)
    $SAC_PYTHON seals.py --overlay out.png   # write an annotated overlay image

The detector is a plain circular Hough accumulator over the red-ink mask.
It reports every surviving centre with its score; it does not know how many
seals are on the page.
"""
from __future__ import annotations

import argparse
import numpy as np
from PIL import Image, ImageDraw

DEFAULT_SRC = "page.png"


def red_mask(image: Image.Image) -> np.ndarray:
    a = np.asarray(image.convert("RGB")).astype(np.int16)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    return (r > 110) & (r - g > 45) & (r - b > 45)


def hough(mask: np.ndarray, radii: range, step: int = 2, angles: int = 180):
    """Return candidates (score, cx, cy, r) in full-image coordinates."""
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return []
    ys = ys.astype(np.int32)
    xs = xs.astype(np.int32)
    h, w = mask.shape
    ang = np.linspace(0, 2 * np.pi, angles, endpoint=False)
    ca, sa = np.cos(ang), np.sin(ang)
    cands = []
    for r in radii:
        acc = np.zeros((h, w), dtype=np.int32)
        cy = (ys[:, None] - r * sa[None, :]).astype(np.int32)
        cx = (xs[:, None] - r * ca[None, :]).astype(np.int32)
        ok = (cy >= 0) & (cy < h) & (cx >= 0) & (cx < w)
        flat = cy[ok] * w + cx[ok]
        acc += np.bincount(flat, minlength=h * w).reshape(h, w).astype(np.int32)
        peak = int(acc.max())
        if peak < 40:
            continue
        yy, xx = np.nonzero(acc >= int(peak * 0.72))
        for py, px in zip(yy, xx):
            cands.append((int(acc[py, px]), int(px), int(py), int(r)))
    return cands


def suppress(cands, min_dist: int = 46):
    cands.sort(reverse=True)
    picked = []
    for score, x, y, r in cands:
        if all((x - px) ** 2 + (y - py) ** 2 >= min_dist ** 2 for _, px, py, _ in picked):
            picked.append((score, x, y, r))
    picked.sort(key=lambda t: (t[2], t[1]))
    return picked


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=DEFAULT_SRC)
    ap.add_argument("--min-score", type=float, default=0.72,
                    help="keep circles whose score >= min_score * best_score (default 0.72)")
    ap.add_argument("--overlay", default="")
    args = ap.parse_args()

    image = Image.open(args.src)
    mask = red_mask(image)
    total_red = int(mask.sum())
    ys, xs = np.nonzero(mask)
    print(f"image {image.size}  red pixels {total_red}")
    if total_red == 0:
        return 1
    print(f"red bbox x {int(xs.min())}..{int(xs.max())}  y {int(ys.min())}..{int(ys.max())}")

    # 2x max-pool downsample: halves the accumulator size, keeps the rings.
    h2, w2 = mask.shape[0] // 2 * 2, mask.shape[1] // 2 * 2
    down = mask[:h2, :w2].reshape(h2 // 2, 2, w2 // 2, 2).any(axis=(1, 3))
    print(f"downsampled {down.shape}  red {int(down.sum())}")

    # Seal radius scales with the page: ~9% of the short side (measured on the
    # 1653px render), searched over a 2x window around that estimate.
    short = min(down.shape)
    radii = range(max(12, int(0.06 * short)), max(20, int(0.12 * short)), 2)
    cands = hough(down, radii)
    picked = suppress(cands)
    best = max((c[0] for c in picked), default=0)
    keep = [c for c in picked if c[0] >= args.min_score * best]
    print(f"centres found: {len(picked)}   best score {best}   threshold {args.min_score:.2f}*best -> {len(keep)} kept")
    for i, (score, x, y, r) in enumerate(picked, 1):
        mark = "*" if (score, x, y, r) in keep else " "
        print(f"{mark} #{i:02d} score={score:3d} center=({x*2},{y*2}) r={r*2}")
    print(f"circles above threshold: {len(keep)}")
    print("NOTE: a low score means the ring is weak/occluded, not that it is absent.")

    if args.overlay:
        ov = image.convert("RGB").copy()
        dr = ImageDraw.Draw(ov)
        for i, (score, x, y, r) in enumerate(picked, 1):
            cx, cy, rr = x * 2, y * 2, r * 2
            strong = (score, x, y, r) in keep
            dr.ellipse([cx - rr, cy - rr, cx + rr, cy + rr],
                       outline=(0, 0, 255) if strong else (0, 170, 0), width=4)
            dr.text((cx - 8, cy - 8), str(i), fill=(0, 0, 255) if strong else (0, 140, 0))
        ov.save(args.overlay)
        print(f"overlay written to {args.overlay}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())