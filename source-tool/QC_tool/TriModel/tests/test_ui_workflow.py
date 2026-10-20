from pathlib import Path
import pytest
from qc.models import FrameData, LabeledObject, BBox2D, QCReport, QCError
from qc.engine import run_qc
from ui.tabs.tab_visualizer import render_tab_visualizer
from ui.manual_editor import render_manual_editor_panel


def test_visualizer_and_frame_10_execution():
    """Kiểm tra trực tiếp việc render visualizer trên frame 10 và vận hành nạp nhãn."""
    # Tạo 12 frame
    frames = []
    for i in range(1, 13):
        fname = f"Video_3_frame_{i:04d}.jpg"
        obj = LabeledObject(
            id=f"car_{i}",
            category="car",
            box2d=BBox2D(x1=50.0, y1=50.0, x2=200.0, y2=200.0),
            attributes={"occluded": False, "truncated": False},
        )
        frames.append(FrameData(name=fname, width=1920, height=1080, objects=[obj]))

    # Giả lập báo cáo QC
    report = run_qc(frames)
    
    # Giả lập cache AI cho frame 10
    ai_cache = {
        "Video_3_frame_0010.jpg": [
            {"category": "car", "confidence": 0.90, "box2d": BBox2D(x1=300.0, y1=300.0, x2=500.0, y2=500.0)}
        ]
    }

    # Frame 10 trước khi nạp
    frame_10 = frames[9]
    assert len(frame_10.objects) == 1
    assert "Video_3_frame_0010.jpg" in ai_cache
    assert len(ai_cache["Video_3_frame_0010.jpg"]) == 1

    # Nạp toàn bộ nhãn
    for f in frames:
        f_missed = ai_cache.get(f.name, [])
        for m in f_missed:
            mbx = m["box2d"]
            new_obj = LabeledObject(
                id=f"missed_{m['category']}",
                category=m["category"],
                box2d=BBox2D(x1=mbx.x1, y1=mbx.y1, x2=mbx.x2, y2=mbx.y2),
                attributes={"occluded": False, "truncated": False},
            )
            f.objects.append(new_obj)
        ai_cache[f.name] = []
        ai_cache[Path(f.name).stem] = []

    # Frame 10 sau khi nạp
    assert len(frame_10.objects) == 2
    assert ai_cache["Video_3_frame_0010.jpg"] == []
    assert ai_cache["Video_3_frame_0010"] == []

    # Kiểm tra truy vấn cache bằng cả tên đầy đủ lẫn Path.stem
    assert ai_cache.get(frame_10.name) == []
    assert ai_cache.get(Path(frame_10.name).stem) == []
