"""
Convert VisDrone2019-DET annotations to YOLO format.

VisDrone annotation format (per line):
  bbox_left, bbox_top, bbox_width, bbox_height, score, object_category, truncation, occlusion

VisDrone categories:
  0: ignored region  ← skip
  1: pedestrian
  2: people
  3: bicycle
  4: car
  5: van
  6: truck
  7: tricycle
  8: awning-tricycle
  9: bus
  10: motor

YOLO output: <class_id> <cx> <cy> <w> <h>  (all normalized 0–1)
  class_id = visdrone_category - 1  (ignored region dropped, 1→0 … 10→9)
"""

import os
import glob
from pathlib import Path
from PIL import Image

SPLITS = {
    'train': 'VisDrone2019-DET-train',
    'val':   'VisDrone2019-DET-val',
    'test':  'VisDrone2019-DET-test-dev',
}

DATASET_ROOT = Path(__file__).parent.parent / 'datasets' / 'VisDrone2019'
OUT_ROOT     = DATASET_ROOT / 'yolo'


def convert_split(split_name, split_dir):
    src_img_dir = DATASET_ROOT / split_dir / 'images'
    src_ann_dir = DATASET_ROOT / split_dir / 'annotations'
    dst_img_dir = OUT_ROOT / 'images' / split_name
    dst_lbl_dir = OUT_ROOT / 'labels' / split_name

    if not src_img_dir.exists():
        print(f'  Skipping {split_name} — {src_img_dir} not found')
        return 0

    dst_img_dir.mkdir(parents=True, exist_ok=True)
    dst_lbl_dir.mkdir(parents=True, exist_ok=True)

    ann_files = sorted(glob.glob(str(src_ann_dir / '*.txt')))
    converted = 0

    for ann_path in ann_files:
        stem = Path(ann_path).stem
        img_path = src_img_dir / f'{stem}.jpg'
        if not img_path.exists():
            img_path = src_img_dir / f'{stem}.png'
        if not img_path.exists():
            continue

        img = Image.open(img_path)
        W, H = img.size

        lines = []
        with open(ann_path) as f:
            for raw in f:
                parts = raw.strip().split(',')
                if len(parts) < 6:
                    continue
                x, y, w, h = map(float, parts[:4])
                cat = int(parts[5])

                if cat == 0 or w <= 0 or h <= 0:
                    continue

                cls_id = cat - 1   # remap 1-10 → 0-9
                cx = (x + w / 2) / W
                cy = (y + h / 2) / H
                nw = w / W
                nh = h / H
                cx, cy, nw, nh = (
                    max(0.0, min(1.0, v)) for v in (cx, cy, nw, nh)
                )
                lines.append(f'{cls_id} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}')

        # Symlink image
        dst_img = dst_img_dir / img_path.name
        if not dst_img.exists():
            os.symlink(img_path.resolve(), dst_img)

        # Write label
        lbl_path = dst_lbl_dir / f'{stem}.txt'
        with open(lbl_path, 'w') as f:
            f.write('\n'.join(lines))

        converted += 1

    print(f'  {split_name}: {converted} images converted')
    return converted


if __name__ == '__main__':
    print(f'Output: {OUT_ROOT}')
    total = 0
    for name, directory in SPLITS.items():
        total += convert_split(name, directory)
    print(f'\nDone — {total} images total')
    print(f'Dataset YAML: {OUT_ROOT.parent}/visdrone.yaml')
