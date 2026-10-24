"""Compose two comparison renders side by side with labels."""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

args = sys.argv[1:]
src_a, src_b, out = args[0], args[1], args[2]
label_a = args[3] if len(args) > 3 else "Original MToon"
label_b = args[4] if len(args) > 4 else "VRM Anime Shader"

im_a = Image.open(src_a).convert("RGB")
im_b = Image.open(src_b).convert("RGB")
scale = 0.5
w = max(1, int(im_a.width * scale))
h = max(1, int(im_a.height * scale))
im_a = im_a.resize((w, h), Image.LANCZOS)
im_b = im_b.resize((w, h), Image.LANCZOS)

gap = 8
canvas = Image.new("RGB", (w * 2 + gap, h), (0, 0, 0))
canvas.paste(im_a, (0, 0))
canvas.paste(im_b, (w + gap, 0))

draw = ImageDraw.Draw(canvas, "RGBA")
try:
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", max(16, int(h * 0.035)))
except Exception:
    font = ImageFont.load_default()

for i, text in enumerate((label_a, label_b)):
    x = i * (w + gap) + int(w * 0.02)
    y = int(h * 0.015)
    bbox = draw.textbbox((x, y), text, font=font)
    draw.rectangle((bbox[0] - 6, bbox[1] - 3, bbox[2] + 6, bbox[3] + 3), fill=(0, 0, 0, 170))
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 235))

os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
canvas.save(out)
print("composed", out, canvas.size)
