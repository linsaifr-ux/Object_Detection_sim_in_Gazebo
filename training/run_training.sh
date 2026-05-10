#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== VisDrone2019 Fine-tuning Pipeline ==="
echo ""

# Check dataset exists
if [ ! -d "$PROJECT_DIR/datasets/VisDrone2019/VisDrone2019-DET-train" ]; then
    echo "ERROR: Dataset not found."
    echo ""
    echo "Download VisDrone2019-DET from http://aiskyeye.com/ and extract into:"
    echo "  $PROJECT_DIR/datasets/VisDrone2019/"
    echo ""
    echo "Expected structure:"
    echo "  datasets/VisDrone2019/"
    echo "  ├── VisDrone2019-DET-train/  (images/ + annotations/)"
    echo "  ├── VisDrone2019-DET-val/    (images/ + annotations/)"
    echo "  └── VisDrone2019-DET-test-dev/ (optional)"
    exit 1
fi

source "$PROJECT_DIR/venv/bin/activate"

echo "[1/2] Converting VisDrone annotations to YOLO format..."
python3 "$PROJECT_DIR/training/convert_visdrone.py"

echo ""
echo "[2/2] Starting fine-tuning (Phase 1: 10 epochs + Phase 2: 50 epochs)..."
echo "      Estimated time on GTX 1070: ~3-4 hours"
echo ""
python3 "$PROJECT_DIR/training/train.py"
