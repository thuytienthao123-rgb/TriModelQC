"""Regression tests for import paths used by the Streamlit UI and extra formats."""

from __future__ import annotations

from PIL import Image

from qc.ai_detector import get_tri_model_detector
from qc.models import BBox2D, LabeledObject
from qc.parser import parse_bdd100k_data, parse_cvat_xml_text, parse_yolo_text
from ui.ai_assistant import detect_ai_issues, detect_missed_objects
from ui.io_utils import read_file_bytes, scan_folder


def test_yolo_polygon_parses_without_unsupported_dataclass_fields():
    frame = parse_yolo_text(
        "0 0.10 0.10 0.40 0.10 0.40 0.50 0.10 0.50",
        frame_name="polygon.jpg",
        width=1000,
        height=500,
        class_names=["car"],
    )

    assert len(frame.objects) == 1
    assert frame.objects[0].poly2d is not None
    assert frame.objects[0].box2d == BBox2D(100.0, 50.0, 400.0, 250.0)


def test_bdd_parser_skips_objects_without_geometry():
    frames = parse_bdd100k_data([
        {
            "name": "frame.jpg",
            "labels": [
                {"id": "garbage", "category": "car", "attributes": {}},
                {
                    "id": "valid",
                    "category": "car",
                    "box2d": {"x1": 1, "y1": 2, "x2": 10, "y2": 20},
                },
            ],
        }
    ])

    assert [obj.id for obj in frames[0].objects] == ["valid"]


def test_cvat_image_xml_parses_boxes_polygons_and_attributes():
    xml = """
    <annotations>
      <image id="0" name="road.jpg" width="1920" height="1080">
        <box id="11" label="car" xtl="10" ytl="20" xbr="110" ybr="120" occluded="1">
          <attribute name="truncated">true</attribute>
        </box>
        <polygon id="12" label="lane" points="1,2;10,2;10,20;1,20" />
      </image>
    </annotations>
    """

    frames = parse_cvat_xml_text(xml)

    assert len(frames) == 1
    assert frames[0].name == "road.jpg"
    assert frames[0].objects[0].attributes == {"truncated": True, "occluded": True}
    assert frames[0].objects[1].poly2d is not None
    assert frames[0].objects[1].box2d == BBox2D(1.0, 2.0, 10.0, 20.0)


def test_cvat_video_track_xml_parses_visible_shapes():
    xml = """
    <annotations>
      <meta><task><original_size><width>1280</width><height>720</height></original_size></task></meta>
      <track id="7" label="bus">
        <box frame="3" outside="0" xtl="10" ytl="20" xbr="50" ybr="80" />
        <box frame="4" outside="1" xtl="11" ytl="21" xbr="51" ybr="81" />
      </track>
    </annotations>
    """

    frames = parse_cvat_xml_text(xml)

    assert len(frames) == 1
    assert frames[0].name == "frame_000003.jpg"
    assert frames[0].width == 1280
    assert len(frames[0].objects) == 1


def test_xml_upload_and_folder_scan_use_real_cvat_parser(tmp_path):
    xml = (
        '<annotations><image id="0" name="road.jpg" width="100" height="80">'
        '<box label="car" xtl="1" ytl="2" xbr="30" ybr="40" />'
        "</image></annotations>"
    )
    xml_path = tmp_path / "annotations.xml"
    xml_path.write_text(xml, encoding="utf-8")

    uploaded = read_file_bytes(xml.encode("utf-8"), "annotations.xml")
    scanned, _ = scan_folder(str(tmp_path))

    assert uploaded is not None and uploaded[0].objects[0].category == "car"
    assert scanned[0][0] == "annotations.xml"


def test_ai_ui_forwards_selected_ensemble_mode():
    class FakeTriModel:
        def __init__(self):
            self.received = None

        def detect_missed_and_mismatched(self, image, objects, **kwargs):
            self.received = kwargs
            return {"missed": [{"category": "car"}], "mismatched": []}

    fake = FakeTriModel()
    missed = detect_missed_objects(
        Image.new("RGB", (10, 10)),
        [LabeledObject("1", "car", box2d=BBox2D(1, 1, 2, 2))],
        fake,
        conf_thresh=0.4,
        ensemble_mode="strict",
    )

    assert missed == [{"category": "car"}]
    assert fake.received == {"conf_thresh": 0.4, "ensemble_mode": "strict"}

    issues = detect_ai_issues(
        Image.new("RGB", (10, 10)),
        [],
        fake,
        conf_thresh=0.5,
        ensemble_mode="majority",
    )
    assert issues["missed"] == [{"category": "car"}]
    assert fake.received == {"conf_thresh": 0.5, "ensemble_mode": "majority"}


def test_tri_model_factory_is_public():
    assert callable(get_tri_model_detector)
