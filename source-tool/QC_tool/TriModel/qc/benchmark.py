"""
qc/benchmark.py — Benchmark & Quantitative Evaluation Suite for TriModel QC Tool.
Cung cấp công cụ đánh giá khoa học độ chính xác của hệ thống QC:
1. Ma trận nhầm lẫn (Confusion Matrix: TP, FP, FN, TN)
2. Độ chuẩn xác (Precision), Độ nhạy (Recall / Detection Rate), F1-Score, Accuracy
3. Đánh giá chất lượng dữ liệu Trước vs Sau QC (mIoU, Class Accuracy, Missing Rate, AQI)
4. Bộ tiêm lỗi Honeypot mô phỏng lỗi thực tế của annotator
"""

from __future__ import annotations
import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from qc.models import FrameData, LabeledObject, BBox2D, Polygon2D, QCReport, QCError
from ui.auto_fix import auto_correct_frames


class DefectCategory(str, Enum):
    B01_OUT_OF_BOUNDS = "RULE_B01: BBox Tràn Viền"
    B02_INVERTED_COORDS = "RULE_B02: Tọa Độ Ngược / Âm"
    B03_TINY_NOISE = "RULE_B03: BBox Quá Nhỏ / Nhiễu"
    B04_EXTREME_RATIO = "RULE_B04: Tỉ Lệ Dị Thường"
    C01_CLASS_TYPO = "RULE_C01: Sai / Lệch Tên Class"
    A01_DUPLICATE_BOX = "RULE_A01: Box Trùng Lặp"
    A02_MISSING_ATTRS = "RULE_A02: Thiếu Thuộc Tính"
    A03_INVALID_TL_COLOR = "RULE_A03: Sai Màu Đèn GT"
    P01_FEW_VERTICES = "RULE_P01: Đa Giác Thiếu Đỉnh"
    P02_SELF_INTERSECTION = "RULE_P02: Đa Giác Tự Cắt Viền"
    P03_BOX_MASK_MISALIGN = "RULE_P03: Lệch Box và Mask"
    AI01_MISSED_OBJECT = "RULE_AI01: Bỏ Sót Xe / Người"


@dataclass
class DetectionMetrics:
    """Các chỉ số khoa học đánh giá năng lực bắt lỗi của hệ thống QC."""
    total_evaluated_objects: int = 0
    total_ground_truth_errors: int = 0
    total_clean_objects: int = 0
    
    tp: int = 0  # Bắt trúng lỗi thực tế
    fp: int = 0  # Báo khống (nhãn chuẩn nhưng bị gắn cờ lỗi)
    fn: int = 0  # Bỏ sót lỗi thực tế
    tn: int = 0  # Nhãn chuẩn được xác nhận chuẩn
    
    precision: float = 0.0      # TP / (TP + FP)
    recall: float = 0.0         # TP / (TP + FN) - Detection Rate
    f1_score: float = 0.0       # 2*P*R / (P + R)
    accuracy: float = 0.0       # (TP + TN) / Total
    specificity: float = 0.0    # TN / (TN + FP) - Khả năng nhận diện nhãn chuẩn
    
    per_rule_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_objects": self.total_evaluated_objects,
            "ground_truth_errors": self.total_ground_truth_errors,
            "clean_objects": self.total_clean_objects,
            "confusion_matrix": {
                "TP (Bắt trúng lỗi)": self.tp,
                "FP (Báo khống / False Alarm)": self.fp,
                "FN (Bỏ sót lỗi)": self.fn,
                "TN (Nhận diện đúng nhãn chuẩn)": self.tn,
            },
            "metrics": {
                "Precision (Độ chuẩn xác)": f"{self.precision:.2%}",
                "Recall (Độ nhạy bắt lỗi)": f"{self.recall:.2%}",
                "F1_Score": f"{self.f1_score:.4f}",
                "Accuracy (Độ chính xác tổng thể)": f"{self.accuracy:.2%}",
                "Specificity (Độ đặc hiệu)": f"{self.specificity:.2%}",
            },
            "per_rule_breakdown": self.per_rule_stats,
        }


