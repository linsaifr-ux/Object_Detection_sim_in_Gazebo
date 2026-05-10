"""Fine-tune YOLOv8l on synthetic Gazebo data for cube/cylinder detection."""

from pathlib import Path
from ultralytics import YOLO
import shutil

PROJECT_ROOT = Path(__file__).parent.parent
DATA_YAML    = PROJECT_ROOT / 'datasets' / 'custom_shapes.yaml'
WEIGHTS      = PROJECT_ROOT / 'models' / 'yolov8l.pt'
RUN_DIR      = PROJECT_ROOT / 'training' / 'runs'


def train():
    model = YOLO(str(WEIGHTS))

    print('\n=== Phase 1: freeze backbone (15 epochs) ===\n')
    model.train(
        data=str(DATA_YAML),
        epochs=15,
        imgsz=640,
        batch=8,
        lr0=0.001,
        lrf=0.1,
        warmup_epochs=3,
        freeze=10,
        # Aerial-view augmentations
        flipud=0.5,
        fliplr=0.5,
        degrees=180.0,      # full rotation — drone sees any angle
        scale=0.5,          # scale variation simulates altitude change
        mosaic=1.0,
        mixup=0.1,
        hsv_h=0.02,
        hsv_s=0.8,
        hsv_v=0.5,
        workers=4,
        device=0,
        amp=True,
        project=str(RUN_DIR),
        name='custom_phase1',
        exist_ok=True,
        plots=True,
        patience=10,
    )

    print('\n=== Phase 2: full fine-tune (60 epochs) ===\n')
    phase1_best = RUN_DIR / 'custom_phase1' / 'weights' / 'best.pt'
    model2 = YOLO(str(phase1_best))

    model2.train(
        data=str(DATA_YAML),
        epochs=60,
        imgsz=640,
        batch=8,
        lr0=0.0001,
        lrf=0.01,
        warmup_epochs=0,
        freeze=0,
        flipud=0.5,
        fliplr=0.5,
        degrees=180.0,
        scale=0.5,
        mosaic=1.0,
        mixup=0.15,
        copy_paste=0.1,
        hsv_h=0.02,
        hsv_s=0.8,
        hsv_v=0.5,
        workers=4,
        device=0,
        amp=True,
        project=str(RUN_DIR),
        name='custom_phase2',
        exist_ok=True,
        plots=True,
        patience=15,
    )

    best = RUN_DIR / 'custom_phase2' / 'weights' / 'best.pt'
    out  = PROJECT_ROOT / 'models' / 'yolov8l_custom.pt'
    shutil.copy(best, out)
    print(f'\nModel saved → {out}')


if __name__ == '__main__':
    train()
