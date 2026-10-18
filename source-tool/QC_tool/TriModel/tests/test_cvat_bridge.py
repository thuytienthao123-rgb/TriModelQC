import json
import pytest
from unittest.mock import MagicMock
import urllib.request
import numpy as np

from qc.models import FrameData, LabeledObject, BBox2D, Polygon2D, QCReport, QCError
from ui.cvat_bridge import CVATBridge, create_cvat_mock_session
from ui.manual_editor import auto_generate_polygon_for_object


def test_cvat_mock_session_creation():
    frames, meta = create_cvat_mock_session()
    assert len(frames) == 2
    assert meta["job_id"] == 88
    assert meta["mode"] == "offline_mock"
    assert len(frames[0].objects) >= 3
    # Check polygon exists
    assert any(o.poly2d is not None for o in frames[0].objects)


def test_auto_generate_polygon():
    # Create synthetic test image with a circle
    img = np.zeros((400, 400, 3), dtype=np.uint8)
    import cv2
    cv2.circle(img, (200, 200), 50, (255, 255, 255), -1)

    box = BBox2D(140.0, 140.0, 260.0, 260.0)
    poly = auto_generate_polygon_for_object(img, box)
    assert poly is not None
    assert len(poly.vertices) >= 3
    # Check bounding box is reasonable
    poly_box = poly.bounding_box()
    assert poly_box is not None
    assert poly_box.x1 >= 130.0 and poly_box.x2 <= 270.0


def test_cvat_bridge_fetch_and_push_mocked(monkeypatch):
    bridge = CVATBridge("https://app.cvat.ai", "fake_token_123")

    def mock_urlopen(req, *args, **kwargs):
        url = req.full_url
        method = req.get_method()

        resp = MagicMock()
        resp.status = 200
        if "/api/jobs/88/annotations" in url and method == "GET":
            data = {
                "shapes": [
                    {
                        "id": 1,
                        "type": "rectangle",
                        "frame": 0,
                        "label_id": 1,
                        "points": [10.0, 20.0, 80.0, 90.0],
                        "attributes": [{"name": "occluded", "value": "false"}]
                    }
                ]
            }
        elif "/api/jobs/88" in url and method == "GET":
            data = {"id": 88, "task_id": 10}
        elif "/api/tasks/10" in url and method == "GET":
            data = {"labels": [{"id": 1, "name": "car"}]}
        elif method in ("PUT", "PATCH"):
            data = {"message": "updated"}
        else:
            data = {}

        resp.read.return_value = json.dumps(data).encode("utf-8")
        resp.__enter__.return_value = resp
        return resp

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    ok, frames, meta = bridge.fetch_job_as_frames(88)
    assert ok is True
    assert len(frames) == 1
    assert frames[0].objects[0].category == "car"
    assert frames[0].objects[0].box2d.x1 == 10.0

    # Test push back
    ok_push, push_res = bridge.push_healed_annotations_to_job(88, frames, {"car": 1})
    assert ok_push is True
    assert push_res["count"] == 1

    # Test push issues
    rep = QCReport()
    rep.add(QCError("RULE_B01", "ERROR", "cvat_job88_frame_0000.jpg", "obj_1", "car", "Out of bounds"))
    ok_issues, issues_res = bridge.push_issues_to_cvat(88, rep)
    assert ok_issues is True
    assert "Đã gắn thành công" in issues_res


def test_auto_generate_polygon_fallback_no_image():
    # Zero-setup fallback when loaded_img is None
    box = BBox2D(100.0, 100.0, 200.0, 200.0)
    poly = auto_generate_polygon_for_object(None, box)
    assert poly is not None
    assert len(poly.vertices) == 8  # Smooth Octagon fallback
    p_box = poly.bounding_box()
    assert p_box is not None
    assert abs(p_box.x1 - 100.0) < 1e-3
    assert abs(p_box.x2 - 200.0) < 1e-3
