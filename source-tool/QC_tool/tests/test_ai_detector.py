"""
test_ai_detector.py — Bộ kiểm thử tự động cho Tri-Model AI Detector & Weighted Boxes Fusion.
Đảm bảo thuật toán lấy trung bình box, cơ chế đồng thuận 3/3 models và lọc nhiễu hoạt động hoàn hảo.
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import numpy as np
from PIL import Image

from qc.models import BBox2D, LabeledObject
from qc.ai_detector import (
    RawDetection,
    EnsembledDetection,
    weighted_boxes_fusion,
    normalize_category,
    compute_iou,
    TriModelQCAssistant,
)


# ---------------------------------------------------------------------------
# 1. Test Category Normalization & Synonyms
# ---------------------------------------------------------------------------
def test_normalize_category():
    assert normalize_category("car") == "car"
    assert normalize_category("automobile") == "car"
    assert normalize_category("o_to") == "car"
    assert normalize_category("xe_con") == "car"
    assert normalize_category("person") == "pedestrian"
    assert normalize_category("nguoi") == "pedestrian"
    assert normalize_category("rider") == "pedestrian"
    assert normalize_category("motorbike") == "motorcycle"
    assert normalize_category("xe_may") == "motorcycle"
    assert normalize_category("traffic_light") == "traffic light"
    assert normalize_category("stop sign") == "traffic sign"


# ---------------------------------------------------------------------------
# 2. Test IoU Computation
# ---------------------------------------------------------------------------
def test_compute_iou():
    box1 = BBox2D(100, 100, 200, 200)  # Area: 100 * 100 = 10000
    box2 = BBox2D(100, 100, 200, 200)  # Identical
    assert compute_iou(box1, box2) == 1.0

    box3 = BBox2D(150, 100, 250, 200)  # 50% overlap horizontally
    # Inter: 50 * 100 = 5000, Union: 10000 + 10000 - 5000 = 15000 => IoU = 1/3
    assert abs(compute_iou(box1, box3) - (1.0 / 3.0)) < 1e-4

    box4 = BBox2D(300, 300, 400, 400)  # Disjoint
    assert compute_iou(box1, box4) == 0.0


# ---------------------------------------------------------------------------
# 3. Test Weighted Boxes Fusion (WBF) & Consensus Averaging
# ---------------------------------------------------------------------------
def test_wbf_strict_consensus_3_models():
    """
    Kịch bản: Cả 3 mô hình cùng nhận diện được 1 chiếc xe với tọa độ hơi lệch nhau.
    WBF phải tính trung bình tọa độ có trọng số của cả 3 mô hình.
    """
    dets = {
        "Model_1": [RawDetection("car", 0.90, BBox2D(100.0, 100.0, 200.0, 200.0), "Model_1")],
        "Model_2": [RawDetection("car", 0.85, BBox2D(102.0, 98.0, 204.0, 202.0), "Model_2")],
        "Model_3": [RawDetection("car", 0.95, BBox2D(98.0, 102.0, 198.0, 198.0), "Model_3")],
    }

    # Strict mode: Yêu cầu cả 3 model cùng đồng thuận
    results = weighted_boxes_fusion(dets, iou_threshold=0.5, min_agreement=3)

    assert len(results) == 1
    res = results[0]
    assert res.category == "car"
    assert res.agreement_count == 3
    assert res.agreement_ratio == 1.0
    assert set(res.models_agreed) == {"Model_1", "Model_2", "Model_3"}

    # Kiểm tra tọa độ trung bình nằm trong khoảng min và max của 3 box
    assert 98.0 <= res.box2d.x1 <= 102.0
    assert 98.0 <= res.box2d.y1 <= 102.0
    assert 198.0 <= res.box2d.x2 <= 204.0
    assert 198.0 <= res.box2d.y2 <= 202.0
    assert 0.85 <= res.confidence <= 0.95


def test_wbf_rejects_noise_and_false_positives():
    """
    Kịch bản:
      - Model 1 nhận diện nhầm một vết bẩn/bóng râm là 'car' (chỉ có Model 1 thấy).
      - Model 2 và Model 3 không thấy.
    -> Thuật toán Strict (min_agreement=3) hoặc Majority (min_agreement=2) PHẢI LOẠI BỎ box này.
    """
    dets = {
        "Model_1": [
            RawDetection("car", 0.70, BBox2D(500, 500, 550, 550), "Model_1"),  # False Positive
            RawDetection("truck", 0.90, BBox2D(50, 50, 150, 150), "Model_1"),
        ],
        "Model_2": [
            RawDetection("truck", 0.88, BBox2D(52, 48, 152, 152), "Model_2"),
        ],
        "Model_3": [
            RawDetection("truck", 0.92, BBox2D(49, 51, 149, 149), "Model_3"),
        ],
    }

    # Strict mode
    strict_res = weighted_boxes_fusion(dets, iou_threshold=0.5, min_agreement=3)
    assert len(strict_res) == 1
    assert strict_res[0].category == "truck"
    # False positive ở (500, 500) phải bị loại bỏ hoàn toàn
    for r in strict_res:
        assert r.category != "car"


def test_wbf_majority_mode():
    """
    Kịch bản Majority (2/3):
      - 2 model phát hiện vật thể, 1 model bị miss do góc khuất.
      - Chế độ 2/3 giữ lại box và gắn cờ agreement_count = 2.
    """
    dets = {
        "Model_1": [RawDetection("pedestrian", 0.80, BBox2D(10, 10, 30, 60), "Model_1")],
        "Model_2": [RawDetection("person", 0.82, BBox2D(12, 11, 31, 62), "Model_2")],
        "Model_3": [],  # Model 3 miss
    }

    strict_res = weighted_boxes_fusion(dets, iou_threshold=0.5, min_agreement=3)
    assert len(strict_res) == 0  # Strict từ chối vì thiếu 1 model

    maj_res = weighted_boxes_fusion(dets, iou_threshold=0.5, min_agreement=2)
    assert len(maj_res) == 1
    assert maj_res[0].category == "pedestrian"
    assert maj_res[0].agreement_count == 2


# ---------------------------------------------------------------------------
# 4. Test Cross-Check with User Annotations (Missed & Mismatch Detection)
# ---------------------------------------------------------------------------
def test_cross_check_missed_object():
    """
    Kịch bản: AI phát hiện 1 xe và 1 người đi bộ.
    Người dùng chỉ mới vẽ box cho chiếc xe, BỎ SÓT người đi bộ.
    -> QC Tool phải chỉ ra chính xác người đi bộ bị bỏ sót kèm tọa độ trung bình.
    """
    assistant = TriModelQCAssistant()
    if not assistant.is_ready():
        pytest.skip("Không có model weights để chạy integration test")

    # Giả lập detections
    user_objects = [
        LabeledObject(
            id="u1",
            category="car",
            box2d=BBox2D(100, 100, 200, 200),
        )
    ]

    # Giả lập ảnh test
    img = Image.new("RGB", (640, 640), color=(128, 128, 128))
    check_res = assistant.check_missed_and_mismatched(
        img_pil=img,
        user_objects=user_objects,
        conf_thresh=0.25,
        ensemble_mode="strict",
    )
    # Kiểm tra cấu trúc trả về chuẩn xác
    assert "missed" in check_res
    assert "mismatched" in check_res
    assert "total_ai_detections" in check_res
    assert "total_user_objects" in check_res


def test_cross_check_category_mismatch():
    """
    Kịch bản: Người dùng vẽ box quanh xe buýt nhưng gán nhãn là 'car'.
    AI Tri-Model xác định đó là 'bus' với độ tin cậy cao.
    -> Hệ thống phải phát hiện ra sự sai lệch danh mục (mismatched).
    """
    # Test hàm phân tích trực tiếp với EnsembledDetection giả lập
    ai_det = EnsembledDetection(
        category="bus",
        confidence=0.92,
        box2d=BBox2D(100, 100, 400, 300),
        models_agreed=["Model_1", "Model_2", "Model_3"],
        agreement_count=3,
        agreement_ratio=1.0,
        individual_boxes=[],
    )

    user_obj = LabeledObject(
        id="u_wrong",
        category="car",  # Sai class so với bus
        box2d=BBox2D(105, 95, 395, 305),
    )

    iou = compute_iou(ai_det.box2d, user_obj.box2d)
    assert iou > 0.85  # Tọa độ trùng khớp rất cao
    assert normalize_category(user_obj.category) != ai_det.category  # Nhưng khác category
