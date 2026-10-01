"""Turn slides/Untitled.jpg into the title-slide background of the IWBIS deck.

The source is 1107 x 582 px: a dark slate panel on the left with two accent bars,
and a photo of a building under a teal overlay on the right. This script
  1. crops it to 16:9 (the slide's shape), trimming both sides equally,
  2. upscales it to 2560 x 1440 with Lanczos resampling,
  3. smooths JPEG block noise in the flat left panel (edge-preserving median)
     and darkens that panel slightly, so white title text has strong contrast,
  4. brightens and adds contrast to the photo side (a percentile levels stretch
     with a mild midtone lift), sharpens it, and nudges saturation,
  5. blends the two treatments across the panel-to-photo transition with a
     smooth horizontal ramp, so no seam appears.
It prints luminance statistics before and after, and the text contrast ratio
the title will have against the panel.

Run:  python slides/make_title_background.py [src] [dst]
"""
import sys

import numpy as np
from PIL import Image, ImageFilter

SRC = sys.argv[1] if len(sys.argv) > 1 else "slides/Untitled.jpg"
DST = sys.argv[2] if len(sys.argv) > 2 else "slides/title_background.jpg"
OUT_W, OUT_H = 2560, 1440

# tuning knobs. The stretch works on luminance only and scales R, G and B by the
# same factor, so hues are kept: the dusk-blue sky stays blue instead of clipping
# in the blue channel and turning cyan.
PANEL_DARKEN = 0.92          # multiply the left panel by this
RAMP = (0.47, 0.60)          # panel -> photo transition, as a fraction of the width
STRETCH_PCT = (0.5, 99.8)    # photo luminance percentiles mapped to the output range below
OUT_RANGE = (0.06, 0.80)
MID_GAMMA = 1.15             # > 1 keeps the midtones from washing out after the stretch
SHARPEN = dict(radius=2.0, percent=50, threshold=3)

LUMA = np.array([0.2126, 0.7152, 0.0722])


def rel_luminance(rgb):
    c = np.asarray(rgb, dtype=float) / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return float(lin @ LUMA)


def contrast(fg, bg):
    a, b = sorted([rel_luminance(fg), rel_luminance(bg)], reverse=True)
    return (a + 0.05) / (b + 0.05)


def stats(arr, xs):
    lum = (arr[:, xs] @ LUMA) * 255
    return lum.mean(), lum.std()


src = Image.open(SRC).convert("RGB")
w0, h0 = src.size
tw = round(h0 * 16 / 9)
left = (w0 - tw) // 2
big = src.crop((left, 0, left + tw, h0)).resize((OUT_W, OUT_H), Image.LANCZOS)

x = np.linspace(0.0, 1.0, OUT_W)
t = np.clip((x - RAMP[0]) / (RAMP[1] - RAMP[0]), 0.0, 1.0)
ramp = (t * t * (3 - 2 * t))[None, :, None]          # smoothstep, 0 = panel, 1 = photo
photo_cols = x > RAMP[1] + 0.02
panel_cols = x < RAMP[0] - 0.02

base = np.asarray(big, dtype=float) / 255.0

# left panel: edge-preserving smoothing, then a slight darkening
panel = np.asarray(big.filter(ImageFilter.MedianFilter(5)), dtype=float) / 255.0 * PANEL_DARKEN

# photo side: light sharpening, then a luminance-only levels stretch that keeps hue
sharp = big.filter(ImageFilter.UnsharpMask(**SHARPEN))
photo = np.asarray(sharp, dtype=float) / 255.0
Y = photo @ LUMA
lo, hi = np.percentile(Y[:, photo_cols], STRETCH_PCT)
Yn = OUT_RANGE[0] + np.clip((Y - lo) / (hi - lo), 0.0, 1.0) ** MID_GAMMA * (OUT_RANGE[1] - OUT_RANGE[0])
photo = np.clip(photo * (Yn / np.maximum(Y, 1e-3))[..., None], 0.0, 1.0)

out = panel * (1.0 - ramp) + photo * ramp
Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(DST, quality=93, subsampling=0)

b_mean, b_std = stats(base, photo_cols)
a_mean, a_std = stats(out, photo_cols)
pb_mean, _ = stats(base, panel_cols)
pa_mean, _ = stats(out, panel_cols)
print(f"wrote {DST} ({OUT_W} x {OUT_H}) from {SRC} ({w0} x {h0}, cropped to {tw} x {h0})")
print(f"photo side  luminance mean {b_mean:5.1f} -> {a_mean:5.1f}   contrast (std) {b_std:5.1f} -> {a_std:5.1f}")
print(f"left panel  luminance mean {pb_mean:5.1f} -> {pa_mean:5.1f}")
clip = ((out[:, photo_cols] * 255) >= 250).any(axis=2).mean() * 100
clip0 = ((base[:, photo_cols] * 255) >= 250).any(axis=2).mean() * 100
dark = ((out[:, photo_cols] @ LUMA) * 255 <= 10).mean() * 100
dark0 = ((base[:, photo_cols] @ LUMA) * 255 <= 10).mean() * 100
print(f"photo side  pixels with any channel >= 250: {clip0:.2f}% -> {clip:.2f}%   near-black (<= 10): {dark0:.2f}% -> {dark:.2f}%")
sky = (slice(0, int(OUT_H * 0.35)), slice(int(OUT_W * 0.92), OUT_W))
def hue(rgb):
    import colorsys
    return colorsys.rgb_to_hsv(*rgb)[0] * 360
print(f"sky (top right) mean RGB {tuple(int(v) for v in base[sky].reshape(-1, 3).mean(0) * 255)} hue {hue(base[sky].reshape(-1, 3).mean(0)):.0f} -> "
      f"{tuple(int(v) for v in out[sky].reshape(-1, 3).mean(0) * 255)} hue {hue(out[sky].reshape(-1, 3).mean(0)):.0f}")
# the text column sits on the panel between x = 5% and 47% of the width
text_cols = (x > 0.05) & (x < 0.47)
y = np.linspace(0.0, 1.0, OUT_H)
text_rows = (y < 0.47) | (y > 0.58)                    # the accent bars sit between these
worst = (out[text_rows][:, text_cols].reshape(-1, 3) * 255)
worst_bg = worst[np.argmax(worst @ LUMA)]              # brightest panel pixel under the text column
typical_bg = np.median(worst, axis=0)
for name, fg in [("white title", (255, 255, 255)), ("affiliation D5E0EA", (0xD5, 0xE0, 0xEA)), ("accent C6AB8E", (0xC6, 0xAB, 0x8E))]:
    print(f"{name:20s} contrast on typical panel {contrast(fg, typical_bg):4.1f}:1, "
          f"on brightest panel pixel {contrast(fg, worst_bg):4.1f}:1")
