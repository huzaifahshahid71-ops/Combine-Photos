from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
SIZE = 1024
img = Image.new("RGBA", (SIZE, SIZE), (17, 18, 22, 255))
d = ImageDraw.Draw(img)

d.rounded_rectangle((90, 90, 934, 934), radius=190, fill=(28, 30, 38, 255))

cards = [
    ((190, 250, 650, 655), (79, 70, 229, 255)),
    ((330, 185, 790, 590), (37, 99, 235, 255)),
    ((395, 365, 855, 770), (14, 165, 233, 255)),
]
for box, accent in cards:
    d.rounded_rectangle(box, radius=70, fill=(245, 247, 250, 255))
    x1, y1, x2, y2 = box
    d.rounded_rectangle((x1+28, y1+28, x2-28, y2-28), radius=48, fill=(30, 34, 45, 255))
    d.polygon([(x1+55, y2-75), (x1+170, y1+160), (x1+255, y2-140), (x2-55, y2-55)], fill=accent)
    d.ellipse((x2-130, y1+65, x2-75, y1+120), fill=(255, 215, 90, 255))

gx, gy = 244, 695
cell = 88
gap = 22
for r in range(2):
    for c in range(3):
        x = gx + c * (cell + gap)
        y = gy + r * (cell + gap)
        d.rounded_rectangle((x, y, x+cell, y+cell), radius=22,
                            fill=(255, 255, 255, 245) if (r+c) % 2 == 0 else (99, 102, 241, 255))

png = ROOT / "combine_photos_studio_icon.png"
ico = ROOT / "combine_photos_studio.ico"
img.save(png)
sizes = [(16,16),(20,20),(24,24),(32,32),(40,40),(48,48),(64,64),(96,96),(128,128),(256,256)]
img.save(ico, format="ICO", sizes=sizes)
print(f"Generated {png.name} and {ico.name}")
