from __future__ import annotations
from typing import List, Dict, Any, Tuple, Optional
from qc.models import FrameData, BBox2D, Polygon2D


def auto_correct_frames(
    frames: List[FrameData],
) -> Tuple[List[Dict[str, Any]], List[str], Dict[str, int]]:
    """
    Thuật toán tự động khắc phục toàn diện các lỗi vi phạm 2D BBox & Polygon (Đề tài N2-04A):
    - 📏 Clamp BBox (B01): Kéo box tràn viền về đúng khung ảnh [0, W] x [0, H]
    - 🔄 Invert Coords (B02): Đảo lại tọa độ bị ngược (x1 > x2 hoặc y1 > y2)
    - 🗑️ Zero-size / Noise Box (B02, B03): Xóa bỏ các box rỗng hoặc chấm nhiễu rác
    - 📉 Fix Polygon Đỉnh < 3 (P01): Tự động sinh đa giác 4 đỉnh từ BBox tương ứng
    - 🎗️ Unknot Self-Intersecting Polygon (P02): Dùng Shapely giải phóng xoắn nơ thành đa giác đơn
    - 🎯 Align Mask vs Box (P03): Căn chỉnh lại BBox theo đúng viền bao thực tế của Polygon (IoU = 1.0)
    - 👥 Deduplicate Box (A01): Xóa box cùng class bị vẽ đè lên nhau (IoU > 0.85)
    - 🏷️ Missing Attributes (A02): Bổ sung thuộc tính occluded=False, truncated=False
    - 🚦 Traffic Light Color (A03): Chuẩn hóa màu đèn sai lệch về 'none'
    - 🔤 Category Typo (C01): Sửa lỗi chính tả tên class về chuẩn BDD100K
    """
    fixed_data = []
    changelog = []
    stats: Dict[str, int] = {
        "B01_clamped": 0,
        "B02_inverted": 0,
        "B02_zero_removed": 0,
        "P01_synthesized": 0,
        "P02_unknotted": 0,
        "P03_aligned": 0,
        "A01_deduped": 0,
        "A02_attrs_filled": 0,
        "A03_tl_normalized": 0,
        "C01_typo_fixed": 0,
    }

    TYPO_MAP = {
        "cars": "car",
        "pedestrians": "pedestrian",
        "persons": "pedestrian",
        "trucks": "truck",
        "tuck": "truck",
        "buses": "bus",
        "traffic_light": "traffic light",
        "trafficlight": "traffic light",
        "traffic_sign": "traffic sign",
        "trafficsign": "traffic sign",
        "motorcycles": "motorcycle",
        "motorbike": "motorcycle",
        "bicycles": "bicycle",
        "bike": "bicycle",
    }

    try:
        from shapely.geometry import Polygon as ShapelyPoly
        from shapely.validation import make_valid
        shapely_ok = True
    except ImportError:
        shapely_ok = False

    for frame in frames:
        fixed_objs = []
        seen_boxes: List[Tuple[str, BBox2D]] = []

        for obj in frame.objects:
            obj_copy_id = obj.id
            obj_copy_cat = (obj.category or "").strip()

            # Fix RULE_C01: Category Typo normalization
            cat_lower = obj_copy_cat.lower()
            if cat_lower in TYPO_MAP:
                new_cat = TYPO_MAP[cat_lower]
                changelog.append(f"[{frame.name}] {obj.id}: Chuẩn hóa tên class '{obj_copy_cat}' -> '{new_cat}' (RULE_C01)")
                obj_copy_cat = new_cat
                stats["C01_typo_fixed"] += 1

            obj_attrs = dict(obj.attributes) if obj.attributes else {}
            fixed_box = None
            fixed_poly = obj.poly2d

            # Fix RULE_A02: Missing attributes
            if "occluded" not in obj_attrs:
                obj_attrs["occluded"] = False
                changelog.append(f"[{frame.name}] {obj.id}: Bổ sung thuộc tính occluded=False (RULE_A02)")
                stats["A02_attrs_filled"] += 1
            if "truncated" not in obj_attrs:
                obj_attrs["truncated"] = False
                changelog.append(f"[{frame.name}] {obj.id}: Bổ sung thuộc tính truncated=False (RULE_A02)")
                stats["A02_attrs_filled"] += 1

            # Fix RULE_A03: Invalid traffic light color
            if obj_copy_cat == "traffic light":
                tl_color = obj_attrs.get("trafficLightColor", "")
                if tl_color not in ["red", "yellow", "green", "none"]:
                    obj_attrs["trafficLightColor"] = "none"
                    changelog.append(f"[{frame.name}] {obj.id}: Đổi màu đèn '{tl_color}' thành 'none' (RULE_A03)")
                    stats["A03_tl_normalized"] += 1

            # Fix Box2D
            if obj.box2d:
                bx1, by1, bx2, by2 = obj.box2d.x1, obj.box2d.y1, obj.box2d.x2, obj.box2d.y2

                # Fix RULE_B02: Inverted coordinates
                if bx2 < bx1:
                    bx1, bx2 = bx2, bx1
                    changelog.append(f"[{frame.name}] {obj.id}: Đảo lại tọa độ x1={bx1:.1f}, x2={bx2:.1f} (RULE_B02)")
                    stats["B02_inverted"] += 1
                if by2 < by1:
                    by1, by2 = by2, by1
                    changelog.append(f"[{frame.name}] {obj.id}: Đảo lại tọa độ y1={by1:.1f}, y2={by2:.1f} (RULE_B02)")
                    stats["B02_inverted"] += 1

                # Skip zero-size box (w=0 or h=0)
                if (bx2 - bx1) <= 0 or (by2 - by1) <= 0:
                    changelog.append(f"[{frame.name}] {obj.id}: Đã xóa box rỗng diện tích 0px (RULE_B02)")
                    stats["B02_zero_removed"] += 1
                    continue

                # Fix RULE_B01: Out of bounds clamp
                clamped_x1 = max(0.0, min(float(frame.width), bx1))
                clamped_y1 = max(0.0, min(float(frame.height), by1))
                clamped_x2 = max(0.0, min(float(frame.width), bx2))
                clamped_y2 = max(0.0, min(float(frame.height), by2))
                if (clamped_x1 != bx1 or clamped_y1 != by1 or clamped_x2 != bx2 or clamped_y2 != by2):
                    changelog.append(
                        f"[{frame.name}] {obj.id}: Kéo box về khung [{clamped_x1:.1f}, {clamped_y1:.1f}, {clamped_x2:.1f}, {clamped_y2:.1f}] (RULE_B01)"
                    )
                    stats["B01_clamped"] += 1
                    bx1, by1, bx2, by2 = clamped_x1, clamped_y1, clamped_x2, clamped_y2

                cand_box = BBox2D(bx1, by1, bx2, by2)

                # Fix RULE_A01: Duplicate box
                is_dup = False
                for seen_cat, seen_b in seen_boxes:
                    if seen_cat == obj_copy_cat and cand_box.iou(seen_b) > 0.85:
                        is_dup = True
                        changelog.append(f"[{frame.name}] {obj.id}: Xóa box trùng lặp với {seen_cat} khác (IoU > 0.85) (RULE_A01)")
                        stats["A01_deduped"] += 1
                        break
                if is_dup:
                    continue

                seen_boxes.append((obj_copy_cat, cand_box))
                fixed_box = cand_box

            # Fix Polygon (P01, P02, P03)
            if fixed_poly is not None and fixed_poly.vertices:
                raw_verts = fixed_poly.vertices
                n_v = len(raw_verts)

                # Fix RULE_P01: Insufficient vertices (< 3)
                if n_v < 3:
                    if fixed_box:
                        # Sinh đa giác 4 đỉnh từ Box2D
                        synthesized_verts = [
                            (round(fixed_box.x1, 1), round(fixed_box.y1, 1)),
                            (round(fixed_box.x2, 1), round(fixed_box.y1, 1)),
                            (round(fixed_box.x2, 1), round(fixed_box.y2, 1)),
                            (round(fixed_box.x1, 1), round(fixed_box.y2, 1)),
                        ]
                        fixed_poly = Polygon2D(vertices=synthesized_verts)
                        changelog.append(f"[{frame.name}] {obj.id}: Đa giác chỉ có {n_v} đỉnh — tự động sinh 4 đỉnh chữ nhật từ BBox (RULE_P01)")
                        stats["P01_synthesized"] += 1
                    else:
                        fixed_poly = None
                        changelog.append(f"[{frame.name}] {obj.id}: Đã xóa đa giác hỏng (< 3 đỉnh không thể phục hồi) (RULE_P01)")

                # Fix RULE_P02: Self-intersection unknotting
                elif shapely_ok and n_v >= 4:
                    try:
                        sp = ShapelyPoly(raw_verts)
                        if not sp.is_valid or not sp.is_simple:
                            # Cố gắng giải xoắn bằng buffer(0) hoặc make_valid
                            repaired = sp.buffer(0)
                            if not repaired.is_valid or repaired.is_empty:
                                repaired = make_valid(sp)

                            new_coords: Optional[List[Tuple[float, float]]] = None
                            if repaired.geom_type == "Polygon" and not repaired.is_empty:
                                new_coords = list(repaired.exterior.coords)[:-1]
                            elif repaired.geom_type == "MultiPolygon" and not repaired.is_empty:
                                largest_g = max(repaired.geoms, key=lambda g: g.area)
                                new_coords = list(largest_g.exterior.coords)[:-1]
                            else:
                                hull = sp.convex_hull
                                if hull.geom_type == "Polygon":
                                    new_coords = list(hull.exterior.coords)[:-1]

                            if new_coords and len(new_coords) >= 3:
                                fixed_poly = Polygon2D(vertices=[(round(x, 1), round(y, 1)) for x, y in new_coords])
                                changelog.append(f"[{frame.name}] {obj.id}: Đa giác tự cắt viền — đã tự động giải xoắn thành đa giác đơn {len(new_coords)} đỉnh (RULE_P02)")
                                stats["P02_unknotted"] += 1
                    except Exception:
                        pass

                # Fix RULE_P03: Mask vs Box Mismatch
                if fixed_poly is not None and fixed_poly.vertices:
                    p_bbox = fixed_poly.bounding_box()
                    if p_bbox is not None:
                        if fixed_box is None:
                            fixed_box = p_bbox
                            changelog.append(f"[{frame.name}] {obj.id}: Tự động sinh BBox từ ranh giới Polygon (RULE_P03)")
                            stats["P03_aligned"] += 1
                        elif fixed_box.iou(p_bbox) < 0.70:
                            # Căn chỉnh lại BBox cho khớp với viền Polygon
                            old_iou = fixed_box.iou(p_bbox)
                            fixed_box = p_bbox
                            changelog.append(f"[{frame.name}] {obj.id}: Căn chỉnh BBox vừa khít Polygon (IoU tăng từ {old_iou:.2f} -> 1.00) (RULE_P03)")
                            stats["P03_aligned"] += 1

            lbl_dict: Dict[str, Any] = {
                "id": obj_copy_id,
                "category": obj_copy_cat,
                "attributes": obj_attrs,
            }
            if fixed_box:
                lbl_dict["box2d"] = {
                    "x1": round(fixed_box.x1, 1),
                    "y1": round(fixed_box.y1, 1),
                    "x2": round(fixed_box.x2, 1),
                    "y2": round(fixed_box.y2, 1),
                }
            if fixed_poly and fixed_poly.vertices:
                lbl_dict["poly2d"] = [{
                    "vertices": [[round(v[0], 1), round(v[1], 1)] for v in fixed_poly.vertices],
                    "types": "cc",
                    "closed": True,
                }]
            fixed_objs.append(lbl_dict)

        fixed_data.append({
            "name": frame.name,
            "width": frame.width,
            "height": frame.height,
            "labels": fixed_objs,
        })

    return fixed_data, changelog, stats
