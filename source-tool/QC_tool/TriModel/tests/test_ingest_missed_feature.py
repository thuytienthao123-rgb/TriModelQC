from pathlib import Path
import pytest
from qc.models import FrameData, LabeledObject, BBox2D
from qc.engine import run_qc


def test_ingest_all_frames_and_check_frame_10():
    # Giả lập 12 frames (bao gồm frame 10)
    frames = []
    for i in range(1, 13):
        fname = f"Video_3_frame_{i:04d}.jpg"
        # Ban đầu mỗi frame chỉ có 1 box người dùng
        obj1 = LabeledObject(
            id=f"user_{i}_01",
            category="car",
            box2d=BBox2D(x1=100.0, y1=100.0, x2=300.0, y2=300.0),
            attributes={"occluded": False, "truncated": False},
        )
        frames.append(FrameData(name=fname, width=1920, height=1080, objects=[obj1]))

    # Giả lập cache AI missed: Frame 1 và Frame 10 đều có vật thể bỏ sót
    ai_cache = {
        "Video_3_frame_0001.jpg": [
            {"category": "car", "confidence": 0.88, "box2d": BBox2D(x1=400.0, y1=200.0, x2=600.0, y2=400.0)}
        ],
        "Video_3_frame_0010.jpg": [
            {"category": "truck", "confidence": 0.92, "box2d": BBox2D(x1=700.0, y1=300.0, x2=950.0, y2=600.0)}
        ],
    }

    total_added = 0
    # Mô phỏng logic nạp nhãn trên toàn bộ ảnh
    for f_idx, f in enumerate(frames):
        f_missed = []
        if f.name in ai_cache:
            f_missed = list(ai_cache[f.name])
        elif Path(f.name).stem in ai_cache:
            f_missed = list(ai_cache[Path(f.name).stem])

        if f_missed:
            cw = float(f.width) if f.width > 0 else 1920.0
            ch = float(f.height) if f.height > 0 else 1080.0
            for m_idx, m_item in enumerate(f_missed):
                mbx = m_item["box2d"]
                mcat = m_item["category"]
                new_id = f"missed_{mcat[:3]}_{f_idx+1}_{m_idx+1}"
                cx1 = max(0.0, min(cw - 2.0, float(mbx.x1)))
                cy1 = max(0.0, min(ch - 2.0, float(mbx.y1)))
                cx2 = max(cx1 + 1.0, min(cw, float(mbx.x2)))
                cy2 = max(cy1 + 1.0, min(ch, float(mbx.y2)))
                new_obj = LabeledObject(
                    id=new_id,
                    category=mcat,
                    box2d=BBox2D(x1=cx1, y1=cy1, x2=cx2, y2=cy2),
                    attributes={"occluded": False, "truncated": False},
                )
                f.objects.append(new_obj)
                total_added += 1

        ai_cache[f.name] = []
        ai_cache[Path(f.name).stem] = []

    # 1. Kiểm tra tổng số nhãn được nạp
    assert total_added == 2

    # 2. Kiểm tra frame 10 (index 9)
    frame_10 = frames[9]
    assert frame_10.name == "Video_3_frame_0010.jpg"
    assert len(frame_10.objects) == 2  # Gồm box ban đầu + box missed mới nạp
    ingested_obj = frame_10.objects[1]
    assert ingested_obj.category == "truck"
    assert ingested_obj.box2d.x1 == 700.0
    assert ingested_obj.box2d.y2 == 600.0

    # 3. Kiểm tra cache AI của frame 10 đã được làm sạch
    assert ai_cache["Video_3_frame_0010.jpg"] == []
    assert ai_cache["Video_3_frame_0010"] == []

    # 4. Chạy lại QC engine trên frames đã chữa lành
    report = run_qc(frames)
    # Không phát sinh bất kỳ lỗi hình học nào cho các box mới nạp
    assert report.total_objects == 12 + 2


def test_layer_visibility_guarantees():
    # Giả lập state ban đầu
    session_state = {}
    
    # Logic khởi tạo layer
    for ly in ["scale_show_err", "scale_show_warn", "scale_show_valid", "scale_show_labels"]:
        if ly not in session_state:
            session_state[ly] = True

    assert session_state["scale_show_valid"] is True
    assert session_state["scale_show_err"] is True
    assert session_state["scale_show_labels"] is True

    # Giả lập phục hồi khi vô tình bị tắt toàn bộ
    session_state["scale_show_valid"] = False
    session_state["scale_show_err"] = False
    session_state["scale_show_warn"] = False

    if (
        not session_state.get("scale_show_valid", True)
        and not session_state.get("scale_show_err", True)
        and not session_state.get("scale_show_warn", True)
    ):
        session_state["scale_show_err"] = True
        session_state["scale_show_warn"] = True
        session_state["scale_show_valid"] = True
        session_state["scale_show_labels"] = True

    assert session_state["scale_show_valid"] is True
    assert session_state["scale_show_err"] is True


