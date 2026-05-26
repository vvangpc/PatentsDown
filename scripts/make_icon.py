"""Generate the PatentsDown application icon.

The icon is drawn with Pillow so the Windows ICO can be reproduced without
external design files.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageFilter


CANVAS = 1024
EXPORT_SIZES = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]


@dataclass(frozen=True)
class Palette:
    blue_top: tuple[int, int, int, int] = (30, 159, 231, 255)
    blue_bottom: tuple[int, int, int, int] = (16, 87, 181, 255)
    cyan: tuple[int, int, int, int] = (81, 214, 232, 255)
    white: tuple[int, int, int, int] = (255, 255, 255, 255)
    paper: tuple[int, int, int, int] = (247, 252, 255, 255)
    paper_shadow: tuple[int, int, int, int] = (8, 28, 58, 58)
    line: tuple[int, int, int, int] = (86, 139, 195, 210)
    fold: tuple[int, int, int, int] = (207, 232, 251, 255)


P = Palette()


def rounded_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    return mask


def vertical_gradient(size: int, top: tuple[int, ...], bottom: tuple[int, ...]) -> Image.Image:
    grad = Image.new("RGBA", (1, size))
    for y in range(size):
        t = y / (size - 1)
        color = tuple(round(top[i] * (1 - t) + bottom[i] * t) for i in range(4))
        grad.putpixel((0, y), color)
    return grad.resize((size, size), Image.Resampling.BICUBIC)


def add_layer(base: Image.Image, layer: Image.Image, mask: Image.Image | None = None) -> None:
    base.alpha_composite(Image.composite(layer, Image.new("RGBA", layer.size, (0, 0, 0, 0)), mask) if mask else layer)


def draw_background(img: Image.Image) -> None:
    mask = rounded_mask(CANVAS, 214)
    bg = vertical_gradient(CANVAS, P.blue_top, P.blue_bottom)
    img.alpha_composite(Image.composite(bg, Image.new("RGBA", bg.size, (0, 0, 0, 0)), mask))

    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((-250, -390, 1060, 650), fill=(255, 255, 255, 54))
    gd.ellipse((480, 430, 1290, 1220), fill=(31, 214, 232, 56))
    glow = glow.filter(ImageFilter.GaussianBlur(36))
    add_layer(img, glow, mask)

    shade = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    sd.rounded_rectangle((30, 30, 994, 994), radius=190, outline=(255, 255, 255, 58), width=10)
    sd.rounded_rectangle((50, 54, 974, 986), radius=176, outline=(6, 28, 72, 48), width=12)
    add_layer(img, shade, mask)


def draw_document(img: Image.Image) -> None:
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((278, 156, 762, 786), radius=44, fill=P.paper_shadow)
    shadow = shadow.filter(ImageFilter.GaussianBlur(24))
    img.alpha_composite(shadow)

    draw = ImageDraw.Draw(img)
    left, top, right, bottom = 250, 126, 774, 772
    fold = 142
    draw.rounded_rectangle((left, top, right, bottom), radius=42, fill=P.paper)
    draw.polygon([(right - fold, top), (right, top + fold), (right - fold, top + fold)], fill=P.fold)
    draw.line([(right - fold, top), (right - fold, top + fold), (right, top + fold)], fill=(153, 194, 230, 220), width=8)

    for y, width in [(332, 310), (416, 250), (500, 300)]:
        draw.rounded_rectangle((330, y, 330 + width, y + 28), radius=14, fill=P.line)

    draw.rounded_rectangle((330, 238, 498, 274), radius=18, fill=(35, 111, 190, 230))
    draw.ellipse((562, 232, 606, 276), fill=P.cyan)
    draw.line((606, 254, 662, 254), fill=P.cyan, width=12)
    draw.ellipse((650, 242, 674, 266), fill=P.cyan)


def draw_download_mark(img: Image.Image) -> None:
    draw = ImageDraw.Draw(img)
    cx = CANVAS // 2

    halo = Image.new("RGBA", img.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    hd.ellipse((314, 560, 710, 956), fill=(6, 42, 104, 74))
    halo = halo.filter(ImageFilter.GaussianBlur(20))
    img.alpha_composite(halo)

    draw.ellipse((342, 548, 682, 888), fill=(22, 111, 209, 255))
    draw.ellipse((374, 580, 650, 856), fill=(38, 156, 230, 255))
    draw.arc((374, 580, 650, 856), 204, 336, fill=(128, 235, 244, 230), width=14)

    draw.rounded_rectangle((cx - 34, 622, cx + 34, 742), radius=30, fill=P.white)
    draw.polygon([(408, 718), (616, 718), (512, 824)], fill=P.white)
    draw.rounded_rectangle((408, 824, 616, 864), radius=20, fill=P.white)


def render_icon() -> Image.Image:
    img = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    draw_background(img)
    draw_document(img)
    draw_download_mark(img)
    return img


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, ".."))
    ico_path = os.path.join(root, "icon.ico")
    preview_path = os.path.join(root, "icon_preview.png")

    source = render_icon()
    preview = source.resize((256, 256), Image.Resampling.LANCZOS)
    preview.save(preview_path, format="PNG")
    preview.save(ico_path, format="ICO", sizes=EXPORT_SIZES)

    print(f"OK -> {ico_path} ({os.path.getsize(ico_path) / 1024:.1f} KB)")
    print(f"Preview -> {preview_path}")


if __name__ == "__main__":
    main()
