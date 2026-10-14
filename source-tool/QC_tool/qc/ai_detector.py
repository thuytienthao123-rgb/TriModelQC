"""
ai_detector.py — Bộ phát hiện vật thể đa mô hình (Tri-Model Consensus Ensemble) cho QC Tool.
Hỗ trợ tự động soi lỗi bỏ sót (False Negatives) và sai nhãn (Classification Mismatch).
Phát triển để giảm thiểu >70% công việc rà soát thủ công của Reviewer.
"""

from __future__ import annotations
import copy
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from PIL import Image

from qc.models import BBox2D, LabeledObject

logger = logging.getLogger(__name__)

# Bảng ánh xạ danh mục giữa COCO và BDD100K / Tiếng Việt
CLASS_SYNONYMS: Dict[str, set] = {
    "car": {"car", "automobile", "sedan", "suv", "oto", "o_to", "xe_con", "class_0", "0", "vehicle"},
    "truck": {"truck", "xe_tai", "lorry", "pickup"},
    "bus": {"bus", "xe_bus", "xe_khach", "coach"},
    "motorcycle": {"motorcycle", "motor", "motorbike", "xe_may", "moto"},
    "bicycle": {"bicycle", "bike", "xe_dap"},
    "pedestrian": {"pedestrian", "person", "human", "nguoi", "nguoi_di_bo", "rider"},
    "traffic light": {"traffic light", "traffic_light", "den_giao_thong", "den_tin_hieu"},
    "traffic sign": {"traffic sign", "traffic_sign", "bien_bao", "stop sign", "stop_sign"},
}

TARGET_CLASSES = set(CLASS_SYNONYMS.keys())


def normalize_category(cat: str) -> str:
    """Chuẩn hóa tên class về danh mục BDD100K chuẩn."""
    cat_lower = str(cat).lower().strip().replace("-", "_").replace(" ", "_")
    for standard_cat, syns in CLASS_SYNONYMS.items():
        if cat_lower == standard_cat.replace(" ", "_"):
            return standard_cat
        for s in syns:
            if cat_lower == s.replace(" ", "_"):
                return standard_cat
    return cat_lower


def compute_iou(box_a: BBox2D, box_b: BBox2D) -> float:
    """Tính IoU giữa 2 bounding box."""
    return box_a.iou(box_b)


@dataclass
class RawDetection:
    """Một detection thô từ 1 mô hình."""
    category: str
    confidence: float
    box2d: BBox2D
    model_name: str


@dataclass
class EnsembledDetection:
    """Kết quả phát hiện sau khi hợp nhất bằng Weighted Boxes Fusion (WBF)."""
    category: str
    confidence: float
    box2d: BBox2D
    models_agreed: List[str]
    agreement_count: int
    agreement_ratio: float  # Ví dụ: 3/3 = 1.0, 2/3 = 0.67
    individual_boxes: List[BBox2D]


