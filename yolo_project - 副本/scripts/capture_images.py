import numpy as np
import cv2
import os

SAVE_DIR = r"/raw_images"
START_INDEX = 1
IMAGE_FORMAT = ".jpg"


def init_camera():
    # 直接指定摄像头索引为1
    cam_index = 1
    cap = cv2.VideoCapture(cam_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        raise Exception(f"无法打开索引为{cam_index}的相机，请检查设备连接")
    return cap


def capture_images():
    os.makedirs(SAVE_DIR, exist_ok=True)
    cap = init_camera()
    index = START_INDEX

    print("=" * 50)
    print("相机采集程序 | 空格拍照 | Q退出")
    print("=" * 50)

    # 关键：创建可缩放窗口（WINDOW_NORMAL）
    cv2.namedWindow("Capture", cv2.WINDOW_NORMAL)
    # 可选：设置窗口初始大小（可根据需求调整）
    cv2.resizeWindow("Capture", 640, 480)

    while True:
        ret, img = cap.read()
        if not ret:
            print("⚠️  无法读取帧，退出采集")
            break

        # 彩色流左右反转
        img_flipped = cv2.flip(img, 1)

        # 显示反转后的画面（窗口可自由缩放）
        display_img = img_flipped.copy()
        cv2.putText(display_img, f"Next: {index:04d}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Capture", display_img)

        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):
            # 保存反转后的图像
            filepath = os.path.join(SAVE_DIR, f"{index:04d}{IMAGE_FORMAT}")
            cv2.imwrite(filepath, img_flipped)
            print(f"✅ 保存: {index:04d}{IMAGE_FORMAT}")
            index += 1
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"\n采集完成！共{index - START_INDEX}张图片")


if __name__ == "__main__":
    capture_images()