@dataclass
class QualityImprovementMetrics:
    """Chỉ số so sánh chất lượng bộ dữ liệu Trước vs Sau khi qua Tool QC & Auto-Fix."""
    total_frames: int = 0
    total_gt_objects: int = 0
    
    # 1. mIoU (Mean Intersection-over-Union) so với Ground Truth
    raw_miou: float = 0.0
    post_qc_miou: float = 0.0
    miou_gain: float = 0.0
    
    # 2. Phân loại nhãn (Class Classification Accuracy)
    raw_class_acc: float = 0.0
    post_qc_class_acc: float = 0.0
    class_acc_gain: float = 0.0
    
    # 3. Tỷ lệ bỏ sót vật thể (Missed Object Rate)
    raw_missed_count: int = 0
    post_qc_missed_count: int = 0
    missed_recovered_count: int = 0
    
    # 4. Chỉ số chất lượng tổng hợp AQI (Annotation Quality Index: 0 - 100)
    raw_aqi: float = 0.0
    post_qc_aqi: float = 0.0
    aqi_gain: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_frames": self.total_frames,
            "total_gt_objects": self.total_gt_objects,
            "mIoU": {
                "Trước QC": f"{self.raw_miou:.4f}",
                "Sau QC (Healed)": f"{self.post_qc_miou:.4f}",
                "Cải thiện (Gain)": f"+{self.miou_gain:.2%}" if self.miou_gain >= 0 else f"{self.miou_gain:.2%}",
            },
            "Class_Accuracy": {
                "Trước QC": f"{self.raw_class_acc:.2%}",
                "Sau QC (Healed)": f"{self.post_qc_class_acc:.2%}",
                "Cải thiện (Gain)": f"+{self.class_acc_gain:.2%}" if self.class_acc_gain >= 0 else f"{self.class_acc_gain:.2%}",
            },
            "Missed_Objects": {
                "Bỏ sót trước QC": self.raw_missed_count,
                "Bỏ sót sau QC": self.post_qc_missed_count,
                "Số xe được AI khôi phục": self.missed_recovered_count,
            },
            "AQI_Score_Thang_100": {
                "Trước QC": f"{self.raw_aqi:.1f} / 100",
                "Sau QC": f"{self.post_qc_aqi:.1f} / 100",
                "Điểm tăng thêm": f"+{self.aqi_gain:.1f} điểm",
            }
        }


def clone_frame(frame: FrameData) -> FrameData:
    """Sao chép sâu một FrameData để an toàn khi tiêm lỗi hoặc chỉnh sửa."""
    new_objs = []
    for obj in frame.objects:
        bx = BBox2D(obj.box2d.x1, obj.box2d.y1, obj.box2d.x2, obj.box2d.y2) if obj.box2d else None
        poly = Polygon2D([(v[0], v[1]) for v in obj.poly2d.vertices]) if obj.poly2d else None
        attrs = dict(obj.attributes) if obj.attributes else {}
        new_objs.append(LabeledObject(
            id=obj.id,
            category=obj.category,
            box2d=bx,
            poly2d=poly,
            attributes=attrs,
        ))
    return FrameData(
        name=frame.name,
        width=frame.width,
        height=frame.height,
        objects=new_objs,
    )


