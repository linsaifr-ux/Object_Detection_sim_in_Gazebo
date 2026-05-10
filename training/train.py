"""
Fine-tune YOLOv8l on VisDrone2019 for drone-view object detection.

GTX 1070 (8 GB VRAM) tuned settings:
  - imgsz 640, batch 8
  - Frozen backbone for first 10 epochs, then full fine-tune
  - Mosaic + mixup augmentation for aerial scene diversity
"""

from pathlib import Path
from ultralytics import YOLO

PROJECT_ROOT = Path(__file__).parent.parent
WEIGHTS      = PROJECT_ROOT / 'models' / 'yolov8l.pt'
DATA_YAML    = PROJECT_ROOT / 'datasets' / 'visdrone.yaml'
RUN_DIR      = PROJECT_ROOT / 'training' / 'runs'


def train():
    model = YOLO(str(WEIGHTS))

    # --- Phase 1: freeze backbone, warm up head ---
    print('\n=== Phase 1: backbone frozen (10 epochs) ===\n')
    model.train(
        data=str(DATA_YAML),
        epochs=10,
        imgsz=640,
        batch=8,
        lr0=0.001,
        lrf=0.1,
        warmup_epochs=3,
        freeze=10,                  # freeze first 10 backbone layers
        mosaic=1.0,
        mixup=0.1,
        copy_paste=0.1,
        degrees=10,                 # rotation augmentation for aerial views
        flipud=0.5,                 # drones see any orientation
        fliplr=0.5,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        workers=4,
        device=0,
        project=str(RUN_DIR),
        name='visdrone_phase1',
        exist_ok=True,
        save=True,
        plots=True,
        val=True,
        patience=10,
        amp=True,                   # mixed precision — halves VRAM usage
    )

    # --- Phase 2: full fine-tune ---
    print('\n=== Phase 2: full fine-tune (50 epochs) ===\n')
    phase1_best = RUN_DIR / 'visdrone_phase1' / 'weights' / 'best.pt'
    model2 = YOLO(str(phase1_best))

    model2.train(
        data=str(DATA_YAML),
        epochs=50,
        imgsz=640,
        batch=8,
        lr0=0.0001,                 # lower LR for fine-tune
        lrf=0.01,
        warmup_epochs=0,
        freeze=0,                   # unfreeze everything
        mosaic=1.0,
        mixup=0.15,
        copy_paste=0.15,
        degrees=15,
        flipud=0.5,
        fliplr=0.5,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        workers=4,
        device=0,
        project=str(RUN_DIR),
        name='visdrone_phase2',
        exist_ok=True,
        save=True,
        plots=True,
        val=True,
        patience=15,
        amp=True,
    )

    best = RUN_DIR / 'visdrone_phase2' / 'weights' / 'best.pt'
    out  = PROJECT_ROOT / 'models' / 'yolov8l_visdrone.pt'
    import shutil
    shutil.copy(best, out)
    print(f'\nFine-tuned model saved to: {out}')
    print('Update run.sh or launch params to use yolov8l_visdrone.pt')


if __name__ == '__main__':
    train()