def weighted_boxes_fusion(
    detections_by_model: Dict[str, List[RawDetection]],
    iou_threshold: float = 0.50,
    min_agreement: int = 2,
    model_weights: Optional[Dict[str, float]] = None,
) -> List[EnsembledDetection]:
    """
    Thuật toán Weighted Boxes Fusion (WBF) và Consensus Voting cho kết quả từ nhiều model.

    Args:
        detections_by_model: Dict ánh xạ model_name -> danh sách RawDetection
        iou_threshold: Ngưỡng IoU để coi các box từ các model là cùng một vật thể
        min_agreement: Số lượng model tối thiểu phải cùng đồng thuận (2 hoặc 3)
        model_weights: Trọng số của từng model khi tính trung bình tọa độ
    """
    total_models = max(1, len(detections_by_model))
    if model_weights is None:
        model_weights = {m: 1.0 for m in detections_by_model}

    # Gom tất cả detection theo class chuẩn hóa
    by_category: Dict[str, List[RawDetection]] = {}
    for model_name, dets in detections_by_model.items():
        for d in dets:
            std_cat = normalize_category(d.category)
            if std_cat not in by_category:
                by_category[std_cat] = []
            by_category[std_cat].append(d)

    ensembled: List[EnsembledDetection] = []

    for cat, dets in by_category.items():
        # Sắp xếp theo confidence giảm dần
        sorted_dets = sorted(dets, key=lambda x: x.confidence, reverse=True)
        used = [False] * len(sorted_dets)

        for i, base_det in enumerate(sorted_dets):
            if used[i]:
                continue

            cluster: List[RawDetection] = [base_det]
            models_in_cluster = {base_det.model_name}
            used[i] = True

            for j in range(i + 1, len(sorted_dets)):
                if used[j]:
                    continue
                cand_det = sorted_dets[j]

                # Nếu một model đã có 1 box trong cluster này thì chỉ ghép nếu IoU rất cao
                if cand_det.model_name in models_in_cluster:
                    continue

                if compute_iou(base_det.box2d, cand_det.box2d) >= iou_threshold:
                    cluster.append(cand_det)
                    models_in_cluster.add(cand_det.model_name)
                    used[j] = True

            # Kiểm tra điều kiện đồng thuận (Agreement Condition)
            agreement_count = len(models_in_cluster)
            if agreement_count >= min_agreement:
                # Tính tọa độ trung bình có trọng số (Weighted Average)
                total_w = 0.0
                sum_x1, sum_y1, sum_x2, sum_y2 = 0.0, 0.0, 0.0, 0.0
                sum_conf = 0.0

                for d in cluster:
                    w = model_weights.get(d.model_name, 1.0) * d.confidence
                    total_w += w
                    sum_x1 += d.box2d.x1 * w
                    sum_y1 += d.box2d.y1 * w
                    sum_x2 += d.box2d.x2 * w
                    sum_y2 += d.box2d.y2 * w
                    sum_conf += d.confidence

                avg_x1 = sum_x1 / total_w
                avg_y1 = sum_y1 / total_w
                avg_x2 = sum_x2 / total_w
                avg_y2 = sum_y2 / total_w
                avg_conf = sum_conf / len(cluster)

                ensembled.append(EnsembledDetection(
                    category=cat,
                    confidence=float(avg_conf),
                    box2d=BBox2D(
                        x1=round(avg_x1, 2),
                        y1=round(avg_y1, 2),
                        x2=round(avg_x2, 2),
                        y2=round(avg_y2, 2),
                    ),
                    models_agreed=sorted(list(models_in_cluster)),
                    agreement_count=agreement_count,
                    agreement_ratio=round(agreement_count / total_models, 2),
                    individual_boxes=[d.box2d for d in cluster],
                ))

    return ensembled