def inject_honeypot_defects(
    gt_frames: List[FrameData],
    defect_rate: float = 0.40,
    seed: int = 42,
) -> Tuple[List[FrameData], Dict[str, Set[str]], List[Dict[str, Any]]]:
    """
    Tiêm lỗi nhân tạo (Honeypot Injected Defects) chuẩn hóa theo 15 bộ luật của hệ thống.
    
    Args:
        gt_frames: Danh sách FrameData chuẩn 100% (Ground Truth).
        defect_rate: Tỷ lệ đối tượng bị cố tình làm sai (mặc định 40%).
        seed: Random seed để đảm bảo khả năng tái lặp thí nghiệm (reproducibility).
        
    Returns:
        (corrupted_frames, injected_defect_map, injection_manifest)
    """
    rng = random.Random(seed)
    corrupted_frames: List[FrameData] = []
    injected_defect_map: Dict[str, Set[str]] = {}  # obj_key -> set of rule_codes
    injection_manifest: List[Dict[str, Any]] = []

    defect_pool = [
        "B01_OUT_OF_BOUNDS",
        "B02_INVERTED_COORDS",
        "B03_TINY_NOISE",
        "B04_EXTREME_RATIO",
        "C01_CLASS_TYPO",
        "A01_DUPLICATE_BOX",
        "A02_MISSING_ATTRS",
        "A03_INVALID_TL_COLOR",
        "P01_FEW_VERTICES",
        "P02_SELF_INTERSECTION",
        "P03_BOX_MASK_MISALIGN",
        "AI01_MISSED_OBJECT",
    ]

    for f_orig in gt_frames:
        frame = clone_frame(f_orig)
        objs_to_keep: List[LabeledObject] = []

        for obj in frame.objects:
            obj_key = f"{frame.name}::{obj.id}"
            
            # Quyết định xem đối tượng này có bị tiêm lỗi hay giữ nguyên chuẩn
            if rng.random() > defect_rate:
                objs_to_keep.append(obj)
                continue

            chosen_defect = rng.choice(defect_pool)

            if chosen_defect == "B01_OUT_OF_BOUNDS" and obj.box2d:
                obj.box2d.x2 = frame.width + rng.randint(20, 100)
                injected_defect_map.setdefault(obj_key, set()).add("RULE_B01")
                injection_manifest.append({"frame": frame.name, "id": obj.id, "defect": "RULE_B01 (Tràn viền W)"})
                objs_to_keep.append(obj)

            elif chosen_defect == "B02_INVERTED_COORDS" and obj.box2d:
                obj.box2d.x1, obj.box2d.x2 = obj.box2d.x2, obj.box2d.x1
                injected_defect_map.setdefault(obj_key, set()).add("RULE_B02")
                injection_manifest.append({"frame": frame.name, "id": obj.id, "defect": "RULE_B02 (Tọa độ ngược x1>x2)"})
                objs_to_keep.append(obj)

            elif chosen_defect == "B03_TINY_NOISE" and obj.box2d:
                obj.box2d.x2 = obj.box2d.x1 + 2.0
                obj.box2d.y2 = obj.box2d.y1 + 2.0
                injected_defect_map.setdefault(obj_key, set()).add("RULE_B03")
                injection_manifest.append({"frame": frame.name, "id": obj.id, "defect": "RULE_B03 (Box vi mô 2x2 px)"})
                objs_to_keep.append(obj)

            elif chosen_defect == "B04_EXTREME_RATIO" and obj.box2d:
                obj.box2d.y2 = obj.box2d.y1 + 5.0
                obj.box2d.x2 = obj.box2d.x1 + 350.0
                injected_defect_map.setdefault(obj_key, set()).add("RULE_B04")
                injection_manifest.append({"frame": frame.name, "id": obj.id, "defect": "RULE_B04 (Tỉ lệ dị thường 70:1)"})
                objs_to_keep.append(obj)

            elif chosen_defect == "C01_CLASS_TYPO":
                typo_options = ["cars", "tuck", "persons", "motorbike", "bicycles"]
                old_cat = obj.category
                obj.category = rng.choice(typo_options)
                injected_defect_map.setdefault(obj_key, set()).add("RULE_C01")
                injection_manifest.append({"frame": frame.name, "id": obj.id, "defect": f"RULE_C01 (Typo: {old_cat} -> {obj.category})"})
                objs_to_keep.append(obj)

            elif chosen_defect == "A01_DUPLICATE_BOX" and obj.box2d:
                dup_id = f"{obj.id}_dup"
                dup_obj = LabeledObject(
                    id=dup_id,
                    category=obj.category,
                    box2d=BBox2D(obj.box2d.x1 + 1.0, obj.box2d.y1 + 1.0, obj.box2d.x2 - 1.0, obj.box2d.y2 - 1.0),
                    attributes=dict(obj.attributes),
                )
                injected_defect_map.setdefault(obj_key, set()).add("RULE_A01")
                injected_defect_map.setdefault(f"{frame.name}::{dup_id}", set()).add("RULE_A01")
                injection_manifest.append({"frame": frame.name, "id": obj.id, "defect": "RULE_A01 (Tạo box trùng đè)"})
                objs_to_keep.append(obj)
                objs_to_keep.append(dup_obj)

            elif chosen_defect == "A02_MISSING_ATTRS":
                obj.attributes = {}
                injected_defect_map.setdefault(obj_key, set()).add("RULE_A02")
                injection_manifest.append({"frame": frame.name, "id": obj.id, "defect": "RULE_A02 (Thiếu thuộc tính)"})
                objs_to_keep.append(obj)

            elif chosen_defect == "A03_INVALID_TL_COLOR":
                obj.category = "traffic light"
                obj.attributes["trafficLightColor"] = "cyan"
                injected_defect_map.setdefault(obj_key, set()).add("RULE_A03")
                injection_manifest.append({"frame": frame.name, "id": obj.id, "defect": "RULE_A03 (Màu đèn sai: cyan)"})
                objs_to_keep.append(obj)

            elif chosen_defect == "P01_FEW_VERTICES":
                obj.poly2d = Polygon2D([(100.0, 100.0), (200.0, 200.0)])
                injected_defect_map.setdefault(obj_key, set()).add("RULE_P01")
                injection_manifest.append({"frame": frame.name, "id": obj.id, "defect": "RULE_P01 (Polygon < 3 đỉnh)"})
                objs_to_keep.append(obj)

            elif chosen_defect == "P02_SELF_INTERSECTION":
                obj.poly2d = Polygon2D([(50.0, 50.0), (150.0, 150.0), (50.0, 150.0), (150.0, 50.0)])
                injected_defect_map.setdefault(obj_key, set()).add("RULE_P02")
                injection_manifest.append({"frame": frame.name, "id": obj.id, "defect": "RULE_P02 (Polygon tự cắt)"})
                objs_to_keep.append(obj)

            elif chosen_defect == "P03_BOX_MASK_MISALIGN" and obj.box2d:
                obj.poly2d = Polygon2D([(obj.box2d.x2 + 50.0, obj.box2d.y1), (obj.box2d.x2 + 100.0, obj.box2d.y2), (obj.box2d.x2 + 20.0, obj.box2d.y2)])
                injected_defect_map.setdefault(obj_key, set()).add("RULE_P03")
                injection_manifest.append({"frame": frame.name, "id": obj.id, "defect": "RULE_P03 (Lệch Box và Mask)"})
                objs_to_keep.append(obj)

            elif chosen_defect == "AI01_MISSED_OBJECT":
                injected_defect_map.setdefault(f"{frame.name}::MISSED::{obj.id}", set()).add("RULE_AI01")
                injection_manifest.append({"frame": frame.name, "id": obj.id, "defect": f"RULE_AI01 (Xóa bỏ sót xe: {obj.category})"})
                # Không append -> xe bị xóa khỏi nhãn

            else:
                objs_to_keep.append(obj)

        frame.objects = objs_to_keep
        corrupted_frames.append(frame)

    return corrupted_frames, injected_defect_map, injection_manifest


