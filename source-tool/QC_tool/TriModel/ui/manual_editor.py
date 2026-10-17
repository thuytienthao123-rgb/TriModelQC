"""
manual_editor.py — Bộ công cụ sửa tay trực tiếp dành cho Annotator & Reviewer.
Tích hợp trực tiếp vào quy trình QC để người gán nhãn có thể:
1. Chỉnh sửa tọa độ BBox (x1, y1, x2, y2), đổi tên lớp, cập nhật thuộc tính occluded/truncated.
2. Xóa các box lỗi, vẽ thừa, trùng lặp hoặc vi phạm không cứu được.
3. Chấp nhận các đối tượng bị bỏ sót do Trợ lý AI (YOLOv8) phát hiện và nạp thẳng vào tập nhãn.
4. Thêm mới hoàn toàn đối tượng nhãn vào khung hình hiện tại.
5. Tự động chạy lại quy trình đối soát QC thời gian thực và cho phép xuất/tải file nhãn đã sửa.
"""

from __future__ import annotations
import json
import time
from typing import List, Dict, Any, Optional
import streamlit as st

from qc.models import FrameData, LabeledObject, BBox2D, Polygon2D, QCReport, QCError
from qc.engine import run_qc
from qc.reporter import export_coco_json, export_yolo_zip_bytes


STANDARD_BDD_CLASSES = [
    "car",
    "truck",
    "bus",
    "pedestrian",
    "rider",
    "traffic sign",
    "traffic light",
    "motorcycle",
    "bicycle",
    "train",
    "other vehicle",
    "trailer",
]


def _sync_missed_to_report(report: QCReport, lang: str = "vi") -> None:
    """Đồng bộ tất cả các vật thể bị bỏ sót (MISSED) từ cache AI vào QCReport để xuất hiện đầy đủ trong báo cáo."""
    if report is None:
        return
    # Loại bỏ các lỗi RULE_AI01 cũ để tránh trùng lặp
    report.errors = [e for e in report.errors if e.rule_id != "RULE_AI01"]
    ai_cache = st.session_state.get("qc_ai_missed_cache", {})
    for fname, missed_items in ai_cache.items():
        for m_idx, m_obj in enumerate(missed_items, start=1):
            mbx = m_obj["box2d"]
            m_cat = m_obj["category"]
            m_conf = m_obj.get("confidence", 0.8)
            err_msg = (
                f"MISSED: Phát hiện [{m_cat}] bị bỏ sót tại [{int(mbx.x1)}, {int(mbx.y1)}, {int(mbx.x2)}, {int(mbx.y2)}] (độ tin cậy: {m_conf:.0%})"
                if lang == "vi"
                else f"MISSED: Unlabeled [{m_cat}] detected at [{int(mbx.x1)}, {int(mbx.y1)}, {int(mbx.x2)}, {int(mbx.y2)}] (confidence: {m_conf:.0%})"
            )
            report.add(QCError(
                rule_id="RULE_AI01",
                severity="ERROR" if m_conf >= 0.60 else "WARNING",
                frame_name=fname,
                object_id=f"missed_{m_idx:02d}",
                category=m_cat,
                message=err_msg,
            ))


def _reevaluate_qc(frames: List[FrameData], lang: str = "vi"):
    """Chạy lại đối soát QC trên toàn bộ dữ liệu nhãn đã chỉnh sửa và bảo toàn các lỗi MISSED."""
    active_rules = st.session_state.get("qc_rules_snapshot", None)
    active_seq_rules = st.session_state.get("qc_active_seq_rules", None)
    report = run_qc(frames, rules=active_rules, sequence_rules=active_seq_rules)
    _sync_missed_to_report(report, lang=lang)
    st.session_state["qc_report"] = report
    st.session_state["qc_frames"] = frames


