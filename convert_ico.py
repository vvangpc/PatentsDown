from PIL import Image
import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_ico.py <image_path>")
        return
    
    img_path = sys.argv[1]
    try:
        # 打开图片并转换为 RGBA 格式
        img = Image.open(img_path).convert("RGBA")
        img.save("icon.ico", format="ICO", sizes=[(256, 256)])
        print(f"成功将 {img_path} 转换为 icon.ico")
    except Exception as e:
        print(f"转换失败: {e}")

if __name__ == "__main__":
    main()