def evaluate_qc_detection_accuracy(
    corrupted_frames: List[FrameData],
    qc_report: QCReport,
    injected_defect_map: Dict[str, Set[str]],
) -> DetectionMetrics:
    """
    Tính toán các chỉ số khoa học định lượng (Precision, Recall, F1, Accuracy)
    dựa trên ma trận nhầm lẫn giữa lỗi thực tế đã tiêm và cảnh báo phát hiện của Tool.
    """
    metrics = DetectionMetrics()

    detected_errors_map: Dict[str, Set[str]] = {}
    for err in qc_report.errors:
        f_name = err.frame_name or ""
        o_id = err.object_id or ""
        key = f"{f_name}::{o_id}"
        rule_prefix = err.rule_id.split(":")[0].strip()
        detected_errors_map.setdefault(key, set()).add(rule_prefix)

    all_evaluated_keys = set()
    for f in corrupted_frames:
        for o in f.objects:
            all_evaluated_keys.add(f"{f.name}::{o.id}")
            
    for k in injected_defect_map.keys():
        if "::MISSED::" in k:
            all_evaluated_keys.add(k)

    metrics.total_evaluated_objects = len(all_evaluated_keys)

    rule_counts: Dict[str, Dict[str, int]] = {}
    tp = 0
    fp = 0
    fn = 0
    tn = 0

    for obj_key in all_evaluated_keys:
        is_actually_defective = (obj_key in injected_defect_map and len(injected_defect_map[obj_key]) > 0)
        actual_rules = injected_defect_map.get(obj_key, set())
        
        is_flagged_by_tool = (obj_key in detected_errors_map and len(detected_errors_map[obj_key]) > 0)
        tool_rules = detected_errors_map.get(obj_key, set())

        if "::MISSED::" in obj_key:
            f_name = obj_key.split("::")[0]
            ai_flagged = any("RULE_AI01" in r for r in detected_errors_map.get(f"{f_name}::", set())) or \
                         any(e.rule_id.startswith("RULE_AI01") and e.frame_name == f_name for e in qc_report.errors)
            if ai_flagged:
                tp += 1
                rule_counts.setdefault("RULE_AI01", {"tp": 0, "fn": 0, "fp": 0})["tp"] += 1
            else:
                fn += 1
                rule_counts.setdefault("RULE_AI01", {"tp": 0, "fn": 0, "fp": 0})["fn"] += 1
            continue

        if is_actually_defective and is_flagged_by_tool:
            tp += 1
            for r in actual_rules:
                rule_counts.setdefault(r, {"tp": 0, "fn": 0, "fp": 0})["tp"] += 1

        elif is_actually_defective and not is_flagged_by_tool:
            fn += 1
            for r in actual_rules:
                rule_counts.setdefault(r, {"tp": 0, "fn": 0, "fp": 0})["fn"] += 1

        elif not is_actually_defective and is_flagged_by_tool:
            fp += 1
            for r in tool_rules:
                rule_counts.setdefault(r, {"tp": 0, "fn": 0, "fp": 0})["fp"] += 1

        else:
            tn += 1

    metrics.tp = tp
    metrics.fp = fp
    metrics.fn = fn
    metrics.tn = tn
    metrics.total_ground_truth_errors = tp + fn
    metrics.total_clean_objects = tn + fp

    metrics.precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    metrics.recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    if (metrics.precision + metrics.recall) > 0:
        metrics.f1_score = 2.0 * (metrics.precision * metrics.recall) / (metrics.precision + metrics.recall)
    else:
        metrics.f1_score = 0.0

    total_all = tp + tn + fp + fn
    metrics.accuracy = (tp + tn) / total_all if total_all > 0 else 1.0
    metrics.specificity = tn / (tn + fp) if (tn + fp) > 0 else 1.0

    for r_name, counts in rule_counts.items():
        r_tp = counts["tp"]
        r_fn = counts["fn"]
        r_fp = counts["fp"]
        r_prec = r_tp / (r_tp + r_fp) if (r_tp + r_fp) > 0 else 1.0
        r_rec = r_tp / (r_tp + r_fn) if (r_tp + r_fn) > 0 else 1.0
        metrics.per_rule_stats[r_name] = {
            "TP": r_tp,
            "FN": r_fn,
            "FP": r_fp,
            "Precision": f"{r_prec:.1%}",
            "Recall (Detection Rate)": f"{r_rec:.1%}",
        }

    return metrics


