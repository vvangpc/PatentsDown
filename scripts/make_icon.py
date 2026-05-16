"""一次性脚本：生成 PatentsDown 现代风格 icon.ico

风格：圆角矩形蓝色渐变背景 + 白色 "P" 字母 + 下方向下箭头。
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter


SIZE = 512  # 高分辨率绘制，最后多尺寸缩放打包
RADIUS = 96  # 圆角半径（512 尺寸下）

COLOR_TOP = (33, 150, 243)      # #2196F3
COLOR_BOTTOM = (13, 71, 161)    # #0D47A1
COLOR_GLOSS = (255, 255, 255, 32)


def make_rounded_gradient(size, radius, top, bottom):
    """生成圆角矩形渐变背景"""
    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    grad = Image.new("RGB", (1, size))
    for y in range(size):
        t = y / (size - 1)
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        grad.putpixel((0, y), (r, g, b))
    grad = grad.resize((size, size))

    mask = Image.new("L", (size, size), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)

    base.paste(grad, (0, 0), mask)
    return base, mask


def load_font(preferred, fallback_list, size):
    candidates = [preferred] + fallback_list
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def draw_letter_p(img, font):
    draw = ImageDraw.Draw(img)
    text = "P"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (SIZE - tw) / 2 - bbox[0]
    # 让 P 在上 60% 区域居中，与下方箭头形成 2:1 的视觉分配
    y = int(SIZE * 0.30) - th / 2 - bbox[1]
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))


def draw_arrow(img):
    """在底部绘制向下箭头：短粗竖线 + 大三角形头"""
    draw = ImageDraw.Draw(img)
    cx = SIZE // 2

    # 把箭头集中在图标下 1/3
    shaft_top = 360
    shaft_bottom = 410
    shaft_w = 36
    arrow_w = 120
    arrow_h = 70
    tip_y = shaft_bottom + arrow_h

    draw.rounded_rectangle(
        (cx - shaft_w // 2, shaft_top, cx + shaft_w // 2, shaft_bottom),
        radius=12,
        fill=(255, 255, 255, 255),
    )
    draw.polygon(
        [
            (cx - arrow_w // 2, shaft_bottom),
            (cx + arrow_w // 2, shaft_bottom),
            (cx, tip_y),
        ],
        fill=(255, 255, 255, 255),
    )


def add_inner_gloss(img, mask):
    """在顶部添加柔和高光以增加立体感"""
    gloss = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(gloss)
    gdraw.ellipse((-SIZE // 2, -SIZE // 2, SIZE + SIZE // 2, SIZE // 2 + 20),
                  fill=(255, 255, 255, 38))
    gloss = gloss.filter(ImageFilter.GaussianBlur(radius=20))
    # 用同一个圆角 mask 把高光限制在图标范围内
    img.alpha_composite(Image.composite(gloss, Image.new("RGBA", gloss.size, (0, 0, 0, 0)), mask))


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.abspath(os.path.join(here, "..", "icon.ico"))

    img, mask = make_rounded_gradient(SIZE, RADIUS, COLOR_TOP, COLOR_BOTTOM)

    # 字体：优先使用 Segoe UI Bold / Microsoft YaHei Bold，找不到则降级
    font = load_font(
        "segoeuib.ttf",
        ["seguibl.ttf", "arialbd.ttf", "msyhbd.ttc", "msyhbd.ttf", "DejaVuSans-Bold.ttf"],
        size=260,
    )
    draw_letter_p(img, font)
    draw_arrow(img)
    add_inner_gloss(img, mask)

    # 多尺寸保存
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img_256 = img.resize((256, 256), Image.LANCZOS)
    img_256.save(out_path, format="ICO", sizes=sizes)

    # 顺便导出 256 PNG 便于预览（不必入版本控制，但 dev 时方便）
    preview_path = os.path.abspath(os.path.join(here, "..", "icon_preview.png"))
    img_256.save(preview_path, format="PNG")

    size_kb = os.path.getsize(out_path) / 1024
    print(f"OK -> {out_path}  ({size_kb:.1f} KB)")
    print(f"Preview -> {preview_path}")


if __name__ == "__main__":
    main()
