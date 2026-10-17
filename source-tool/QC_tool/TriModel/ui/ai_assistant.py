from __future__ import annotations
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image
import streamlit as st

from qc.models import BBox2D, LabeledObject

logger = logging.getLogger("QC_AI")


@st.cache_resource
def load_ai_detector():
    """Nạp Bộ ba mô hình AI Tri-Model Consensus Detector (WBF) hoặc YOLOv8 cục bộ."""
    # 1. Thử nạp Tri-Model Ensemble (3 Pipeline + WBF)
    try:
        from qc.ai_detector import get_tri_model_detector
        detector = get_tri_model_detector()
        if detector and detector.is_ready():
            return detector
    except Exception as e:
        logger.warning("Không thể nạp TriModelAIDetector: %s. Thử nạp YOLOv8 cục bộ...", e)

    # 2. Dự phòng nạp YOLOv8 đơn lẻ
    base_dir = Path(__file__).parent.parent
    candidates = [
        base_dir / "models" / "yolov8m.pt",
        base_dir / "models" / "yolov8s.pt",
        base_dir / "yolov8n.pt",
        Path("yolov8n.pt"),
    ]
    for p in candidates:
        if p.exists():
            try:
                from ultralytics import YOLO
                m = YOLO(str(p))
                return m
            except Exception as e:
                logger.warning("Lỗi nạp YOLO từ %s: %s", p, e)
    return None


def detect_missed_objects(
    img_pil: Image.Image,
    user_objects: List[LabeledObject],
    model: Any,
    conf_thresh: float = 0.20,
    ensemble_mode: str = "majority",
) -> List[Dict[str, Any]]:
    """Dùng AI quét ảnh và tìm các vật thể xe/người chưa được gán nhãn."""
    if model is None or img_pil is None:
        return []

    # Nếu là Tri-Model Ensemble (hỗ trợ WBF & đa mô hình đồng thuận)
    if hasattr(model, "detect_missed_and_mismatched"):
        try:
            res = model.detect_missed_and_mismatched(
                img_pil,
                user_objects,
                conf_thresh=conf_thresh,
                ensemble_mode=ensemble_mode,
            )
            return res.get("missed", [])
        except Exception as ex:
            logger.warning("Lỗi Tri-Model cross-check: %s", ex)
            return []

    TARGET_CLASSES = {"car", "truck", "bus", "motorcycle", "person", "bicycle"}
    try:
        w, h = img_pil.size
        adaptive_sz = 1280 if max(w, h) >= 960 else (960 if max(w, h) >= 640 else 640)
        res = model(img_pil, imgsz=adaptive_sz, conf=conf_thresh, verbose=False)
        if not res or len(res[0].boxes) == 0:
            return []
        boxes = res[0].boxes
        missed = []
        for b in boxes:
            cls_id = int(b.cls[0])
            cls_name = model.names[cls_id]
            if cls_name.lower() not in TARGET_CLASSES:
                continue
            x1, y1, x2, y2 = b.xyxy[0].tolist()
            conf = float(b.conf[0])
            ai_box = BBox2D(x1, y1, x2, y2)

            has_match = False
            for uobj in user_objects:
                if uobj.box2d is not None and ai_box.iou(uobj.box2d) > 0.15:
                    has_match = True
                    break
            if not has_match:
                missed.append({
                    "category": cls_name,
                    "confidence": conf,
                    "box2d": ai_box,
                })
        return missed
    except Exception as ex:
        logger.warning("Lỗi AI cross-check: %s", ex)
        return []


def detect_ai_issues(
    img_pil: Image.Image,
    user_objects: List[LabeledObject],
    model: Any,
    conf_thresh: float = 0.20,
    ensemble_mode: str = "majority",
) -> Dict[str, List[Dict[str, Any]]]:
    """Phát hiện cả vật thể bỏ sót và nhãn sai lệch bằng AI."""
    if model is None or img_pil is None:
        return {"missed": [], "mismatched": []}

    if hasattr(model, "detect_missed_and_mismatched"):
        try:
            return model.detect_missed_and_mismatched(
                img_pil,
                user_objects,
                conf_thresh=conf_thresh,
                ensemble_mode=ensemble_mode,
            )
        except Exception as ex:
            logger.warning("Lỗi Tri-Model detect_missed_and_mismatched: %s", ex)
            return {"missed": [], "mismatched": []}

    missed = detect_missed_objects(
        img_pil,
        user_objects,
        model,
        conf_thresh=conf_thresh,
        ensemble_mode=ensemble_mode,
    )
    return {"missed": missed, "mismatched": []}