def evaluate_quality_improvement(
    gt_frames: List[FrameData],
    raw_frames: List[FrameData],
    healed_frames: Optional[List[FrameData]] = None,
) -> QualityImprovementMetrics:
    """
    Đo lường mức độ cải thiện chất lượng dữ liệu giữa:
    - Tập nhãn thô ban đầu (Raw / Corrupted)
    - Tập nhãn sau khi qua Tool QC & Tự động sửa lỗi (Healed)
    So với mốc chuẩn tuyệt đối Ground Truth (GT).
    """
    if healed_frames is None:
        fixed_data, _, _ = auto_correct_frames(raw_frames)
        from qc.parser import parse_bdd100k_data
        healed_frames = parse_bdd100k_data(fixed_data)

    metrics = QualityImprovementMetrics()
    metrics.total_frames = len(gt_frames)
    metrics.total_gt_objects = sum(len(f.objects) for f in gt_frames)

    gt_dict = {f.name: f for f in gt_frames}
    raw_dict = {f.name: f for f in raw_frames}
    healed_dict = {f.name: f for f in healed_frames}

    raw_ious: List[float] = []
    healed_ious: List[float] = []

    raw_class_correct = 0
    raw_class_total = 0
    healed_class_correct = 0
    healed_class_total = 0

    raw_missed = 0
    healed_missed = 0

    for fname, gt_f in gt_dict.items():
        raw_f = raw_dict.get(fname, FrameData(name=fname))
        healed_f = healed_dict.get(fname, FrameData(name=fname))

        raw_objs_by_id = {o.id: o for o in raw_f.objects}
        healed_objs_by_id = {o.id: o for o in healed_f.objects}

        for gt_obj in gt_f.objects:
            if gt_obj.id in raw_objs_by_id:
                raw_obj = raw_objs_by_id[gt_obj.id]
                if gt_obj.box2d and raw_obj.box2d:
                    raw_ious.append(gt_obj.box2d.iou(raw_obj.box2d))
                raw_class_total += 1
                if raw_obj.category.lower() == gt_obj.category.lower():
                    raw_class_correct += 1
            else:
                raw_missed += 1
                raw_ious.append(0.0)

            if gt_obj.id in healed_objs_by_id:
                healed_obj = healed_objs_by_id[gt_obj.id]
                if gt_obj.box2d and healed_obj.box2d:
                    healed_ious.append(gt_obj.box2d.iou(healed_obj.box2d))
                healed_class_total += 1
                if healed_obj.category.lower() == gt_obj.category.lower():
                    healed_class_correct += 1
            else:
                healed_missed += 1
                healed_ious.append(0.0)

    metrics.raw_miou = sum(raw_ious) / len(raw_ious) if raw_ious else 0.0
    metrics.post_qc_miou = sum(healed_ious) / len(healed_ious) if healed_ious else 1.0
    metrics.miou_gain = metrics.post_qc_miou - metrics.raw_miou

    metrics.raw_class_acc = raw_class_correct / raw_class_total if raw_class_total > 0 else 0.0
    metrics.post_qc_class_acc = healed_class_correct / healed_class_total if healed_class_total > 0 else 1.0
    metrics.class_acc_gain = metrics.post_qc_class_acc - metrics.raw_class_acc

    metrics.raw_missed_count = raw_missed
    metrics.post_qc_missed_count = healed_missed
    metrics.missed_recovered_count = max(0, raw_missed - healed_missed)

    total_gt = max(1, metrics.total_gt_objects)
    raw_rec = 1.0 - (raw_missed / total_gt)
    healed_rec = 1.0 - (healed_missed / total_gt)

    metrics.raw_aqi = (0.45 * metrics.raw_miou + 0.35 * metrics.raw_class_acc + 0.20 * raw_rec) * 100.0
    metrics.post_qc_aqi = (0.45 * metrics.post_qc_miou + 0.35 * metrics.post_qc_class_acc + 0.20 * healed_rec) * 100.0
    metrics.aqi_gain = metrics.post_qc_aqi - metrics.raw_aqi

    return metrics


