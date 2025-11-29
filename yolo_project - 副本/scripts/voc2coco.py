import os
import json
import xml.etree.ElementTree as ET
from sklearn.model_selection import train_test_split
from collections import defaultdict
import shutil

# 配置参数
CONFIG = {
    "image_dir": r"D:\yolo_project\dataset\images",
    "output_dir": r"D:\yolo_project\coco_dataset",
    "train_ratio": 0.8,
    "copy_images": True,
    "random_seed": 42,
    "image_extensions": (".jpg", ".jpeg", ".png", ".bmp")
}


def parse_xml(xml_path):
    """解析VOC格式XML"""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception as e:
        print(f"❌ 解析XML失败: {xml_path} - {e}")
        return None, None, None

    # 提取图片尺寸
    size_node = root.find('size')
    if not size_node:
        print(f"❌ XML缺少size节点: {xml_path}")
        return None, None, None
    width = int(size_node.find('width').text) if size_node.find('width') else 640
    height = int(size_node.find('height').text) if size_node.find('height') else 480
    # 提取物体标注
    objects = []
    for obj in root.findall('object'):
        name = obj.find('name').text.strip() if obj.find('name') else None
        if not name:
            continue
        bbox = obj.find('bndbox')
        if not bbox:
            continue

        # 边界框坐标（VOC→COCO格式转换）
        xmin = max(0, float(bbox.find('xmin').text))
        ymin = max(0, float(bbox.find('ymin').text))
        xmax = min(width, float(bbox.find('xmax').text))
        ymax = min(height, float(bbox.find('ymax').text))
        if xmin >= xmax or ymin >= ymax:
            continue

        objects.append({'name': name, 'bbox': [xmin, ymin, xmax, ymax]})
    return width, height, objects


def collect_data(image_dir):
    """收集所有标注数据"""
    print("\n[1/5] 收集标注数据...")
    categories = set()

    all_data = []
    xml_files = [f for f in os.listdir(image_dir) if f.endswith('.xml')]
    print(f"找到 {len(xml_files)} 个XML文件")


    for xml_file in sorted(xml_files):
        xml_path = os.path.join(image_dir, xml_file)
        base_name = os.path.splitext(xml_file)[0]

        # 匹配对应图片
        image_name = None
        for ext in CONFIG["image_extensions"]:
            candidate = base_name + ext
            if os.path.exists(os.path.join(image_dir, candidate)):
                image_name = candidate
                break
        if not image_name:
            continue

        # 解析XML
        width, height, objects = parse_xml(xml_path)
        if not objects:
            continue

        # 收集类别
        for obj in objects:
            categories.add(obj['name'])
        print(categories)
        all_data.append({
            'xml_file': xml_file, 'image_name': image_name,
            'width': width, 'height': height, 'objects': objects
        })
        print(all_data)

    return all_data, sorted(list(categories))


def create_coco_json(data_list, categories, cat_to_id, output_path):
    """生成COCO格式JSON"""
    coco = {
        'images': [], 'annotations': [],
        'categories': [{'id': cat_to_id[cat], 'name': cat} for cat in categories]
    }

    ann_id = 1
    for img_id, data in enumerate(data_list, 1):
        # 图片信息
        coco['images'].append({
            'id': img_id, 'file_name': data['image_name'],
            'width': data['width'], 'height': data['height']
        })

        # 标注信息（VOC→COCO：xmin,ymin,xmax,ymax → xmin,ymin,w,h）
        for obj in data['objects']:
            xmin, ymin, xmax, ymax = obj['bbox']
            w, h = xmax - xmin, ymax - ymin
            coco['annotations'].append({
                'id': ann_id, 'image_id': img_id, 'category_id': cat_to_id[obj['name']],
                'bbox': [xmin, ymin, w, h], 'area': w * h, 'iscrowd': 0
            })
            ann_id += 1

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(coco, f, ensure_ascii=False, indent=2)
    return len(coco['images']), len(coco['annotations'])


def print_statistics(all_data, categories, train_data, val_data):
    """打印数据集统计信息"""
    print("\n📊 数据集统计:")
    cat_count = defaultdict(int)
    for data in all_data:
        for obj in data['objects']:
            cat_count[obj['name']] += 1

    print(f"类别分布:")
    total = sum(cat_count.values())
    for cat in categories:
        print(f"  - {cat}: {cat_count[cat]} 个标注 ({cat_count[cat] / total * 100:.1f}%)")
    print(f"\n图片数量: 总计 {len(all_data)} 张 | 训练集 {len(train_data)} 张 | 验证集 {len(val_data)} 张")


def main():
    print("=" * 60)
    print("VOC → COCO 格式转换工具")
    print("=" * 60)

    # 1. 检查输入目录
    if not os.path.exists(CONFIG["image_dir"]):
        print(f"❌ 输入目录不存在: {CONFIG['image_dir']}")
        return

    # 2. 收集数据
    all_data, categories = collect_data(CONFIG["image_dir"])
    if not all_data:
        print("❌ 无有效标注数据")
        return
    cat_to_id = {cat: i + 1 for i, cat in enumerate(categories)}
    print(f"检测到 {len(categories)} 个类别: {categories}")

    # 3. 划分训练集/验证集
    print("\n[2/5] 划分数据集...")
    train_data, val_data = train_test_split(
        all_data, train_size=CONFIG["train_ratio"], random_state=CONFIG["random_seed"]
    )

    # 4. 创建输出目录
    print("[3/5] 创建输出目录...")
    annotations_dir = os.path.join(CONFIG["output_dir"], 'annotations')
    images_dir = os.path.join(CONFIG["output_dir"], 'images')
    os.makedirs(annotations_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    # 5. 生成COCO JSON
    print("[4/5] 生成COCO格式文件...")
    train_json = os.path.join(annotations_dir, 'train.json')
    val_json = os.path.join(annotations_dir, 'val.json')
    n_train_img, n_train_ann = create_coco_json(train_data, categories, cat_to_id, train_json)
    n_val_img, n_val_ann = create_coco_json(val_data, categories, cat_to_id, val_json)
    print(f"  - 训练集: {n_train_img} 张图片, {n_train_ann} 个标注")
    print(f"  - 验证集: {n_val_img} 张图片, {n_val_ann} 个标注")

    # 6. 保存类别文件
    label_list_path = os.path.join(CONFIG["output_dir"], 'label_list.txt')
    with open(label_list_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(categories))

    # 7. 复制图片
    if CONFIG["copy_images"]:
        print("[5/5] 复制图片...")
        copied = 0
        for data in all_data:
            src = os.path.join(CONFIG["image_dir"], data['image_name'])
            dst = os.path.join(images_dir, data['image_name'])
            if os.path.exists(src) and not os.path.exists(dst):
                shutil.copy2(src, dst)
                copied += 1
        print(f"  复制完成 {copied} 张图片")

    # 8. 打印统计信息
    print_statistics(all_data, categories, train_data, val_data)
    print("\n✅ 转换完成！")
    print(f"数据集目录: {CONFIG['output_dir']}")


if __name__ == "__main__":
    main()