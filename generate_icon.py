"""
generate_icon.py -- 为 PatentsDown 生成多分辨率桌面图标
运行: python generate_icon.py
输出: icon.ico (16x16 ~ 256x256)
"""
from PIL import Image, ImageDraw
import os
import math


def draw_icon(size):
    """绘制专利下载主题图标"""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = size * 0.06
    center_x = size / 2
    center_y = size / 2

    # --- 1. 蓝色圆形背景 (带微妙渐变效果) ---
    bg_color = (25, 118, 210, 255)  # #1976D2
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=bg_color,
    )

    # 内圈略浅，模拟光泽
    inner_margin = size * 0.08
    highlight_color = (33, 133, 225, 60)
    draw.ellipse(
        [inner_margin, inner_margin, size * 0.65, size * 0.65],
        fill=highlight_color,
    )

    # --- 2. 白色文档 (带折角) ---
    doc_left = size * 0.26
    doc_top = size * 0.16
    doc_right = size * 0.74
    doc_bottom = size * 0.80
    fold_size = size * 0.13

    # 文档主体
    doc_points = [
        (doc_left, doc_top),
        (doc_right - fold_size, doc_top),
        (doc_right, doc_top + fold_size),
        (doc_right, doc_bottom),
        (doc_left, doc_bottom),
    ]
    draw.polygon(doc_points, fill=(255, 255, 255, 245))

    # 折角三角
    fold_points = [
        (doc_right - fold_size, doc_top),
        (doc_right, doc_top + fold_size),
        (doc_right - fold_size, doc_top + fold_size),
    ]
    draw.polygon(fold_points, fill=(190, 215, 240, 255))

    # 折角阴影线
    lw = max(1, int(size * 0.01))
    draw.line(
        [(doc_right - fold_size, doc_top), (doc_right - fold_size, doc_top + fold_size)],
        fill=(160, 190, 220, 200),
        width=lw,
    )
    draw.line(
        [(doc_right - fold_size, doc_top + fold_size), (doc_right, doc_top + fold_size)],
        fill=(160, 190, 220, 200),
        width=lw,
    )

    # --- 3. 文档上的文字行 ---
    line_color = (160, 190, 220, 200)
    line_y_start = doc_top + size * 0.20
    line_spacing = size * 0.09
    line_lw = max(1, int(size * 0.028))

    for i in range(3):
        y = line_y_start + i * line_spacing
        # 每行长度略有变化，更自然
        line_end = doc_right - size * 0.12 - (i * size * 0.06)
        if y + size * 0.03 < doc_bottom - size * 0.20:
            draw.line(
                [(doc_left + size * 0.08, y), (line_end, y)],
                fill=line_color,
                width=line_lw,
            )

    # --- 4. 下载箭头 (文档下半部分) ---
    arrow_color = (25, 118, 210, 255)
    arrow_cx = center_x
    arrow_top = doc_bottom - size * 0.30
    arrow_bottom = doc_bottom - size * 0.06

    shaft_half_w = size * 0.035
    head_half_w = size * 0.12
    head_start_y = arrow_bottom - size * 0.12

    # 箭头竖轴
    draw.rectangle(
        [
            arrow_cx - shaft_half_w,
            arrow_top,
            arrow_cx + shaft_half_w,
            head_start_y,
        ],
        fill=arrow_color,
    )

    # 箭头三角头
    arrow_head = [
        (arrow_cx - head_half_w, head_start_y),
        (arrow_cx + head_half_w, head_start_y),
        (arrow_cx, arrow_bottom),
    ]
    draw.polygon(arrow_head, fill=arrow_color)

    # --- 5. 底部小横线 (下载托盘) ---
    tray_y = doc_bottom - size * 0.03
    tray_lw = max(1, int(size * 0.025))
    draw.line(
        [(arrow_cx - head_half_w * 0.9, tray_y), (arrow_cx + head_half_w * 0.9, tray_y)],
        fill=arrow_color,
        width=tray_lw,
    )

    return img


def main():
    sizes = [16, 32, 48, 64, 128, 256]
    images = [draw_icon(s) for s in sizes]

    script_dir = os.path.dirname(os.path.abspath(__file__))
    ico_path = os.path.join(script_dir, "icon.ico")

    # 保存为多分辨率 ICO
    images[-1].save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[:-1],
    )
    print(f"图标已生成: {ico_path}")
    print(f"包含分辨率: {', '.join(f'{s}x{s}' for s in sizes)}")


if __name__ == "__main__":
    main()
