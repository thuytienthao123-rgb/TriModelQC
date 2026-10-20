"""
tests/test_benchmark.py — Unit test cho bộ benchmark và đo lường độ chính xác QC.
"""

import pytest
from qc.models import FrameData, LabeledObject, BBox2D
from qc.benchmark import (
    inject_honeypot_defects,
    evaluate_qc_detection_accuracy,
    evaluate_quality_improvement,
)
from qc.engine import run_qc


@pytest.fixture
def clean_gt_fixture():
    f1 = FrameData(
        name="frame_01.jpg",
        width=1280,
        height=720,
        objects=[
            LabeledObject("c1", "car", BBox2D(100, 100, 300, 300), attributes={"occluded": False, "truncated": False}),
            LabeledObject("p1", "pedestrian", BBox2D(400, 200, 450, 350), attributes={"occluded": False, "truncated": False}),
            LabeledObject("t1", "truck", BBox2D(600, 150, 900, 400), attributes={"occluded": False, "truncated": False}),
            LabeledObject("b1", "bus", BBox2D(950, 200, 1200, 450), attributes={"occluded": False, "truncated": False}),
        ]
    )
    return [f1]


def test_inject_honeypot_defects(clean_gt_fixture):
    corrupted, defect_map, manifest = inject_honeypot_defects(clean_gt_fixture, defect_rate=0.50, seed=123)
    assert len(corrupted) == 1
    assert len(manifest) > 0
    assert len(defect_map) > 0


def test_evaluate_qc_detection_accuracy(clean_gt_fixture):
    corrupted, defect_map, _ = inject_honeypot_defects(clean_gt_fixture, defect_rate=0.50, seed=42)
    report = run_qc(corrupted)
    metrics = evaluate_qc_detection_accuracy(corrupted, report, defect_map)
    assert metrics.total_evaluated_objects > 0
    assert 0.0 <= metrics.precision <= 1.0
    assert 0.0 <= metrics.recall <= 1.0
    assert 0.0 <= metrics.f1_score <= 1.0


def test_evaluate_quality_improvement(clean_gt_fixture):
    corrupted, _, _ = inject_honeypot_defects(clean_gt_fixture, defect_rate=0.50, seed=42)
    improvement = evaluate_quality_improvement(clean_gt_fixture, corrupted)
    assert improvement.total_frames == 1
    assert improvement.post_qc_miou >= improvement.raw_miou
    assert improvement.post_qc_aqi >= improvement.raw_aqi