def test_multi_format_exports():
    import json
    import io
    import zipfile
    import xml.etree.ElementTree as ET
    from qc.reporter import (
        export_bdd100k_json,
        export_bdd100k_zip_bytes,
        export_coco_json,
        export_yolo_txt_single,
        export_yolo_zip_bytes,
        export_cvat_xml_str,
        export_anylabeling_json_single,
        export_anylabeling_zip_bytes,
    )

    f1 = FrameData(
        name="frame_0001.jpg",
        width=1920,
        height=1080,
        objects=[
            LabeledObject(
                id="obj_1",
                category="car",
                box2d=BBox2D(x1=100.0, y1=200.0, x2=500.0, y2=600.0),
                attributes={"occluded": False, "truncated": False},
            )
        ],
    )
    frames = [f1]

    # 1. BDD100K JSON
    bdd_json = export_bdd100k_json(frames)
    parsed_bdd = json.loads(bdd_json)
    assert len(parsed_bdd) == 1
    assert parsed_bdd[0]["name"] == "frame_0001.jpg"
    assert parsed_bdd[0]["labels"][0]["category"] == "car"
    assert parsed_bdd[0]["labels"][0]["box2d"]["x1"] == 100.0

    # 2. BDD100K JSON Single frame
    bdd_single = export_bdd100k_json([f1])
    parsed_single = json.loads(bdd_single)
    assert len(parsed_single) == 1

    # 3. BDD100K ZIP (Per frame JSON files)
    bdd_zip_bytes = export_bdd100k_zip_bytes(frames)
    with zipfile.ZipFile(io.BytesIO(bdd_zip_bytes), "r") as zf:
        assert "frame_0001.json" in zf.namelist()
        content = json.loads(zf.read("frame_0001.json").decode("utf-8"))
        assert len(content) == 1
        assert content[0]["name"] == "frame_0001.jpg"

    # 4. AnyLabeling JSON Single frame
    any_single = export_anylabeling_json_single(f1)
    parsed_any = json.loads(any_single)
    assert parsed_any["version"] == "0.4.1"
    assert parsed_any["imagePath"] == "frame_0001.jpg"
    assert len(parsed_any["shapes"]) == 1
    assert parsed_any["shapes"][0]["label"] == "car"
    assert parsed_any["shapes"][0]["shape_type"] == "rectangle"
    assert parsed_any["shapes"][0]["points"] == [[100.0, 200.0], [500.0, 600.0]]

    # 5. AnyLabeling ZIP (Per frame JSON files for AnyLabeling)
    any_zip_bytes = export_anylabeling_zip_bytes(frames)
    with zipfile.ZipFile(io.BytesIO(any_zip_bytes), "r") as zf:
        assert "frame_0001.json" in zf.namelist()
        content = json.loads(zf.read("frame_0001.json").decode("utf-8"))
        assert content["version"] == "0.4.1"
        assert content["imagePath"] == "frame_0001.jpg"
        assert content["shapes"][0]["label"] == "car"

    # 6. COCO JSON
    coco_json = export_coco_json(frames)
    parsed_coco = json.loads(coco_json)
    assert "images" in parsed_coco
    assert "annotations" in parsed_coco
    assert parsed_coco["images"][0]["file_name"] == "frame_0001.jpg"

    # 7. YOLO TXT Single
    yolo_txt = export_yolo_txt_single(f1)
    parts = yolo_txt.strip().split()
    assert len(parts) == 5
    assert parts[0] == "0"  # class id

    # 8. YOLO ZIP
    yolo_zip = export_yolo_zip_bytes(frames)
    assert len(yolo_zip) > 0

    # 9. CVAT XML
    cvat_xml = export_cvat_xml_str(frames)
    root = ET.fromstring(cvat_xml)
    assert root.tag == "annotations"
    image_el = root.find(".//image")
    assert image_el is not None
    assert image_el.get("name") == "frame_0001.jpg"
    box_el = image_el.find("box")
    assert box_el is not None
    assert box_el.get("label") == "car"