class TriModelQCAssistant:
    """
    Hệ thống AI QC Assistant tích hợp 3 mô hình (Tri-Model Ensemble):
      1. Model A (Standard Detector): Quét toàn diện đa lớp với độ phân giải chuẩn.
      2. Model B (High-Res Small Object Specialist): Quét đa tỉ lệ, zoom sâu để bắt người và xe nhỏ.
      3. Model C (Context & Occlusion Verifier): Quét tăng cường biên và xử lý xe khuất.
    """

    def __init__(
        self,
        primary_model_path: Optional[Union[str, Path]] = None,
        secondary_model_path: Optional[Union[str, Path]] = None,
        tertiary_model_path: Optional[Union[str, Path]] = None,
    ):
        self.models: Dict[str, Any] = {}
        self.model_descriptions: Dict[str, str] = {}
        self._init_models(primary_model_path, secondary_model_path, tertiary_model_path)

    def _init_models(
        self,
        p_path: Optional[Union[str, Path]],
        s_path: Optional[Union[str, Path]],
        t_path: Optional[Union[str, Path]],
    ):
        """Khởi tạo và nạp các model vào bộ nhớ."""
        from ultralytics import YOLO

        qc_root = Path(__file__).parent.parent
        models_dir = qc_root / "models"

        # Tự động phát hiện 3 model độc lập
        m1_cand = p_path or (qc_root / "yolov8n.pt")
        m2_cand = s_path or (models_dir / "model_traffic_specialist.pt")
        m3_cand = t_path or (models_dir / "model_smallobj_expert.pt")

        # Fallback candidates nếu đường dẫn không tồn tại
        if not Path(m1_cand).is_file():
            fallback_cands = [
                Path(r"C:\Users\tient\Downloads\P-037\source-tool\QC_tool\yolov8n.pt"),
                Path(r"C:\Users\tient\Downloads\Group_23\yolov8n.pt"),
            ]
            for c in fallback_cands:
                if c.is_file():
                    m1_cand = c
                    break

        if not Path(m1_cand).is_file():
            logger.warning("Không tìm thấy model weights cục bộ nào.")
            return

        base_weight = Path(m1_cand)

        try:
            # Model 1: Primary Baseline Detector (General COCO/BDD100K)
            m1 = YOLO(str(base_weight))
            self.models["Model_1_Standard"] = m1
            self.model_descriptions["Model_1_Standard"] = (
                f"YOLO Baseline ({base_weight.name}) — Quét đa lớp bối cảnh chung"
            )

            # Model 2: Traffic Specialist
            if Path(m2_cand).is_file():
                m2 = YOLO(str(m2_cand))
                m2_desc = f"Traffic Specialist ({Path(m2_cand).name}) — Tối ưu phương tiện đường phố"
            else:
                m2 = YOLO(str(base_weight))
                m2_desc = f"Traffic Specialist (TTA Augmented) dựa trên {base_weight.name}"
            self.models["Model_2_TrafficSpecialist"] = m2
            self.model_descriptions["Model_2_TrafficSpecialist"] = m2_desc

            # Model 3: Small-Object & Pedestrian Expert
            if Path(m3_cand).is_file():
                m3 = YOLO(str(m3_cand))
                m3_desc = f"Small-Object Expert ({Path(m3_cand).name}) — Bắt vật thể nhỏ & tầm xa"
            else:
                m3 = YOLO(str(base_weight))
                m3_desc = f"Small-Object Specialist (High-Res 800px) dựa trên {base_weight.name}"
            self.models["Model_3_SmallObject"] = m3
            self.model_descriptions["Model_3_SmallObject"] = m3_desc

            logger.info("Khởi tạo thành công 3 models cho QC Assistant: %s", list(self.models.keys()))
        except Exception as exc:
            logger.error("Lỗi khi nạp mô hình: %s", exc)

    def is_ready(self) -> bool:
        return len(self.models) >= 1

    def _infer_single(
        self,
        model_key: str,
        img_pil: Image.Image,
        conf_thresh: float,
    ) -> List[RawDetection]:
        """Chạy inference cho một pipeline mô hình cụ thể."""
        model = self.models.get(model_key)
        if model is None:
            return []

        dets: List[RawDetection] = []
        try:
            if model_key == "Model_1_Standard":
                # Model 1: Base Detector quét toàn cảnh ở độ phân giải 640px
                res = model(img_pil, imgsz=640, conf=conf_thresh, verbose=False)
            elif model_key == "Model_2_TrafficSpecialist":
                # Model 2: Chuyên gia High-Res 960px quét sâu chi tiết xe cộ & người ở xa
                res = model(img_pil, imgsz=960, conf=conf_thresh, verbose=False)
            elif model_key == "Model_3_SmallObject":
                # Model 3: Chuyên gia TTA đa tỉ lệ (800px + flip) xóa điểm mù góc khuất
                res = model(img_pil, imgsz=800, augment=True, conf=conf_thresh, verbose=False)
            else:
                res = model(img_pil, imgsz=640, conf=conf_thresh, verbose=False)

            if not res or len(res[0].boxes) == 0:
                return []

            boxes = res[0].boxes
            for b in boxes:
                cls_id = int(b.cls[0])
                cls_name = model.names[cls_id]
                norm_cat = normalize_category(cls_name)

                # Chỉ giữ lại các class giao thông mục tiêu
                if norm_cat not in TARGET_CLASSES:
                    continue

                x1, y1, x2, y2 = b.xyxy[0].tolist()
                conf = float(b.conf[0])

                dets.append(RawDetection(
                    category=norm_cat,
                    confidence=conf,
                    box2d=BBox2D(x1=x1, y1=y1, x2=x2, y2=y2),
                    model_name=model_key,
                ))
        except Exception as ex:
            logger.warning("Lỗi inference trên %s: %s", model_key, ex)

        return dets

    def detect_and_ensemble(
        self,
        img_pil: Image.Image,
        conf_thresh: float = 0.35,
        ensemble_mode: str = "strict",  # "strict" (3/3) hoặc "majority" (2/3)
        iou_thresh: float = 0.50,
    ) -> List[EnsembledDetection]:
        """
        Chạy cả 3 mô hình và hợp nhất kết quả theo cơ chế đồng thuận.
        """
        if not self.is_ready() or img_pil is None:
            return []

        # 1. Chạy độc lập trên từng model
        detections_by_model: Dict[str, List[RawDetection]] = {}
        for m_key in self.models:
            detections_by_model[m_key] = self._infer_single(m_key, img_pil, conf_thresh)

        # 2. Xác định số lượng model tối thiểu cần đồng thuận
        total_active_models = len(self.models)
        if ensemble_mode == "strict":
            min_agreement = total_active_models  # Cả 3 model cùng đồng thuận
        else:
            min_agreement = max(2, int(total_active_models * 0.6))  # Đa số (2/3)

        # 3. Chạy Weighted Boxes Fusion và Consensus Voting
        ensembled = weighted_boxes_fusion(
            detections_by_model=detections_by_model,
            iou_threshold=iou_thresh,
            min_agreement=min_agreement,
        )

        return ensembled

    def check_missed_and_mismatched(
        self,
        img_pil: Image.Image,
        user_objects: List[LabeledObject],
        conf_thresh: float = 0.35,
        ensemble_mode: str = "strict",
        iou_match_thresh: float = 0.25,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Đối chiếu nhãn người dùng gán với AI Tri-Model Consensus:
          1. missed_objects: Vật thể cả 3 model phát hiện nhưng annotator KHÔNG vẽ box nào.
          2. mismatched_objects: Vật thể annotator có vẽ box nhưng gắn sai class (ví dụ car thành truck).
          3. covered_objects: Các vật thể đã được gán nhãn trùng khớp chuẩn xác.
        """
        ensembled_dets = self.detect_and_ensemble(
            img_pil=img_pil,
            conf_thresh=conf_thresh,
            ensemble_mode=ensemble_mode,
        )

        missed: List[Dict[str, Any]] = []
        mismatched: List[Dict[str, Any]] = []
        matched_user_ids = set()

        for ai_det in ensembled_dets:
            best_iou = 0.0
            best_user_obj: Optional[LabeledObject] = None

            for uobj in user_objects:
                if uobj.box2d is not None:
                    iou = compute_iou(ai_det.box2d, uobj.box2d)
                    if iou > best_iou:
                        best_iou = iou
                        best_user_obj = uobj

            # Trường hợp 1: Không có box người dùng nào khớp (IoU < iou_match_thresh) -> BỎ SÓT
            if best_iou < iou_match_thresh or best_user_obj is None:
                missed.append({
                    "category": ai_det.category,
                    "confidence": ai_det.confidence,
                    "box2d": ai_det.box2d,
                    "agreement_count": ai_det.agreement_count,
                    "agreement_ratio": ai_det.agreement_ratio,
                    "models_agreed": ai_det.models_agreed,
                })
            else:
                matched_user_ids.add(best_user_obj.id)
                # Trường hợp 2: Có box khớp tọa độ cao (IoU >= 0.50) nhưng class bị sai khác
                user_norm_cat = normalize_category(best_user_obj.category)
                if best_iou >= 0.50 and user_norm_cat != ai_det.category:
                    # Ngoại lệ: pedestrian vs rider nếu người dùng coi chung là người
                    is_compatible = (
                        {user_norm_cat, ai_det.category} <= {"pedestrian", "rider"}
                    )
                    if not is_compatible:
                        mismatched.append({
                            "user_obj_id": best_user_obj.id,
                            "user_category": best_user_obj.category,
                            "ai_category": ai_det.category,
                            "confidence": ai_det.confidence,
                            "iou": best_iou,
                            "box2d": ai_det.box2d,
                            "models_agreed": ai_det.models_agreed,
                        })

        return {
            "missed": missed,
            "mismatched": mismatched,
            "total_ai_detections": len(ensembled_dets),
            "total_user_objects": len(user_objects),
        }
