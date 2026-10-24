"""Final pose showcase sheet: cover-cropped cells with captions."""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

OUT = sys.argv[1]
items = [
    ("idle-studio-clean.png", "IDLE", "Anime Clean · Studio"),
    ("wave-outdoor-wuthering.png", "WAVE", "Wuthering Waves · Outdoor"),
    ("point-neon-honkai.png", "POINT", "Honkai Star Rail · Neon stage"),
    ("lookback-outdoor-genshin.png", "LOOK BACK", "Genshin Impact · Outdoor"),
    ("wave-portrait-closeup.png", "PORTRAIT", "Wuthering Waves · Close-up"),
    ("idle-sunset-clean.png", "SUNSET", "Anime Clean · Golden hour"),
]
cell_w, cell_h = 720, 1000
gap = 16
cols, rows = 3, 2
canvas = Image.new(
    "RGB",
    (cell_w * cols + gap * (cols + 1), cell_h * rows + gap * (rows + 1) + 90),
    (9, 9, 11),
)
draw = ImageDraw.Draw(canvas, "RGBA")
try:
    f_title = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 46)
    f_big = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 30)
    f_small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22)
except Exception:
    f_title = f_big = f_small = ImageFont.load_default()

header = "VRM ANIME SHADER v2  ·  POSE SHOWCASE"
draw.text((gap + 6, 22), header, font=f_title, fill=(240, 240, 245, 255))
draw.text(
    (gap + 6, 72),
    "Blender 4.4 EEVEE · scene-light driven toon shading · MToon materials preserved",
    font=f_small,
    fill=(180, 185, 195, 255),
)


def cover(im, w, h):
    scale = max(w / im.width, h / im.height)
    nw, nh = int(im.width * scale + 0.5), int(im.height * scale + 0.5)
    im = im.resize((nw, nh), Image.LANCZOS)
    left = (nw - w) // 2
    top = (nh - h) // 2
    return im.crop((left, top, left + w, top + h))


for i, (name, title, sub) in enumerate(items):
    path = os.path.join(OUT, name)
    if not os.path.exists(path):
        print("missing", path)
        continue
    im = cover(Image.open(path).convert("RGB"), cell_w, cell_h)
    x = gap + (i % cols) * (cell_w + gap)
    y = 110 + gap + (i // cols) * (cell_h + gap)
    canvas.paste(im, (x, y))
    draw.rectangle((x, y + cell_h - 84, x + cell_w, y + cell_h), fill=(0, 0, 0, 175))
    draw.text((x + 20, y + cell_h - 76), title, font=f_big, fill=(255, 255, 255, 245))
    draw.text((x + 20, y + cell_h - 38), sub, font=f_small, fill=(215, 220, 230, 235))

out = os.path.join(OUT, "pose_showcase_sheet.png")
canvas.save(out)
print("saved", out, canvas.size)
