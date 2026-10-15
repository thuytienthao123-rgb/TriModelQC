from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Any
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

from qc.models import QCReport, FrameData
from qc.reporter import (
    generate_csv_str,
    generate_html_str,
    export_coco_json,
    export_yolo_zip_bytes,
)
from ui.constants import RULE_SUGGESTIONS
from ui.auto_fix import auto_correct_frames


def render_tab_error_list(report: QCReport, frames: List[FrameData], file_display_name: str):
    """Render Tab 1: Danh sách lỗi vi phạm, QC Disposition Hub, Xuất đa định dạng (CSV, HTML, COCO, YOLO)."""
    total_issues = len(report.errors)

    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; flex-wrap: wrap; gap: 10px;">
        <div>
            <h3 style="margin: 0; color: #f8fafc; font-size: 1.25rem;">Danh Sách Vi Phạm & Trung Tâm Phê Duyệt (Disposition Hub)</h3>
            <p style="margin: 2px 0 0 0; color: #94a3b8; font-size: 0.85rem;">Chi tiết từng đối tượng lỗi kèm hướng dẫn khắc phục cụ thể và phê duyệt của Reviewer</p>
        </div>
        <div style="display: flex; gap: 8px;">
            <span class="badge-err">🔴 {report.error_count()} ERRORs</span>
            <span class="badge-warn">🟡 {report.warning_count()} WARNINGs</span>
            <span class="badge-ok">📦 {total_issues} Tổng số</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if total_issues == 0:
        st.success("🎉 Xuất sắc! Dữ liệu nhãn hoàn toàn sạch sẽ, không có lỗi hay cảnh báo nào.")
        return

    # Khởi tạo kho lưu trữ ghi chú của reviewer
    if "qc_reviewer_notes" not in st.session_state:
        st.session_state["qc_reviewer_notes"] = {}
    reviewer_notes = st.session_state["qc_reviewer_notes"]

    # Bảng điều khiển ghi chú & duyệt lỗi (Reviewer Disposition Hub)
    with st.expander("📝 Phê Duyệt & Ghi Chú Của Reviewer (QC Disposition Hub)", expanded=False):
        st.caption("Reviewer có thể viết nhận xét, hướng dẫn sửa đổi cụ thể cho Annotator hoặc duyệt ngoại lệ:")
        issue_items = []
        issue_keys = []
        for e in report.errors:
            k = f"{e.frame_name}_{e.object_id}_{e.rule_id}"
            issue_keys.append(k)
            issue_items.append(f"[{e.rule_id}] {e.frame_name} · {e.object_id} ({e.category}) - {e.severity}")

        sel_idx = 0
        r_col1, r_col2 = st.columns([6, 4])
        with r_col1:
            selected_issue_label = st.selectbox("Chọn vi phạm để ghi chú:", options=issue_items, index=0)
            sel_idx = issue_items.index(selected_issue_label) if selected_issue_label in issue_items else 0
            target_key = issue_keys[sel_idx]

        cur_note_entry = reviewer_notes.get(target_key, {})
        with r_col2:
            disp_status = st.selectbox(
                "Quyết định duyệt:",
                options=["🔴 Bắt buộc sửa (Fix Required)", "🟡 Chấp nhận ngoại lệ (Waived / Pass)", "🟢 Đã xác minh đạt (Verified)"],
                index=0 if "Fix" in cur_note_entry.get("status", "") else (1 if "Waived" in cur_note_entry.get("status", "") else 0),
            )

        user_comment = st.text_input(
            "Nhận xét chi tiết cho Annotator:",
            value=cur_note_entry.get("comment", ""),
            placeholder="Ví dụ: Đa giác cần nắn thêm 2 đỉnh ở phần gương chiếu hậu...",
        )

        b_c1, b_c2 = st.columns([3, 7])
        with b_c1:
            if st.button("💾 Lưu Quyết Định Duyệt", use_container_width=True, type="primary"):
                reviewer_notes[target_key] = {
                    "status": disp_status,
                    "comment": user_comment.strip(),
                }
                st.session_state["qc_reviewer_notes"] = reviewer_notes
                st.toast(f"✅ Đã lưu nhận xét cho {report.errors[sel_idx].object_id}", icon="💾")
                st.rerun()
        with b_c2:
            if target_key in reviewer_notes:
                st.caption(f"Trạng thái hiện tại: **{cur_note_entry.get('status')}** | Ghi chú: *'{cur_note_entry.get('comment')}'*")

    # Tạo bảng dữ liệu kèm cột ghi chú Reviewer
    records = []
    for e in report.errors:
        k = f"{e.frame_name}_{e.object_id}_{e.rule_id}"
        n_entry = reviewer_notes.get(k) or reviewer_notes.get(e.object_id) or {}
        records.append({
            "Frame": e.frame_name,
            "Object ID": e.object_id,
            "Class": e.category,
            "Rule": e.rule_id,
            "Mức độ": e.severity,
            "Chi tiết lỗi": e.message,
            "💡 Hướng dẫn sửa": RULE_SUGGESTIONS.get(e.rule_id, "Kiểm tra và sửa theo quy chuẩn BDD100K."),
            "Trạng thái QC": n_entry.get("status", "🔴 Chờ sửa"),
            "Nhận xét Reviewer": n_entry.get("comment", ""),
        })
    df_errors = pd.DataFrame(records)

    # Bộ lọc tương tác (Mức độ, Rule, Class, Tìm kiếm)
    fcol1, fcol2, fcol3, fcol4 = st.columns([2, 2.2, 2.2, 3.6])
    with fcol1:
        severity_filter = st.selectbox("Lọc mức độ:", options=["Tất cả", "ERROR", "WARNING"], index=0)
    with fcol2:
        rules_available = ["Tất cả"] + sorted(list(df_errors["Rule"].unique()))
        rule_filter = st.selectbox("Lọc theo Rule:", options=rules_available, index=0)
    with fcol3:
        classes_available = ["Tất cả"] + sorted(list(df_errors["Class"].unique()))
        class_filter = st.selectbox("Lọc theo Class:", options=classes_available, index=0)
    with fcol4:
        search_text = st.text_input("🔍 Tìm kiếm nhanh:", "", placeholder="ID, frame, class, mô tả...")

    filtered_df = df_errors.copy()
    if severity_filter != "Tất cả":
        filtered_df = filtered_df[filtered_df["Mức độ"] == severity_filter]
    if rule_filter != "Tất cả":
        filtered_df = filtered_df[filtered_df["Rule"] == rule_filter]
    if class_filter != "Tất cả":
        filtered_df = filtered_df[filtered_df["Class"] == class_filter]
    if search_text:
        s = search_text.lower()
        filtered_df = filtered_df[
            filtered_df["Frame"].str.lower().str.contains(s) |
            filtered_df["Object ID"].str.lower().str.contains(s) |
            filtered_df["Class"].str.lower().str.contains(s) |
            filtered_df["Chi tiết lỗi"].str.lower().str.contains(s) |
            filtered_df["Nhận xét Reviewer"].str.lower().str.contains(s)
        ]

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Mức độ": st.column_config.TextColumn("Mức độ", help="ERROR: Bắt buộc sửa | WARNING: Cần rà soát"),
            "Rule": st.column_config.TextColumn("Mã Rule"),
            "💡 Hướng dẫn sửa": st.column_config.TextColumn("💡 Hướng dẫn sửa", width="medium"),
            "Trạng thái QC": st.column_config.TextColumn("Trạng thái", width="small"),
            "Nhận xét Reviewer": st.column_config.TextColumn("📝 Ghi chú Reviewer", width="medium"),
        }
    )

    st.caption(f"Đang hiển thị **{len(filtered_df)} / {total_issues}** vấn đề vi phạm.")

    # -----------------------------------------------------------------------
    # NÚT XUẤT BÁO CÁO ĐA ĐỊNH DẠNG (EXPORT HUB)
    # -----------------------------------------------------------------------
    st.markdown("##### 📥 Xuất Báo Cáo & Tập Dữ Liệu Đã Kiểm Duyệt (Multi-Format Export Hub):")
    dcol1, dcol2, dcol3, dcol4 = st.columns(4)

    with dcol1:
        csv_data = generate_csv_str(
            report,
            reviewer_notes=reviewer_notes,
            rule_suggestions=RULE_SUGGESTIONS,
        )
        st.download_button(
            label="📄 Tải Báo Cáo CSV (Có Note Reviewer)",
            data=csv_data.encode("utf-8-sig"),
            file_name=f"qc_report_{Path(file_display_name).stem or file_display_name}.csv",
            mime="text/csv",
            use_container_width=True,
            help="File CSV có đủ mã lỗi, gợi ý sửa, ghi chú phê duyệt của Reviewer, mở tiếng Việt trên Excel không lỗi font",
        )

    with dcol2:
        html_data = generate_html_str(report)
        st.download_button(
            label="🌐 Báo Cáo HTML (Bản In PDF A4)",
            data=html_data,
            file_name=f"qc_report_{Path(file_display_name).stem or file_display_name}.html",
            mime="text/html",
            use_container_width=True,
            help="Báo cáo HTML Dashboard độc lập có tìm kiếm, bộ lọc và định dạng in PDF A4 chuyên nghiệp",
        )

    with dcol3:
        coco_json_str = export_coco_json(frames)
        st.download_button(
            label="📦 Xuất Tập Nhãn COCO JSON",
            data=coco_json_str.encode("utf-8"),
            file_name=f"coco_instances_{Path(file_display_name).stem or file_display_name}.json",
            mime="application/json",
            use_container_width=True,
            help="Xuất tập dữ liệu theo chuẩn COCO JSON (instances_default.json) dùng cho Detectron2/MMDetection",
        )

    with dcol4:
        yolo_zip_bytes = export_yolo_zip_bytes(frames)
        st.download_button(
            label="⚡ Xuất Nhãn YOLO TXT (ZIP)",
            data=yolo_zip_bytes,
            file_name=f"yolo_labels_{Path(file_display_name).stem or file_display_name}.zip",
            mime="application/zip",
            use_container_width=True,
            help="Tải tệp ZIP chứa classes.txt và các file txt chuẩn YOLO (class xc yc w h) để huấn luyện YOLOv8",
        )

    # Xem trước trực tiếp HTML Dashboard ngay trên app
    with st.expander("🌐 Xem trước Báo cáo HTML Trực quan (Interactive Live Preview)", expanded=False):
        components.html(html_data, height=560, scrolling=True)

    # Bộ Công Cụ Tự Động Sửa Lỗi (1-Click Auto-Fix)
    with st.expander("🛠️ Bộ Công Cụ Tự Động Sửa Lỗi (1-Click Auto-Fix & Xuất BDD100K Đã Sửa)", expanded=False):
        st.markdown("""
        **Thuật toán tự động khắc phục toàn diện các lỗi vi phạm (Đề tài N2-04A):**
        - 📏 **Clamp BBox (B01):** Tự động kéo bounding box bị tràn viền về đúng kích thước khung ảnh.
        - 🔄 **Invert Coords (B02):** Đảo lại tọa độ bị ngược (x1 > x2 hoặc y1 > y2).
        - 🗑️ **Zero-size Box (B02):** Tự động gỡ bỏ các box rỗng (w=0 và h=0).
        - 📉 **Synthesize Poly (P01):** Tự động sinh hình chữ nhật 4 đỉnh từ BBox cho đa giác < 3 đỉnh.
        - 🎗️ **Unknot Poly (P02):** Dùng Shapely giải phóng xoắn nơ tự cắt viền thành đa giác đơn.
        - 🎯 **Align Mask vs Box (P03):** Căn chỉnh lại BBox theo đúng viền bao Polygon (IoU = 1.0).
        - 👥 **Duplicate Box (A01):** Tự động loại bỏ các box trùng lặp cùng category (IoU > 0.85).
        - 🏷️ **Missing Attributes (A02):** Bổ sung thuộc tính mặc định `occluded=False`, `truncated=False`.
        - 🚦 **Traffic Light Color (A03):** Chuẩn hóa giá trị màu đèn sai lệch về `none`.
        - 🔤 **Category Typos (C01):** Tự động sửa lỗi chính tả tên class về chuẩn BDD100K.
        """)

        if st.button("✨ Thực Thi Tự Động Sửa Lỗi (Run Auto-Fix Engine)", type="primary", key="btn_run_autofix", use_container_width=True):
            fixed_dataset, changelog, fix_stats = auto_correct_frames(frames)
            st.session_state["auto_fix_done"] = True
            st.session_state["auto_fix_data"] = fixed_dataset
            st.session_state["auto_fix_log"] = changelog
            st.session_state["auto_fix_stats"] = fix_stats
            st.rerun()

        if st.session_state.get("auto_fix_done", False):
            fixed_data = st.session_state.get("auto_fix_data", [])
            logs = st.session_state.get("auto_fix_log", [])
            fix_stats = st.session_state.get("auto_fix_stats", {})
            st.success(f"🎉 Đã tự động xử lý và khắc phục thành công **{len(logs)} vị trí vi phạm**!")

            # Hiển thị tóm tắt các hạng mục đã sửa
            if fix_stats:
                s_col1, s_col2, s_col3, s_col4 = st.columns(4)
                s_col1.metric("📏 BBox Clamped & Inverted", fix_stats.get("B01_clamped", 0) + fix_stats.get("B02_inverted", 0))
                s_col2.metric("📉 Polygon Healed & Aligned", fix_stats.get("P01_synthesized", 0) + fix_stats.get("P02_unknotted", 0) + fix_stats.get("P03_aligned", 0))
                s_col3.metric("👥 Deduped & Cleaned", fix_stats.get("A01_deduped", 0) + fix_stats.get("B02_zero_removed", 0))
                s_col4.metric("🏷️ Attributes & Class Typos", fix_stats.get("A02_attrs_filled", 0) + fix_stats.get("A03_tl_normalized", 0) + fix_stats.get("C01_typo_fixed", 0))

            with st.expander("📝 Nhật ký chi tiết các mục đã sửa (Changelog):", expanded=True):
                for log_item in logs[:50]:
                    st.markdown(f"- `{log_item}`")
                if len(logs) > 50:
                    st.caption(f"... và {len(logs) - 50} mục khác.")

            fixed_json_bytes = json.dumps(fixed_data, indent=2, ensure_ascii=False).encode("utf-8")
            st.download_button(
                label="💾 Tải Về Tệp BDD100K Đã Sửa Lỗi (Cleaned JSON)",
                data=fixed_json_bytes,
                file_name=f"bdd100k_cleaned_{file_display_name}.json",
                mime="application/json",
                use_container_width=True,
            )
