import os
import cv2
from PIL import Image
import numpy as np

# 配置参数
INPUT_DIR = r"D:\yolo_project\raw_images"
OUTPUT_DIR = r"D:\yolo_project\dataset\images"
TARGET_SIZE = (640, 480)
IMAGE_FORMAT = ".jpg"
QUALITY = 95


def check_image_validity(img_path):
    """检查图片有效性"""
    try:
        with Image.open(img_path) as img:
            img.verify()
        return True
    except Exception as e:
        print(f"❌ 无效图片: {os.path.basename(img_path)} - {e}")
        return False


def resize_image(img, target_size):
    """等比例缩放+居中填充"""
    h, w = img.shape[:2]
    target_w, target_h = target_size
    scale = min(target_w / w, target_h / h)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # 黑色背景填充
    canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
    x_offset = (target_w - new_w) // 2
    y_offset = (target_h - new_h) // 2
    canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w, :] = resized
    return canvas


def preprocess_images():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    valid_ext = (".jpg", ".jpeg", ".png", ".bmp")
    image_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(valid_ext)]

    if not image_files:
        print(f"❌ 未找到图片: {INPUT_DIR}")
        return

    processed = 0
    for idx, filename in enumerate(image_files, 1):
        input_path = os.path.join(INPUT_DIR, filename)
        if not check_image_validity(input_path):
            continue

        # 读取并预处理
        img = cv2.imread(input_path)
        if img is None:
            print(f"❌ 无法读取: {filename}")
            continue
        img_processed = resize_image(img, TARGET_SIZE)

        # 保存（按顺序重命名）
        output_filename = f"{idx:04d}{IMAGE_FORMAT}"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        cv2.imwrite(output_path, img_processed, [cv2.IMWRITE_JPEG_QUALITY, QUALITY])
        print(f"✅ {filename} → {output_filename}")
        processed += 1

    print(f"\n📊 预处理完成: {processed}/{len(image_files)} 张有效图片")
    print(f"输出目录: {OUTPUT_DIR}")


if __name__ == "__main__":
    preprocess_images()
