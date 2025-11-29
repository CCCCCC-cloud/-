import json
import os
from collections import defaultdict

COCO_DIR = r"D:\yolo_project\coco_dataset"


def verify_dataset():
    print("=" * 60)
    print("📋 COCO 数据集验证工具")
    print("=" * 60)

    errors = []

    # 1. 检查核心文件
    print("\n[1/4] 检查核心文件...")
    required = [
        (os.path.join(COCO_DIR, 'annotations', 'train.json'), "训练集标注"),
        (os.path.join(COCO_DIR, 'annotations', 'val.json'), "验证集标注"),
        (os.path.join(COCO_DIR, 'label_list.txt'), "类别文件"),
        (os.path.join(COCO_DIR, 'images'), "图片目录")
    ]
    for path, desc in required:
        if os.path.exists(path):
            print(f"✅ {desc}: 存在")
        else:
            errors.append(f"❌ {desc}缺失: {path}")

    if errors:
        for err in errors:
            print(err)
        return False

    # 2. 验证JSON格式
    print("\n[2/4] 验证JSON文件...")
    json_paths = [
        (os.path.join(COCO_DIR, 'annotations', 'train.json'), "训练集"),
        (os.path.join(COCO_DIR, 'annotations', 'val.json'), "验证集")
    ]
    for path, name in json_paths:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 检查必要字段
        for field in ['images', 'annotations', 'categories']:
            if field not in data:
                errors.append(f"❌ {name}JSON缺少{field}字段")

        # 统计信息
        print(f"\n{name}:")