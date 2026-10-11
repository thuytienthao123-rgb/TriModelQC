"""
tests/test_rules.py — Unit test cho toàn bộ 10 Rules của BDD-QC Tool.
Chạy: python -m pytest tests/test_rules.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from qc.models import BBox2D, FrameData, LabeledObject, Polygon2D
from qc.rules.bbox_rules import RuleB01OutOfBounds, RuleB02InvertedOrZero, RuleB03TooSmall, RuleB04AbnormalRatio
from qc.rules.polygon_rules import RuleP01InsufficientVertices, RuleP02SelfIntersection, RuleP03MaskBoxMismatch
from qc.rules.attribute_rules import RuleA01DuplicateObject, RuleA02MissingAttributes, RuleA03TrafficLightColor
from qc.engine import run_qc
from qc.parser import load_bdd100k


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_frame(*objects, name="test_frame.jpg", w=1280, h=720):
    return FrameData(name=name, width=w, height=h, objects=list(objects))

def make_obj(id_, cat, x1=100, y1=100, x2=300, y2=250, attrs=None, poly=None):
    return LabeledObject(
        id=id_, category=cat,
        box2d=BBox2D(x1, y1, x2, y2),
        poly2d=poly,
        attributes=attrs or {"occluded": False, "truncated": False},
    )


# ===========================================================================
# RULE B01: Out of Bounds
# ===========================================================================

class TestRuleB01:
    rule = RuleB01OutOfBounds()

    def test_valid_box(self):
        obj = make_obj("ok", "car")
        frame = make_frame(obj)
        assert self.rule.check(frame) == []

    def test_x1_negative(self):
        obj = make_obj("err", "car", x1=-10)
        frame = make_frame(obj)
        errs = self.rule.check(frame)
        assert len(errs) == 1
        assert errs[0].rule_id == "RULE_B01"

    def test_x2_exceeds_width(self):
        obj = make_obj("err", "car", x2=1300)
        frame = make_frame(obj)
        errs = self.rule.check(frame)
        assert len(errs) == 1

    def test_y2_exceeds_height(self):
        obj = make_obj("err", "car", y2=800)
        frame = make_frame(obj)
        errs = self.rule.check(frame)
        assert len(errs) == 1

    def test_multiple_violations_one_obj(self):
        obj = make_obj("err", "car", x1=-5, y2=800)
        frame = make_frame(obj)
        # Cả hai vi phạm nhưng chỉ tạo 1 QCError (1 lần gọi rule)
        errs = self.rule.check(frame)
        assert len(errs) == 1


# ===========================================================================
# RULE B02: Inverted / Zero
# ===========================================================================

class TestRuleB02:
    rule = RuleB02InvertedOrZero()

    def test_normal(self):
        obj = make_obj("ok", "car")
        assert self.rule.check(make_frame(obj)) == []

    def test_zero_width(self):
        obj = make_obj("z", "car", x1=200, x2=200)
        errs = self.rule.check(make_frame(obj))
        assert len(errs) == 1 and errs[0].rule_id == "RULE_B02"

    def test_inverted(self):
        obj = make_obj("inv", "car", x1=300, x2=100)
        errs = self.rule.check(make_frame(obj))
        assert len(errs) == 1


# ===========================================================================
# RULE B03: Too Small
# ===========================================================================

class TestRuleB03:
    rule = RuleB03TooSmall()

    def test_normal_size(self):
        obj = make_obj("ok", "car")
        assert self.rule.check(make_frame(obj)) == []

    def test_tiny_box(self):
        obj = make_obj("tiny", "pedestrian", x1=100, y1=100, x2=104, y2=104)  # 16 px²
        errs = self.rule.check(make_frame(obj))
        assert len(errs) == 1 and errs[0].rule_id == "RULE_B03"

    def test_exactly_threshold(self):
        # 8×8 = 64px² — đúng ngưỡng, không báo lỗi
        obj = make_obj("thresh", "car", x1=100, y1=100, x2=108, y2=108)
        assert self.rule.check(make_frame(obj)) == []


# ===========================================================================
# RULE B04: Abnormal Ratio
# ===========================================================================

class TestRuleB04:
    rule = RuleB04AbnormalRatio()

    def test_normal_ratio(self):
        obj = make_obj("ok", "car")
        assert self.rule.check(make_frame(obj)) == []

    def test_extreme_ratio(self):
        obj = make_obj("wide", "car", x1=0, y1=100, x2=1000, y2=101)  # ratio 1000:1
        errs = self.rule.check(make_frame(obj))
        assert len(errs) == 1 and errs[0].rule_id == "RULE_B04"

    def test_barrier_exempt(self):
        obj = make_obj("bar", "barrier", x1=0, y1=100, x2=1000, y2=101)
        assert self.rule.check(make_frame(obj)) == []


# ===========================================================================
# RULE P01: Insufficient Vertices
# ===========================================================================

class TestRuleP01:
    rule = RuleP01InsufficientVertices()

    def test_valid_polygon(self):
        poly = Polygon2D([(0,0),(100,0),(50,100)])
        obj = LabeledObject("p", "lane", poly2d=poly, attributes={})
        assert self.rule.check(make_frame(obj)) == []

    def test_only_two_vertices(self):
        poly = Polygon2D([(0,0),(100,0)])
        obj = LabeledObject("p", "lane", poly2d=poly, attributes={})
        errs = self.rule.check(make_frame(obj))
        assert len(errs) == 1 and errs[0].rule_id == "RULE_P01"


# ===========================================================================
# RULE P02: Self-Intersection
# ===========================================================================

class TestRuleP02:
    rule = RuleP02SelfIntersection()

    def test_valid_square(self):
        poly = Polygon2D([(0,0),(100,0),(100,100),(0,100)])
        obj = LabeledObject("p", "car", poly2d=poly, attributes={})
        assert self.rule.check(make_frame(obj)) == []

    def test_self_intersecting_butterfly(self):
        # Hình bướm: tự cắt viền
        poly = Polygon2D([(0,0),(100,100),(100,0),(0,100)])
        obj = LabeledObject("p", "car", poly2d=poly, attributes={})
        errs = self.rule.check(make_frame(obj))
        assert len(errs) == 1 and errs[0].rule_id == "RULE_P02"


# ===========================================================================
# RULE P03: Mask vs Box Mismatch
# ===========================================================================

class TestRuleP03:
    rule = RuleP03MaskBoxMismatch()

    def test_matching(self):
        poly = Polygon2D([(100,100),(300,100),(300,250),(100,250)])
        obj = LabeledObject("p","car", box2d=BBox2D(100,100,300,250), poly2d=poly, attributes={})
        assert self.rule.check(make_frame(obj)) == []

    def test_mismatching(self):
        poly = Polygon2D([(500,400),(700,400),(700,600),(500,600)])
        obj = LabeledObject("p","car", box2d=BBox2D(100,100,300,250), poly2d=poly, attributes={})
        errs = self.rule.check(make_frame(obj))
        assert len(errs) == 1 and errs[0].rule_id == "RULE_P03"


# ===========================================================================
# RULE A01: Duplicate
# ===========================================================================

class TestRuleA01:
    rule = RuleA01DuplicateObject()

    def test_no_duplicate(self):
        a = make_obj("a", "car", x1=0, y1=0, x2=200, y2=200)
        b = make_obj("b", "car", x1=600, y1=400, x2=800, y2=600)
        assert self.rule.check(make_frame(a, b)) == []

    def test_duplicate_same_class(self):
        a = make_obj("a", "bus", x1=100, y1=100, x2=400, y2=400)
        b = make_obj("b", "bus", x1=102, y1=102, x2=399, y2=399)
        errs = self.rule.check(make_frame(a, b))
        assert len(errs) == 1 and errs[0].rule_id == "RULE_A01"

    def test_overlap_different_class_ok(self):
        a = make_obj("a", "car", x1=100, y1=100, x2=400, y2=400)
        b = make_obj("b", "rider", x1=102, y1=102, x2=399, y2=399)
        assert self.rule.check(make_frame(a, b)) == []


# ===========================================================================
# RULE A02: Missing Attributes
# ===========================================================================

class TestRuleA02:
    rule = RuleA02MissingAttributes()

    def test_complete_attributes(self):
        obj = make_obj("ok", "car", attrs={"occluded": False, "truncated": False})
        assert self.rule.check(make_frame(obj)) == []

    def test_missing_occluded(self):
        obj = make_obj("m", "car", attrs={"truncated": False})
        errs = self.rule.check(make_frame(obj))
        assert len(errs) == 1 and errs[0].rule_id == "RULE_A02"

    def test_missing_both(self):
        obj = LabeledObject("m", "pedestrian", box2d=BBox2D(100,100,200,200), attributes={})
        errs = self.rule.check(make_frame(obj))
        assert len(errs) == 1  # 1 QCError tong hop, message liet ke ca hai truong bi thieu


# ===========================================================================
# RULE A03: Traffic Light Color
# ===========================================================================

class TestRuleA03:
    rule = RuleA03TrafficLightColor()

    def test_valid_color(self):
        obj = make_obj("tl", "traffic light", attrs={"occluded": False, "truncated": False, "trafficLightColor": "red"})
        assert self.rule.check(make_frame(obj)) == []

    def test_missing_color(self):
        obj = make_obj("tl", "traffic light", attrs={"occluded": False})
        errs = self.rule.check(make_frame(obj))
        assert len(errs) == 1 and errs[0].rule_id == "RULE_A03"

    def test_invalid_color(self):
        obj = make_obj("tl", "traffic light", attrs={"trafficLightColor": "blue"})
        errs = self.rule.check(make_frame(obj))
        assert len(errs) == 1 and "blue" in errs[0].message

    def test_non_traffic_light_ignored(self):
        obj = make_obj("car1", "car")
        assert self.rule.check(make_frame(obj)) == []


# ===========================================================================
# Integration test — engine + parser
# ===========================================================================

class TestIntegration:
    def test_engine_runs_all_rules(self):
        objs = [make_obj("ok", "car")]
        frames = [make_frame(*objs)]
        report = run_qc(frames)
        assert report.total_frames == 1
        assert report.total_objects == 1

    def test_parser_sample_file(self):
        sample = os.path.join(
            os.path.dirname(__file__), "..", "data_sample", "sample_with_errors.json"
        )
        frames = load_bdd100k(sample)
        assert len(frames) >= 1

    def test_full_pipeline_detects_errors(self):
        sample = os.path.join(
            os.path.dirname(__file__), "..", "data_sample", "sample_with_errors.json"
        )
        frames = load_bdd100k(sample)
        report = run_qc(frames)
        # File mẫu có nhiều lỗi giả lập — phải phát hiện ít nhất 1 lỗi ERROR
        assert report.error_count() >= 1


if __name__ == "__main__":
    import pytest as pt
    pt.main([__file__, "-v", "--tb=short"])