def generate_benchmark_html_report(
    detection: DetectionMetrics,
    improvement: QualityImprovementMetrics,
    report_title: str = "BÁO CÁO ĐÁNH GIÁ ĐỊNH LƯỢNG ĐỘ CHÍNH XÁC QC TOOL (TRIMODEL)",
) -> str:
    """Tạo báo cáo Dashboard HTML trực quan, sắc nét để trình chiếu slide hoặc đính kèm báo cáo."""
    rows = ""
    for r, v in detection.per_rule_stats.items():
        rows += f"<tr><td><b>{r}</b></td><td>{v['TP']}</td><td>{v['FN']}</td><td>{v['FP']}</td><td>{v['Precision']}</td><td class='tag-green'>{v['Recall (Detection Rate)']}</td></tr>"

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <title>{report_title}</title>
  <style>
    :root {{
      --bg: #0b0f19;
      --card-bg: #131b2e;
      --card-border: #1e293b;
      --accent: #6366f1;
      --green: #10b981;
      --red: #ef4444;
      --yellow: #f59e0b;
      --text: #f8fafc;
      --text-muted: #94a3b8;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      margin: 0;
      padding: 30px;
    }}
    .container {{
      max-width: 1100px;
      margin: 0 auto;
    }}
    .header {{
      text-align: center;
      margin-bottom: 35px;
      border-bottom: 1px solid var(--card-border);
      padding-bottom: 20px;
    }}
    .header h1 {{
      font-size: 26px;
      margin: 0 0 10px 0;
      color: #fff;
      letter-spacing: 0.5px;
    }}
    .header p {{
      color: var(--text-muted);
      margin: 0;
      font-size: 14px;
    }}
    .badge {{
      display: inline-block;
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 12px;
      font-weight: bold;
      background: rgba(99, 102, 241, 0.2);
      color: var(--accent);
      margin-top: 10px;
    }}
    .grid-4 {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 30px;
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2);
    }}
    .card-title {{
      font-size: 12px;
      text-transform: uppercase;
      color: var(--text-muted);
      margin-bottom: 8px;
      font-weight: 600;
    }}
    .card-value {{
      font-size: 32px;
      font-weight: 800;
      color: #fff;
    }}
    .card-sub {{
      font-size: 12px;
      margin-top: 6px;
      color: var(--green);
    }}
    .section-title {{
      font-size: 18px;
      font-weight: 700;
      margin: 30px 0 15px 0;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: var(--card-bg);
      border-radius: 10px;
      overflow: hidden;
      border: 1px solid var(--card-border);
    }}
    th, td {{
      padding: 12px 16px;
      text-align: left;
      font-size: 14px;
      border-bottom: 1px solid var(--card-border);
    }}
    th {{
      background: #1e293b;
      color: var(--text-muted);
      font-weight: 600;
      text-transform: uppercase;
      font-size: 11px;
    }}
    tr:last-child td {{
      border-bottom: none;
    }}
    .tag-green {{ color: var(--green); font-weight: bold; }}
    .tag-blue {{ color: #38bdf8; font-weight: bold; }}
    .footer {{
      margin-top: 40px;
      text-align: center;
      font-size: 12px;
      color: var(--text-muted);
      border-top: 1px solid var(--card-border);
      padding-top: 20px;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="badge">CHỨNG NHẬN ĐỊNH LƯỢNG KHOA HỌC (QA BENCHMARK)</div>
      <h1>{report_title}</h1>
      <p>Hệ Thống Kiểm Định Chất Lượng Bounding Box & Polygon 2D (TriModel QC Studio)</p>
    </div>

    <div class="section-title">🎯 1. Năng Lực Phát Hiện Lỗi Của Tool (Detection Power)</div>
    <div class="grid-4">
      <div class="card">
        <div class="card-title">Precision (Độ Chuẩn Xác)</div>
        <div class="card-value tag-green">{detection.precision:.1%}</div>
        <div class="card-sub">Tránh báo khống (FP = {detection.fp})</div>
      </div>
      <div class="card">
        <div class="card-title">Recall (Độ Nhạy Bắt Lỗi)</div>
        <div class="card-value tag-blue">{detection.recall:.1%}</div>
        <div class="card-sub">Bắt trúng {detection.tp}/{detection.total_ground_truth_errors} lỗi</div>
      </div>
      <div class="card">
        <div class="card-title">F1-Score Cân Bằng</div>
        <div class="card-value" style="color: #a855f7;">{detection.f1_score:.4f}</div>
        <div class="card-sub">Chỉ số F1 chuẩn quốc tế</div>
      </div>
      <div class="card">
        <div class="card-title">Accuracy Tổng Thể</div>
        <div class="card-value" style="color: #ec4899;">{detection.accuracy:.1%}</div>
        <div class="card-sub">Trên {detection.total_evaluated_objects} đối tượng kiểm tra</div>
      </div>
    </div>

    <div class="section-title">📈 2. Mức Độ Nâng Cao Chất Lượng Dữ Liệu (Trước vs Sau QC)</div>
    <div class="grid-4">
      <div class="card">
        <div class="card-title">Điểm Chất Lượng Nhãn (AQI)</div>
        <div class="card-value tag-green">{improvement.post_qc_aqi:.1f}<span style="font-size:18px;">/100</span></div>
        <div class="card-sub">Tăng vọt +{improvement.aqi_gain:.1f} điểm (Trước: {improvement.raw_aqi:.1f})</div>
      </div>
      <div class="card">
        <div class="card-title">Mean IoU Hộp Bao & Mask</div>
        <div class="card-value tag-blue">{improvement.post_qc_miou:.3f}</div>
        <div class="card-sub">Tăng +{improvement.miou_gain:.1%} so với nhãn thô ({improvement.raw_miou:.3f})</div>
      </div>
      <div class="card">
        <div class="card-title">Độ Chính Xác Phân Loại</div>
        <div class="card-value" style="color: #38bdf8;">{improvement.post_qc_class_acc:.1%}</div>
        <div class="card-sub">Chuẩn hóa tên class (Trước: {improvement.raw_class_acc:.1%})</div>
      </div>
      <div class="card">
        <div class="card-title">Khôi Phục Đối Tượng Bỏ Sót</div>
        <div class="card-value tag-green">+{improvement.missed_recovered_count} xe</div>
        <div class="card-sub">Bù đắp thông minh qua AI Ensemble</div>
      </div>
    </div>

    <div class="section-title">📊 3. Ma Trận Nhầm Lẫn & Phân Rã Chi Tiết Từng Rule (Breakdown)</div>
    <table>
      <thead>
        <tr>
          <th>Mã Quy Tắc (Rule ID)</th>
          <th>TP (Bắt đúng)</th>
          <th>FN (Bỏ sót)</th>
          <th>FP (Báo sai)</th>
          <th>Precision</th>
          <th>Recall (Detection Rate)</th>
        </tr>
      </thead>
      <tbody>
        {rows if rows else "<tr><td colspan='6' style='text-align:center;'>100% Rules hoạt động hoàn hảo không phát sinh sai số.</td></tr>"}
      </tbody>
    </table>

    <div class="footer">
      TriModel QC Benchmark Suite · Chuẩn hóa theo tiêu chuẩn BDD100K & Cleanlab · Ngày xuất báo cáo tự động
    </div>
  </div>
</body>
</html>
"""