def render_manual_editor_panel(
    target_obj: Optional[LabeledObject],
    selected_frame: FrameData,
    frames: List[FrameData],
    canvas_w: int = 1920,
    canvas_h: int = 1080,
    lang: str = "vi",
    loaded_img: Optional[Any] = None,
):
    """Giao diện tương tác sửa tay trực tiếp dành cho Annotator trong Inspector."""
    st.markdown("---")
    panel_title = "🛠️ BỘ CÔNG CỤ SỬA TAY NHÃN (ANNOTATOR SUITE)" if lang == "vi" else "🛠️ MANUAL ANNOTATION & REMEDIATION SUITE"
    st.markdown(f"""
    <div style="background: var(--bg-card-sub); border: 1px solid var(--val-cyan); border-radius: 8px; padding: 10px 14px; margin-bottom: 12px;">
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; font-weight: 800; color: var(--val-cyan); display: flex; align-items: center; justify-content: space-between;">
            <span>{panel_title}</span>
            <span style="font-size: 0.68rem; background: rgba(0, 229, 255, 0.15); color: var(--val-cyan); padding: 2px 6px; border-radius: 4px;">INTERACTIVE</span>
        </div>
        <p style="font-size: 0.74rem; color: var(--text-sub); margin: 4px 0 0 0;">
            {"Sửa trực tiếp tọa độ, lớp hoặc xóa/thêm box vi phạm và đối soát lại ngay lập tức." if lang == "vi" else "Directly edit coordinates, re-classify, remove defects or add missing boxes in real-time."}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 1. SỬA ĐỐI TƯỢNG ĐANG CHỌN
    # -------------------------------------------------------------------------
    if target_obj is not None:
        edit_box_title = f"✏️ Chỉnh Sửa Đối Tượng: {target_obj.id}" if lang == "vi" else f"✏️ Edit Instance: {target_obj.id}"
        with st.expander(edit_box_title, expanded=True):
            # Chọn Category
            cur_cat = target_obj.category.lower() if target_obj.category else "car"
            cat_options = STANDARD_BDD_CLASSES.copy()
            if cur_cat not in cat_options:
                cat_options.insert(0, cur_cat)
            cat_idx = cat_options.index(cur_cat) if cur_cat in cat_options else 0

            new_cat = st.selectbox(
                "Phân loại đối tượng (Category):" if lang == "vi" else "Object Category:",
                options=cat_options,
                index=cat_idx,
                key=f"medit_cat_{selected_frame.name}_{target_obj.id}",
            )

            # Tọa độ BBox
            cur_bx = target_obj.box2d or BBox2D(x1=0.0, y1=0.0, x2=100.0, y2=100.0)
            c1, c2 = st.columns(2)
            with c1:
                new_x1 = st.number_input(
                    "x1 (Trái):" if lang == "vi" else "x1 (Left):",
                    value=float(round(cur_bx.x1, 1)),
                    step=1.0,
                    min_value=0.0,
                    max_value=float(canvas_w),
                    key=f"medit_x1_{selected_frame.name}_{target_obj.id}",
                )
                new_y1 = st.number_input(
                    "y1 (Trên):" if lang == "vi" else "y1 (Top):",
                    value=float(round(cur_bx.y1, 1)),
                    step=1.0,
                    min_value=0.0,
                    max_value=float(canvas_h),
                    key=f"medit_y1_{selected_frame.name}_{target_obj.id}",
                )
            with c2:
                new_x2 = st.number_input(
                    "x2 (Phải):" if lang == "vi" else "x2 (Right):",
                    value=float(round(cur_bx.x2, 1)),
                    step=1.0,
                    min_value=0.0,
                    max_value=float(canvas_w),
                    key=f"medit_x2_{selected_frame.name}_{target_obj.id}",
                )
                new_y2 = st.number_input(
                    "y2 (Dưới):" if lang == "vi" else "y2 (Bottom):",
                    value=float(round(cur_bx.y2, 1)),
                    step=1.0,
                    min_value=0.0,
                    max_value=float(canvas_h),
                    key=f"medit_y2_{selected_frame.name}_{target_obj.id}",
                )

            # Thuộc tính
            cur_attrs = target_obj.attributes or {}
            a1, a2 = st.columns(2)
            with a1:
                new_occ = st.checkbox(
                    "Bị che khuất (Occluded)" if lang == "vi" else "Occluded",
                    value=bool(cur_attrs.get("occluded", False)),
                    key=f"medit_occ_{selected_frame.name}_{target_obj.id}",
                )
            with a2:
                new_trunc = st.checkbox(
                    "Bị cắt xén (Truncated)" if lang == "vi" else "Truncated",
                    value=bool(cur_attrs.get("truncated", False)),
                    key=f"medit_trunc_{selected_frame.name}_{target_obj.id}",
                )

            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                btn_save_lbl = "💾 Lưu Thay Đổi" if lang == "vi" else "💾 Save Edits"
                if st.button(btn_save_lbl, use_container_width=True, type="primary", key=f"btn_save_{selected_frame.name}_{target_obj.id}"):
                    if new_x2 <= new_x1 or new_y2 <= new_y1:
                        st.error("⚠️ Tọa độ không hợp lệ: x2 phải lớn hơn x1 và y2 phải lớn hơn y1!" if lang == "vi" else "⚠️ Invalid coords: x2 > x1 and y2 > y1 required!")
                    else:
                        target_obj.category = new_cat
                        target_obj.box2d = BBox2D(x1=new_x1, y1=new_y1, x2=new_x2, y2=new_y2)
                        if target_obj.attributes is None:
                            target_obj.attributes = {}
                        target_obj.attributes["occluded"] = new_occ
                        target_obj.attributes["truncated"] = new_trunc
                        _reevaluate_qc(frames, lang=lang)
                        st.toast(f"✅ Đã lưu đối tượng {target_obj.id} và cập nhật đối soát QC!", icon="💾")
                        st.rerun()

            with btn_col2:
                btn_del_lbl = "🗑️ Xóa Box Này" if lang == "vi" else "🗑️ Delete Box"
                if st.button(btn_del_lbl, use_container_width=True, key=f"btn_del_{selected_frame.name}_{target_obj.id}"):
                    selected_frame.objects = [o for o in selected_frame.objects if o.id != target_obj.id]
                    _reevaluate_qc(frames, lang=lang)
                    st.toast(f"🗑️ Đã xóa đối tượng {target_obj.id} khỏi nhãn!", icon="🗑️")
                    st.rerun()

    # -------------------------------------------------------------------------
    # 2. CHẤP NHẬN GỢI Ý VẬT THỂ BỎ SÓT (MISSED -> NẠP THÀNH NHÃN)
    # -------------------------------------------------------------------------
    ai_missed_cache = st.session_state.get("qc_ai_missed_cache", {}).get(selected_frame.name, [])
    if ai_missed_cache:
        ai_box_title = f"🤖 Gợi Ý MISSED: Phát Hiện {len(ai_missed_cache)} Vật Thể Bỏ Sót" if lang == "vi" else f"🤖 MISSED Suggestions: {len(ai_missed_cache)} Unlabeled Instances"
        with st.expander(ai_box_title, expanded=True):
            st.caption(
                "Trợ lý AI phát hiện các đối tượng bị bỏ sót (MISSED) chưa được gán nhãn. Bạn có thể nạp từng đối tượng hoặc nạp toàn bộ một lần:"
                if lang == "vi"
                else "AI consensus detected unlabeled objects (MISSED). Accept individually or import all at once:"
            )

            # NÚT NẠP TOÀN BỘ VẬT THỂ BỎ SÓT
            btn_all_lbl = f"📥 Nạp Toàn Bộ Vật Thể Bỏ Sót Vào Nhãn ({len(ai_missed_cache)})" if lang == "vi" else f"📥 Accept All Missed Objects ({len(ai_missed_cache)})"
            if st.button(btn_all_lbl, type="primary", use_container_width=True, key=f"btn_acc_all_{selected_frame.name}"):
                added_count = 0
                for m_idx, m_item in enumerate(ai_missed_cache):
                    mbx: BBox2D = m_item["box2d"]
                    mcat = m_item["category"]
                    new_id = f"missed_{mcat[:3]}_{int(time.time()*100)%10000}_{m_idx+1}"
                    new_obj = LabeledObject(
                        id=new_id,
                        category=mcat,
                        box2d=BBox2D(x1=mbx.x1, y1=mbx.y1, x2=mbx.x2, y2=mbx.y2),
                        attributes={"occluded": False, "truncated": False},
                    )
                    selected_frame.objects.append(new_obj)
                    added_count += 1
                # Xóa toàn bộ cache cho frame này vì đã được nạp thành công
                st.session_state["qc_ai_missed_cache"][selected_frame.name] = []
                _reevaluate_qc(frames, lang=lang)
                st.toast(f"✅ Đã nạp toàn bộ {added_count} vật thể bỏ sót vào danh sách nhãn!", icon="📥")
                st.rerun()

            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

            # NẠP TỪNG ĐỐI TƯỢNG RIÊNG LẺ
            for m_i, m_item in enumerate(ai_missed_cache):
                mbx: BBox2D = m_item["box2d"]
                mcat = m_item["category"]
                mconf = m_item.get("confidence", 0.8)
                
                mcol_info, mcol_btn = st.columns([6, 4])
                with mcol_info:
                    st.markdown(
                        f"**{mcat}** · `[{int(mbx.x1)}, {int(mbx.y1)}, {int(mbx.x2)}, {int(mbx.y2)}]` ({mconf:.0%})"
                    )
                with mcol_btn:
                    btn_acc_lbl = "➕ Nạp Vào..." if lang == "vi" else "➕ Add Box"
                    if st.button(btn_acc_lbl, key=f"btn_acc_ai_{selected_frame.name}_{m_i}", use_container_width=True):
                        new_id = f"missed_{mcat[:3]}_{int(time.time()*100)%10000}"
                        new_obj = LabeledObject(
                            id=new_id,
                            category=mcat,
                            box2d=BBox2D(x1=mbx.x1, y1=mbx.y1, x2=mbx.x2, y2=mbx.y2),
                            attributes={"occluded": False, "truncated": False},
                        )
                        selected_frame.objects.append(new_obj)
                        # Gỡ khỏi cache AI để không bị cảnh báo trùng
                        ai_missed_cache.pop(m_i)
                        st.session_state["qc_ai_missed_cache"][selected_frame.name] = ai_missed_cache
                        _reevaluate_qc(frames, lang=lang)
                        st.toast(f"✅ Đã nạp đối tượng MISSED [{mcat}] vào danh sách nhãn!", icon="➕")
                        st.rerun()

    # -------------------------------------------------------------------------
    # 3. VẼ TAY TRỰC QUAN / THÊM ĐỐI TƯỢNG MỚI (VISUAL CLICK-AND-DRAG BBOX)
    # -------------------------------------------------------------------------
    add_box_title = "🎨 Vẽ Tay & Thêm Đối Tượng Mới Vào Khung Hình" if lang == "vi" else "🎨 Visual Draw & Add Annotation Box"
    with st.expander(add_box_title, expanded=False):
        add_cat = st.selectbox(
            "Lớp đối tượng cần vẽ:" if lang == "vi" else "Target Category:",
            options=STANDARD_BDD_CLASSES,
            index=0,
            key=f"madd_cat_{selected_frame.name}",
        )

        # Kiểm tra xem có ảnh hiển thị để người dùng vẽ tay trực tiếp hay không
        if loaded_img is not None:
            st.markdown(
                """
                <div style="background: rgba(0, 229, 255, 0.08); border-left: 3px solid #00e5ff; padding: 6px 10px; margin-bottom: 8px; border-radius: 4px; font-size: 0.78rem;">
                    🎯 <strong>Hướng dẫn vẽ tay trực quan:</strong> Nhấn giữ chuột và kéo thả (Drag & Drop) quanh vật thể nhìn thấy trên ảnh dưới đây. Box sẽ tự động được tạo theo đúng kích thước bạn vẽ!
                </div>
                """
                if lang == "vi"
                else """
                <div style="background: rgba(0, 229, 255, 0.08); border-left: 3px solid #00e5ff; padding: 6px 10px; margin-bottom: 8px; border-radius: 4px; font-size: 0.78rem;">
                    🎯 <strong>Visual Mouse Drawing:</strong> Click and drag your mouse across the object in the image below to automatically create a bounding box.
                </div>
                """,
                unsafe_allow_html=True,
            )

            from ui.visual_drawer import visual_bbox_drawer
            draw_result = visual_bbox_drawer(
                loaded_img,
                label=add_cat,
                orig_w=canvas_w,
                orig_h=canvas_h,
                display_w=390,
                key=f"visual_drawer_{selected_frame.name}",
            )

            # Khi người dùng kéo thả chuột vẽ xong trên Canvas
            if draw_result and "x1" in draw_result and "x2" in draw_result:
                st.session_state[f"drawn_box_{selected_frame.name}"] = {
                    "x1": draw_result["x1"],
                    "y1": draw_result["y1"],
                    "x2": draw_result["x2"],
                    "y2": draw_result["y2"],
                    "cat": add_cat,
                }

            drawn_cache = st.session_state.get(f"drawn_box_{selected_frame.name}")
            if drawn_cache:
                bx1 = drawn_cache["x1"]
                by1 = drawn_cache["y1"]
                bx2 = drawn_cache["x2"]
                by2 = drawn_cache["y2"]
                bw = int(bx2 - bx1)
                bh = int(by2 - by1)

                st.markdown(
                    f"""
                    <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid #10b981; border-radius: 6px; padding: 8px 12px; margin: 8px 0;">
                        <span style="color: #10b981; font-weight: 700; font-size: 0.8rem;">✨ Box Bạn Vừa Vẽ:</span>
                        <div style="font-family: monospace; font-size: 0.82rem; color: #f8fafc; margin-top: 2px;">
                            Lớp: <strong style="color: #00e5ff;">{add_cat}</strong> · [{bx1}, {by1}, {bx2}, {by2}] ({bw}×{bh} px)
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                btn_c1, btn_c2 = st.columns([6, 4])
                with btn_c1:
                    btn_confirm_lbl = "➕ Thêm Box Vừa Vẽ Này" if lang == "vi" else "➕ Add Drawn Box"
                    if st.button(btn_confirm_lbl, type="primary", use_container_width=True, key=f"btn_add_drawn_{selected_frame.name}"):
                        new_id = f"user_{add_cat[:3]}_{len(selected_frame.objects)+1:02d}"
                        new_obj = LabeledObject(
                            id=new_id,
                            category=add_cat,
                            box2d=BBox2D(x1=bx1, y1=by1, x2=bx2, y2=by2),
                            attributes={"occluded": False, "truncated": False},
                        )
                        selected_frame.objects.append(new_obj)
                        st.session_state.pop(f"drawn_box_{selected_frame.name}", None)
                        _reevaluate_qc(frames, lang=lang)
                        st.toast(f"✅ Đã thêm mới đối tượng {new_id} ({add_cat}) từ nét vẽ!", icon="🎉")
                        st.rerun()

                with btn_c2:
                    btn_reset_lbl = "🔄 Vẽ Lại" if lang == "vi" else "🔄 Reset"
                    if st.button(btn_reset_lbl, use_container_width=True, key=f"btn_reset_drawn_{selected_frame.name}"):
                        st.session_state.pop(f"drawn_box_{selected_frame.name}", None)
                        st.rerun()

        # Phần nhập tọa độ số phụ (Dành cho trường hợp không có ảnh hoặc muốn vi chỉnh)
        with st.expander("⚙️ Nhập tọa độ số thủ công (Tùy chọn phụ)" if lang == "vi" else "⚙️ Manual Coordinate Input (Optional)", expanded=(loaded_img is None)):
            col_ax1, col_ax2 = st.columns(2)
            with col_ax1:
                add_x1 = st.number_input("x1:", value=50.0, step=10.0, min_value=0.0, max_value=float(canvas_w), key=f"madd_x1_{selected_frame.name}")
                add_y1 = st.number_input("y1:", value=50.0, step=10.0, min_value=0.0, max_value=float(canvas_h), key=f"madd_y1_{selected_frame.name}")
            with col_ax2:
                add_x2 = st.number_input("x2:", value=250.0, step=10.0, min_value=0.0, max_value=float(canvas_w), key=f"madd_x2_{selected_frame.name}")
                add_y2 = st.number_input("y2:", value=200.0, step=10.0, min_value=0.0, max_value=float(canvas_h), key=f"madd_y2_{selected_frame.name}")

            btn_add_lbl = "➕ Thêm Bằng Tọa Độ Số" if lang == "vi" else "➕ Add Box by Numbers"
            if st.button(btn_add_lbl, use_container_width=True, key=f"btn_add_new_{selected_frame.name}"):
                if add_x2 <= add_x1 or add_y2 <= add_y1:
                    st.error("⚠️ Tọa độ không hợp lệ: x2 > x1 và y2 > y1!" if lang == "vi" else "⚠️ Invalid: x2 > x1 and y2 > y1!")
                else:
                    new_id = f"user_{len(selected_frame.objects)+1:03d}"
                    new_obj = LabeledObject(
                        id=new_id,
                        category=add_cat,
                        box2d=BBox2D(x1=add_x1, y1=add_y1, x2=add_x2, y2=add_y2),
                        attributes={"occluded": False, "truncated": False},
                    )
                    selected_frame.objects.append(new_obj)
                    _reevaluate_qc(frames, lang=lang)
                    st.toast(f"✅ Đã thêm mới đối tượng {new_id} ({add_cat})!", icon="🎉")
                    st.rerun()

    # -------------------------------------------------------------------------
    # 4. TẢI VỀ BỘ NHÃN ĐÃ SỬA HOÀN TẤT
    # -------------------------------------------------------------------------
    exp_title = "📥 Xuất Tệp Nhãn Đã Sửa (BDD100K / YOLO)" if lang == "vi" else "📥 Export Healed Annotations"
    with st.expander(exp_title, expanded=False):
        st.caption(
            "Tải về ngay bộ dữ liệu đã được chữa lành và kiểm định đạt chuẩn:"
            if lang == "vi"
            else "Download the remediated dataset ready for model training:"
        )
        # 1. BDD100K JSON
        export_data = []
        for f in frames:
            f_dict = {"name": f.name, "labels": []}
            for o in f.objects:
                lbl = {
                    "id": o.id,
                    "category": o.category,
                    "attributes": o.attributes or {},
                }
                if o.box2d:
                    lbl["box2d"] = {
                        "x1": o.box2d.x1,
                        "y1": o.box2d.y1,
                        "x2": o.box2d.x2,
                        "y2": o.box2d.y2,
                    }
                if o.poly2d:
                    poly_types = getattr(o.poly2d, "types", "L" * len(o.poly2d.vertices))
                    poly_closed = getattr(o.poly2d, "closed", True)
                    lbl["poly2d"] = [{"vertices": [list(v) for v in o.poly2d.vertices], "types": poly_types, "closed": poly_closed}]
                f_dict["labels"].append(lbl)
            export_data.append(f_dict)

        bdd_json_bytes = json.dumps(export_data, indent=2, ensure_ascii=False).encode("utf-8")
        st.download_button(
            "📄 " + ("Tải Nhãn BDD100K Đã Sửa (.json)" if lang == "vi" else "Download Healed BDD100K (.json)"),
            data=bdd_json_bytes,
            file_name=f"{selected_frame.name}_healed.json",
            mime="application/json",
            use_container_width=True,
            key=f"dl_bdd_healed_{selected_frame.name}",
        )

        # 2. YOLO Zip
        try:
            yolo_bytes = export_yolo_zip_bytes(frames)
            st.download_button(
                "📦 " + ("Tải Toàn Bộ Nhãn YOLO (.zip)" if lang == "vi" else "Download YOLO Labels (.zip)"),
                data=yolo_bytes,
                file_name="yolo_healed_labels.zip",
                mime="application/zip",
                use_container_width=True,
                key=f"dl_yolo_healed_{selected_frame.name}",
            )
        except Exception:
            pass
