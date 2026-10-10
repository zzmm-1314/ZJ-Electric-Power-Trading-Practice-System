# make_ico.py
from PIL import Image
import os

base_dir = os.path.dirname(__file__)
SRC = os.path.join(base_dir, "icon.png")  # 你的原始图片（PNG/JPG 都行）
DST = os.path.join(base_dir, "icon.ico")

if not os.path.exists(SRC):
    raise SystemExit(f"找不到源图片: {SRC}，请先把你的图标另存为 {SRC}")

img = Image.open(SRC).convert("RGBA")

# 建议源图至少 256x256，否则会模糊
if img.width < 256 or img.height < 256:
    img = img.resize((256, 256), Image.LANCZOS)

img.save(
    DST,
    format="ICO",
    sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)
print(f"已生成标准 ICO: {DST}")
