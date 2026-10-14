"""
train_models.py — Script huấn luyện / tinh chỉnh 2 mô hình chuyên sâu (Specialized Models)
để tạo bộ 3 mô hình (Tri-Model) cho QC Tool:
  - Model 1: Baseline YOLOv8n (COCO general) -> yolov8n.pt
  - Model 2: Traffic Specialist (xe cộ, ô tô, xe máy, xe tải) -> models/model_traffic_specialist.pt
  - Model 3: Small-Object & Pedestrian Expert (người đi bộ, xe nhỏ, tầm xa) -> models/model_smallobj_expert.pt
"""

from __future__ import annotations
import os
import shutil
import zipfile
import logging
from pathlib import Path
from typing import Optional

from ultralytics import YOLO

logger = logging.getLogger(__name__)


def prepare_dataset_from_zip(
    zip_path: Path,
    target_dir: Path,
    max_images: int = 40,
    val_ratio: float = 0.2,
) -> Path:
    """Trích xuất và chuẩn bị dataset chuẩn YOLO từ file zip."""
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True)

    img_train = target_dir / "images" / "train"
    lbl_train = target_dir / "labels" / "train"
    img_val = target_dir / "images" / "val"
    lbl_val = target_dir / "labels" / "val"

    for d in [img_train, lbl_train, img_val, lbl_val]:
        d.mkdir(parents=True)

    with zipfile.ZipFile(zip_path, "r") as z:
        # Lấy danh sách ảnh hợp lệ
        all_imgs = [
            n for n in z.namelist()
            if (n.startswith("images/") or "/images/" in n)
            and n.lower().endswith((".jpg", ".jpeg", ".png"))
            and "__MACOSX" not in n
        ][:max_images]

        all_entries = set(z.namelist())
        n_train = max(1, int(len(all_imgs) * (1 - val_ratio)))

        for idx, im_path in enumerate(all_imgs):
            is_train = idx < n_train
            dst_img_dir = img_train if is_train else img_val
            dst_lbl_dir = lbl_train if is_train else lbl_val

            stem = Path(im_path).stem
            dest_img = dst_img_dir / f"{stem}.jpg"
            with open(dest_img, "wb") as f:
                f.write(z.read(im_path))

            # Tìm file nhãn tương ứng
            cand_labels = [
                f"labels/{stem}.txt",
                f"du_lieu/labels/{stem}.txt",
                str(Path(im_path).with_suffix(".txt")),
            ]
            for cand in cand_labels:
                if cand in all_entries:
                    with open(dst_lbl_dir / f"{stem}.txt", "wb") as f:
                        f.write(z.read(cand))
                    break

    data_yaml = target_dir / "data.yaml"
    data_yaml.write_text(f"""path: {target_dir.resolve()}
train: images/train
val: images/val
names:
  0: car
""", encoding="utf-8")

    return data_yaml


def train_tri_models(
    base_model_path: Optional[Path] = None,
    dataset_zip: Optional[Path] = None,
    epochs: int = 2,
    output_dir: Optional[Path] = None,
) -> dict:
    """
    Huấn luyện và xuất 2 models chuyên sâu kết hợp cùng Base Model:
      1. Model 2: Traffic Specialist
      2. Model 3: Small-Object Expert
    """
    qc_root = Path(__file__).parent.parent
    if base_model_path is None:
        base_model_path = qc_root / "yolov8n.pt"

    if output_dir is None:
        output_dir = qc_root / "models"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Tìm dataset zip có sẵn trên máy
    if dataset_zip is None or not dataset_zip.is_file():
        candidates = [
            Path(r"C:\Users\tient\Downloads\Group_23\du_lieu_final.zip"),
            Path(r"C:\Users\tient\Downloads\Group_23\du_lieu.zip"),
            Path(r"C:\Users\tient\Downloads\Group_23\du_lieu_v2.zip"),
        ]
        for c in candidates:
            if c.is_file():
                dataset_zip = c
                break

    if not dataset_zip or not dataset_zip.is_file():
        raise FileNotFoundError("Không tìm thấy tệp dataset zip để huấn luyện.")

    work_data_dir = qc_root / "temp_train_dataset"
    data_yaml = prepare_dataset_from_zip(dataset_zip, work_data_dir, max_images=35)

    print(f"[*] Đã chuẩn bị dữ liệu huấn luyện từ {dataset_zip.name}")

    # 1. Train Model 2: Traffic Specialist (Cân bằng đặc trưng xe)
    print("\n" + "=" * 60)
    print("🚀 Bắt đầu huấn luyện Model 2: Traffic Specialist...")
    print("=" * 60)
    m2 = YOLO(str(base_model_path))
    m2.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=416,
        batch=4,
        lr0=0.003,
        weight_decay=0.001,
        project=str(qc_root / "temp_runs"),
        name="train_traffic_specialist",
        exist_ok=True,
        verbose=False,
    )
    best_m2 = Path(m2.trainer.best)
    target_m2 = output_dir / "model_traffic_specialist.pt"
    shutil.copyfile(best_m2, target_m2)
    print(f"[✓] Đã lưu Model 2 thành công tại: {target_m2}")

    # 2. Train Model 3: Small-Object & High-Resolution Specialist
    print("\n" + "=" * 60)
    print("🚀 Bắt đầu huấn luyện Model 3: Small-Object Expert...")
    print("=" * 60)
    m3 = YOLO(str(base_model_path))
    m3.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=512,  # Kích thước ảnh lớn hơn để tối ưu vật thể nhỏ
        batch=4,
        lr0=0.002,
        scale=0.7,   # Tăng cường scale để bắt xe xa/nhỏ
        mosaic=1.0,  # Mosaic ghép 4 ảnh để tăng mật độ vật thể nhỏ
        project=str(qc_root / "temp_runs"),
        name="train_smallobj_expert",
        exist_ok=True,
        verbose=False,
    )
    best_m3 = Path(m3.trainer.best)
    target_m3 = output_dir / "model_smallobj_expert.pt"
    shutil.copyfile(best_m3, target_m3)
    print(f"[✓] Đã lưu Model 3 thành công tại: {target_m3}")

    # Dọn dẹp thư mục tạm
    if work_data_dir.exists():
        shutil.rmtree(work_data_dir, ignore_errors=True)
    temp_runs = qc_root / "temp_runs"
    if temp_runs.exists():
        shutil.rmtree(temp_runs, ignore_errors=True)

    print("\n" + "=" * 60)
    print("🎉 Hoàn tất huấn luyện toàn bộ hệ thống Tri-Model!")
    print(f"  - Model 1 (Base):       {base_model_path}")
    print(f"  - Model 2 (Traffic):    {target_m2}")
    print(f"  - Model 3 (Small-Obj):  {target_m3}")
    print("=" * 60)

    return {
        "model_1": str(base_model_path),
        "model_2": str(target_m2),
        "model_3": str(target_m3),
    }


if __name__ == "__main__":
    train_tri_models()
