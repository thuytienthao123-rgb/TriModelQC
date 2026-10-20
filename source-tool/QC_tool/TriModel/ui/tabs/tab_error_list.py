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
    export_bdd100k_json,
    export_bdd100k_zip_bytes,
    export_anylabeling_zip_bytes,
    export_cvat_xml_str,
)
from ui.constants import RULE_SUGGESTIONS
from ui.auto_fix import auto_correct_frames
from ui.i18n import get_current_lang


def render_tab_error_list(report: QCReport, frames: List[FrameData], file_display_name: str):
    """Render Tab 1: Danh sách lỗi vi phạm, Bảng phê duyệt, Xuất đa định dạng (CSV, HTML, COCO, YOLO)."""
    lang = get_current_lang()
    total_issues = len(report.errors)

    if lang == "vi":
        header_title = "Danh Sách Vi Phạm & Bảng Phê Duyệt"
        header_sub = "Chi tiết từng đối tượng lỗi kèm hướng dẫn khắc phục cụ thể và phê duyệt của Reviewer"
        badge_err_txt = f"🔴 {report.error_count()} LỖI"
        badge_warn_txt = f"🟡 {report.warning_count()} CẢNH BÁO"
        badge_ok_txt = f"📦 {total_issues} Tổng số"
    else:
        header_title = "Defect Catalog & Reviewer Disposition Hub"
        header_sub = "Detailed violation breakdown with remediation guidelines and reviewer disposition actions"
        badge_err_txt = f"🔴 {report.error_count()} ERRORs"
        badge_warn_txt = f"🟡 {report.warning_count()} WARNINGs"
        badge_ok_txt = f"📦 {total_issues} Total"

    st.markdown(f"""
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; flex-wrap: wrap; gap: 10px;">
        <div>
            <h3 style="margin: 0; color: #f8fafc; font-size: 1.25rem;">{header_title}</h3>
            <p style="margin: 2px 0 0 0; color: #94a3b8; font-size: 0.85rem;">{header_sub}</p>
        </div>
        <div style="display: flex; gap: 8px;">
            <span class="badge-err">{badge_err_txt}</span>
            <span class="badge-warn">{badge_warn_txt}</span>
            <span class="badge-ok">{badge_ok_txt}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if total_issues == 0:
        if lang == "vi":
            st.success("🎉 Xuất sắc! Dữ liệu nhãn hoàn toàn sạch sẽ, không có lỗi hay cảnh báo nào.")
        else:
            st.success("🎉 Perfect! Dataset is 100% compliant with zero defects or warnings.")
        return

    # Khởi tạo kho lưu trữ ghi chú của reviewer
    if "qc_reviewer_notes" not in st.session_state:
        st.session_state["qc_reviewer_notes"] = {}
    reviewer_notes = st.session_state["qc_reviewer_notes"]

    # Bảng điều khiển ghi chú & duyệt lỗi (Reviewer Disposition Hub)
    expander_hub_label = "📝 Phê Duyệt & Ghi Chú Của Reviewer" if lang == "vi" else "📝 Reviewer Disposition & Action Notes"
    with st.expander(expander_hub_label, expanded=False):
        hub_caption = (
            "Reviewer có thể viết nhận xét, hướng dẫn sửa đổi cụ thể cho Annotator hoặc duyệt ngoại lệ:"
            if lang == "vi"
            else "Reviewers can assign remediation instructions to annotators or waive exceptions:"
        )
        st.caption(hub_caption)
        issue_items = []
        issue_keys = []
        for e in report.errors:
            k = f"{e.frame_name}_{e.object_id}_{e.rule_id}"
            issue_keys.append(k)
            issue_items.append(f"[{e.rule_id}] {e.frame_name} · {e.object_id} ({e.category}) - {e.severity}")

        sel_idx = 0
        r_col1, r_col2 = st.columns([6, 4])
        with r_col1:
            sel_prompt = "Chọn vi phạm để ghi chú:" if lang == "vi" else "Select violation to annotate:"
            selected_issue_label = st.selectbox(sel_prompt, options=issue_items, index=0)
            sel_idx = issue_items.index(selected_issue_label) if selected_issue_label in issue_items else 0
            target_key = issue_keys[sel_idx]

        cur_note_entry = reviewer_notes.get(target_key, {})
        with r_col2:
            disp_options = (
                ["🔴 Bắt buộc sửa", "🟡 Chấp nhận ngoại lệ", "🟢 Đã xác minh đạt"]
                if lang == "vi"
                else ["🔴 Fix Required", "🟡 Waived / Accepted", "🟢 Verified"]
            )
            disp_prompt = "Quyết định duyệt:" if lang == "vi" else "Disposition Decision:"
            disp_status = st.selectbox(
                disp_prompt,
                options=disp_options,
                index=0 if "sửa" in cur_note_entry.get("status", "").lower() or "fix" in cur_note_entry.get("status", "").lower()
                else (1 if "ngoại lệ" in cur_note_entry.get("status", "").lower() or "waived" in cur_note_entry.get("status", "").lower() else 0),
            )

        comment_prompt = "Nhận xét chi tiết cho Annotator:" if lang == "vi" else "Remediation note for annotator:"
        comment_placeholder = "Ví dụ: Đa giác cần nắn thêm 2 đỉnh ở phần gương chiếu hậu..." if lang == "vi" else "e.g., Adjust bounding box tighter along left bumper..."
        user_comment = st.text_input(
            comment_prompt,
            value=cur_note_entry.get("comment", ""),
            placeholder=comment_placeholder,
        )

        b_c1, b_c2 = st.columns([3, 7])
        with b_c1:
            save_btn_lbl = "💾 Lưu Quyết Định Duyệt" if lang == "vi" else "💾 Save Disposition"
            if st.button(save_btn_lbl, use_container_width=True, type="primary"):
                reviewer_notes[target_key] = {
                    "status": disp_status,
                    "comment": user_comment.strip(),
                }
                st.session_state["qc_reviewer_notes"] = reviewer_notes
                saved_toast = f"✅ Đã lưu nhận xét cho {report.errors[sel_idx].object_id}" if lang == "vi" else f"✅ Saved note for {report.errors[sel_idx].object_id}"
                st.toast(saved_toast, icon="💾")
                st.rerun()
        with b_c2:
            if target_key in reviewer_notes:
                curr_status_msg = (
                    f"Trạng thái hiện tại: **{cur_note_entry.get('status')}** | Ghi chú: *'{cur_note_entry.get('comment')}'*"
                    if lang == "vi"
                    else f"Current status: **{cur_note_entry.get('status')}** | Note: *'{cur_note_entry.get('comment')}'*"
                )
                st.caption(curr_status_msg)

    # Tạo bảng dữ liệu kèm cột ghi chú Reviewer
    records = []
    default_status = "🔴 Chờ sửa" if lang == "vi" else "🔴 Pending Fix"
    col_frame = "Khung hình" if lang == "vi" else "Frame"
    col_obj = "Mã đối tượng" if lang == "vi" else "Object ID"
    col_class = "Lớp" if lang == "vi" else "Class"
    col_rule = "Mã Rule" if lang == "vi" else "Rule ID"
    col_sev = "Mức độ" if lang == "vi" else "Severity"
    col_desc = "Chi tiết vi phạm" if lang == "vi" else "Defect Detail"
    col_fix = "💡 Hướng dẫn sửa" if lang == "vi" else "💡 Recommended Fix"
    col_status = "Trạng thái" if lang == "vi" else "QC Status"
    col_rev = "Ghi chú Reviewer" if lang == "vi" else "Reviewer Note"

    for e in report.errors:
        k = f"{e.frame_name}_{e.object_id}_{e.rule_id}"
        n_entry = reviewer_notes.get(k) or reviewer_notes.get(e.object_id) or {}
        suggestion = RULE_SUGGESTIONS.get(e.rule_id, "Kiểm tra và sửa theo quy chuẩn BDD100K." if lang == "vi" else "Inspect and correct according to BDD100K standard.")
        records.append({
            col_frame: e.frame_name,
            col_obj: e.object_id,
            col_class: e.category,
            col_rule: e.rule_id,
            col_sev: e.severity,
            col_desc: e.message,
            col_fix: suggestion,
            col_status: n_entry.get("status", default_status),
            col_rev: n_entry.get("comment", ""),
        })
    df_errors = pd.DataFrame(records)

    # Bộ lọc tương tác (Mức độ, Rule, Class, Tìm kiếm)
    all_label = "Tất cả" if lang == "vi" else "All"
    fcol1, fcol2, fcol3, fcol4 = st.columns([2, 2.2, 2.2, 3.6])
    with fcol1:
        f_sev_lbl = "Lọc mức độ:" if lang == "vi" else "Filter Severity:"
        severity_filter = st.selectbox(f_sev_lbl, options=[all_label, "ERROR", "WARNING"], index=0)
    with fcol2:
        f_rule_lbl = "Lọc theo Rule:" if lang == "vi" else "Filter Rule:"
        rules_available = [all_label] + sorted(list(df_errors[col_rule].unique()))
        rule_filter = st.selectbox(f_rule_lbl, options=rules_available, index=0)
    with fcol3:
        f_class_lbl = "Lọc theo Lớp:" if lang == "vi" else "Filter Class:"
        classes_available = [all_label] + sorted(list(df_errors[col_class].unique()))
        class_filter = st.selectbox(f_class_lbl, options=classes_available, index=0)
    with fcol4:
        s_lbl = "🔍 Tìm kiếm nhanh:" if lang == "vi" else "🔍 Quick Search:"
        s_ph = "ID, frame, class, mô tả..." if lang == "vi" else "ID, frame, class, keywords..."
        search_text = st.text_input(s_lbl, "", placeholder=s_ph)

    filtered_df = df_errors.copy()
    if severity_filter != all_label:
        filtered_df = filtered_df[filtered_df[col_sev] == severity_filter]
    if rule_filter != all_label:
        filtered_df = filtered_df[filtered_df[col_rule] == rule_filter]
    if class_filter != all_label:
        filtered_df = filtered_df[filtered_df[col_class] == class_filter]
    if search_text:
        s = search_text.lower()
        filtered_df = filtered_df[
            filtered_df[col_frame].str.lower().str.contains(s) |
            filtered_df[col_obj].str.lower().str.contains(s) |
            filtered_df[col_class].str.lower().str.contains(s) |
            filtered_df[col_desc].str.lower().str.contains(s) |
            filtered_df[col_rev].str.lower().str.contains(s)
        ]

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            col_sev: st.column_config.TextColumn(col_sev, help="ERROR: Bắt buộc sửa | WARNING: Cần rà soát" if lang == "vi" else "ERROR: Must fix | WARNING: Review"),
            col_rule: st.column_config.TextColumn(col_rule),
            col_fix: st.column_config.TextColumn(col_fix, width="medium"),
            col_status: st.column_config.TextColumn(col_status, width="small"),
            col_rev: st.column_config.TextColumn(col_rev, width="medium"),
        }
    )

    showing_msg = (
        f"Đang hiển thị **{len(filtered_df)} / {total_issues}** vấn đề vi phạm."
        if lang == "vi"
        else f"Displaying **{len(filtered_df)} / {total_issues}** defect items."
    )
    st.caption(showing_msg)

    # -----------------------------------------------------------------------
    # NÚT XUẤT BÁO CÁO & TẬP NHÃN ĐÃ CHỮA LÀNH (EXPORT HUB)
    # -----------------------------------------------------------------------
    export_header = "##### 📥 Xuất Báo Cáo & Dữ Liệu Kiểm Duyệt Đa Định Dạng:" if lang == "vi" else "##### 📥 Export Multi-Format Reports & Remediated Datasets:"
    st.markdown(export_header)
    
    # Hàng 1: Báo cáo kiểm định QC
    st.caption("📊 " + ("Báo Cáo Kiểm Định QC:" if lang == "vi" else "QC Audit Reports:"))
    r1_col1, r1_col2 = st.columns(2)
    with r1_col1:
        csv_data = generate_csv_str(
            report,
            reviewer_notes=reviewer_notes,
            rule_suggestions=RULE_SUGGESTIONS,
        )
        csv_lbl = "📄 Tải Báo Cáo CSV" if lang == "vi" else "📄 Export CSV Report"
        csv_help = "File CSV có đủ mã lỗi, gợi ý sửa, ghi chú phê duyệt của Reviewer, mở tiếng Việt trên Excel không lỗi font" if lang == "vi" else "CSV report with defect codes, suggestions, and reviewer notes (UTF-8 BOM compatible with Excel)"
        st.download_button(
            label=csv_lbl,
            data=csv_data.encode("utf-8-sig"),
            file_name=f"qc_report_{Path(file_display_name).stem or file_display_name}.csv",
            mime="text/csv",
            use_container_width=True,
            help=csv_help,
        )

    with r1_col2:
        html_data = generate_html_str(report)
        html_lbl = "🌐 Báo Cáo HTML Độc Lập" if lang == "vi" else "🌐 Standalone HTML Report"
        html_help = "Báo cáo HTML Dashboard độc lập có tìm kiếm, bộ lọc và định dạng in PDF A4 chuyên nghiệp" if lang == "vi" else "Standalone interactive HTML report with dynamic search and print-ready A4 layout"
        st.download_button(
            label=html_lbl,
            data=html_data,
            file_name=f"qc_report_{Path(file_display_name).stem or file_display_name}.html",
            mime="text/html",
            use_container_width=True,
            help=html_help,
        )

    # Hàng 2: Các tập nhãn xuất theo từng frame (AnyLabeling / Labelme & BDD100K)
    st.caption("🏷️ " + ("Xuất Tệp JSON Từng Frame (Dành cho AnyLabeling, Labelme, Custom Tool):" if lang == "vi" else "Per-Frame JSON Datasets (For AnyLabeling, Labelme, Custom Tools):"))
    pf_col1, pf_col2 = st.columns(2)
    with pf_col1:
        try:
            anylabeling_zip_bytes = export_anylabeling_zip_bytes(frames)
            an_lbl = "🏷️ Tải ZIP JSON Từng Frame (Chuẩn AnyLabeling / Labelme)" if lang == "vi" else "🏷️ Download AnyLabeling Per-Frame JSONs (.zip)"
            an_help = "Tệp ZIP chứa các file {tên_ảnh}.json riêng lẻ theo chuẩn AnyLabeling. Giải nén vào cùng thư mục ảnh để mở và chỉnh sửa ngay trên AnyLabeling / Labelme!" if lang == "vi" else "ZIP containing individual {image_stem}.json files ready for AnyLabeling / Labelme"
            st.download_button(
                label=an_lbl,
                data=anylabeling_zip_bytes,
                file_name=f"anylabeling_frames_{Path(file_display_name).stem or file_display_name}.zip",
                mime="application/zip",
                use_container_width=True,
                help=an_help,
                key="tab1_export_anylabeling_zip",
            )
        except Exception:
            pass

    with pf_col2:
        try:
            bdd_zip_bytes = export_bdd100k_zip_bytes(frames)
            bdd_zip_lbl = "📦 Tải ZIP Từng Frame (Chuẩn BDD100K - Không dùng cho AnyLabeling)" if lang == "vi" else "📦 Download BDD100K Per-Frame JSONs (.zip)"
            bdd_zip_help = "Tệp ZIP chứa từng file {tên_ảnh}.json riêng lẻ theo chuẩn BDD100K (dạng danh sách [ ]). Chú ý: AnyLabeling không đọc được dạng này, hãy dùng nút [Chuẩn AnyLabeling / Labelme] bên cạnh!" if lang == "vi" else "ZIP containing individual {image_stem}.json files in BDD100K format"
            st.download_button(
                label=bdd_zip_lbl,
                data=bdd_zip_bytes,
                file_name=f"bdd100k_frames_{Path(file_display_name).stem or file_display_name}.zip",
                mime="application/zip",
                use_container_width=True,
                help=bdd_zip_help,
                key="tab1_export_bdd_zip",
            )
        except Exception:
            pass

    # Hàng 3: Các tập nhãn đã sửa định dạng chuẩn (BDD100K Toàn Bộ / COCO / YOLO / CVAT)
    st.caption("📦 " + ("Tập Nhãn Gộp & Đa Định Dạng (BDD100K Toàn Bộ / COCO / YOLO / CVAT XML):" if lang == "vi" else "Combined & Multi-Format Datasets:"))
    dcol1, dcol2, dcol3, dcol4 = st.columns(4)

    with dcol1:
        bdd_json_str = export_bdd100k_json(frames)
        bdd_lbl = "📄 BDD100K Gộp (.json)" if lang == "vi" else "📄 BDD100K Combined (.json)"
        bdd_help = "Xuất toàn bộ tập nhãn đã sửa vào 1 file JSON duy nhất theo chuẩn BDD100K" if lang == "vi" else "Export remediated dataset in a single combined BDD100K JSON file"
        st.download_button(
            label=bdd_lbl,
            data=bdd_json_str.encode("utf-8"),
            file_name=f"bdd100k_instances_{Path(file_display_name).stem or file_display_name}.json",
            mime="application/json",
            use_container_width=True,
            help=bdd_help,
            key="tab1_export_bdd_all",
        )

    with dcol2:
        coco_json_str = export_coco_json(frames)
        coco_lbl = "📦 COCO JSON" if lang == "vi" else "📦 COCO JSON"
        coco_help = "Xuất tập dữ liệu theo chuẩn COCO JSON dùng cho Detectron2 / MMDetection / YOLO" if lang == "vi" else "Export annotations in COCO JSON format for Detectron2 / MMDetection"
        st.download_button(
            label=coco_lbl,
            data=coco_json_str.encode("utf-8"),
            file_name=f"coco_instances_{Path(file_display_name).stem or file_display_name}.json",
            mime="application/json",
            use_container_width=True,
            help=coco_help,
            key="tab1_export_coco_all",
        )

    with dcol3:
        yolo_zip_bytes = export_yolo_zip_bytes(frames)
        yolo_lbl = "⚡ YOLO TXT (ZIP)" if lang == "vi" else "⚡ YOLO TXT (ZIP)"
        yolo_help = "Tải tệp ZIP chứa classes.txt và các file txt chuẩn YOLO để huấn luyện YOLOv8" if lang == "vi" else "Download ZIP archive containing normalized YOLO txt annotations and classes.txt"
        st.download_button(
            label=yolo_lbl,
            data=yolo_zip_bytes,
            file_name=f"yolo_labels_{Path(file_display_name).stem or file_display_name}.zip",
            mime="application/zip",
            use_container_width=True,
            help=yolo_help,
            key="tab1_export_yolo_zip",
        )

    with dcol4:
        try:
            cvat_xml_str = export_cvat_xml_str(frames)
            cvat_lbl = "🌐 CVAT XML" if lang == "vi" else "🌐 CVAT XML"
            cvat_help = "Xuất file XML chuẩn CVAT 1.1 để nạp trực tiếp vào CVAT Tool" if lang == "vi" else "Export annotations in CVAT XML 1.1 format"
            st.download_button(
                label=cvat_lbl,
                data=cvat_xml_str.encode("utf-8"),
                file_name=f"cvat_annotations_{Path(file_display_name).stem or file_display_name}.xml",
                mime="application/xml",
                use_container_width=True,
                help=cvat_help,
                key="tab1_export_cvat_xml",
            )
        except Exception:
            pass

    # Xem trước trực tiếp HTML Dashboard ngay trên app
    preview_lbl = "🌐 Xem trước Báo Cáo HTML Trực Quan" if lang == "vi" else "🌐 Interactive HTML Report Live Preview"
    with st.expander(preview_lbl, expanded=False):
        components.html(html_data, height=560, scrolling=True)

    # Bộ Công Cụ Tự Động Sửa Lỗi (1-Click Auto-Fix)
    autofix_exp_lbl = "🛠️ Bộ Công Cụ Tự Động Sửa Lỗi (1-Click Auto-Fix)" if lang == "vi" else "🛠️ Automated Remediation Engine (1-Click Auto-Fix)"
    with st.expander(autofix_exp_lbl, expanded=False):
        if lang == "vi":
            st.markdown("""
            **Thuật toán tự động khắc phục toàn diện các lỗi vi phạm:**
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
        else:
            st.markdown("""
            **Automated remediation algorithms for dataset defects:**
            - 📏 **Clamp BBox (B01):** Clamps overflowing bounding boxes back into image canvas bounds.
            - 🔄 **Invert Coords (B02):** Corrects inverted coordinates where $x_1 > x_2$ or $y_1 > y_2$.
            - 🗑️ **Zero-size Box (B02):** Prunes empty zero-area bounding boxes.
            - 📉 **Synthesize Poly (P01):** Generates 4-point bounding polygon for polygons with $< 3$ points.
            - 🎗️ **Unknot Poly (P02):** Resolves self-intersecting bowties using Shapely buffer operations.
            - 🎯 **Align Mask vs Box (P03):** Realigns bounding box tightly enclosing polygon bounds (IoU = 1.0).
            - 👥 **Duplicate Box (A01):** Deduplicates identical category boxes overlapping with IoU $> 0.85$.
            - 🏷️ **Missing Attributes (A02):** Imputes default attributes `occluded=False`, `truncated=False`.
            - 🚦 **Traffic Light Color (A03):** Normalizes invalid traffic light color attribute values to `none`.
            - 🔤 **Category Typos (C01):** Normalizes misspelled class labels to BDD100K ontology standards.
            """)

        all_missed_cache = st.session_state.get("qc_ai_missed_cache", {})
        total_missed_cnt = sum(len(items) for items in all_missed_cache.values())

        col_af1, col_af2 = st.columns([1, 1]) if total_missed_cnt > 0 else (st.container(), None)
        
        with col_af1:
            run_autofix_btn_lbl = "✨ Thực Thi Tự Động Sửa Lỗi" if lang == "vi" else "✨ Run Auto-Fix Engine"
            if st.button(run_autofix_btn_lbl, type="primary", key="btn_run_autofix", use_container_width=True):
                fixed_dataset, changelog, fix_stats = auto_correct_frames(frames)
                st.session_state["auto_fix_done"] = True
                st.session_state["auto_fix_data"] = fixed_dataset
                st.session_state["auto_fix_log"] = changelog
                st.session_state["auto_fix_stats"] = fix_stats
                st.rerun()

        if col_af2 is not None and total_missed_cnt > 0:
            with col_af2:
                btn_all_missed_lbl = f"⚡ Nạp Toàn Bộ Vật Thể Bỏ Sót ({total_missed_cnt})" if lang == "vi" else f"⚡ Ingest All Missed Objects ({total_missed_cnt})"
                if st.button(btn_all_missed_lbl, type="secondary", key="btn_autofix_all_missed", use_container_width=True):
                    with st.spinner("Đang nạp toàn bộ nhãn bỏ sót..." if lang == "vi" else "Ingesting all missed objects..."):
                        import time
                        from qc.models import LabeledObject, BBox2D
                        from qc.engine import run_qc
                        added_total = 0
                        for f_i, f in enumerate(frames):
                            f_missed = all_missed_cache.get(f.name, [])
                            for m_i, m_item in enumerate(f_missed):
                                mbx = m_item["box2d"]
                                mcat = m_item["category"]
                                new_id = f"missed_{mcat[:3]}_{int(time.time()*100)%10000}_{f_i+1}_{m_i+1}"
                                new_obj = LabeledObject(
                                    id=new_id,
                                    category=mcat,
                                    box2d=BBox2D(x1=mbx.x1, y1=mbx.y1, x2=mbx.x2, y2=mbx.y2),
                                    attributes={"occluded": False, "truncated": False},
                                )
                                f.objects.append(new_obj)
                                added_total += 1
                            all_missed_cache[f.name] = []
                        st.session_state["qc_ai_missed_cache"] = all_missed_cache
                        st.session_state["qc_report"] = run_qc(frames)
                        st.toast(f"🎉 Đã nạp thành công {added_total} đối tượng bỏ sót vào nhãn!", icon="⚡")
                        st.rerun()

        if st.session_state.get("auto_fix_done", False):
            fixed_data = st.session_state.get("auto_fix_data", [])
            logs = st.session_state.get("auto_fix_log", [])
            fix_stats = st.session_state.get("auto_fix_stats", {})
            done_msg = (
                f"🎉 Đã tự động xử lý và khắc phục thành công **{len(logs)} vị trí vi phạm**!"
                if lang == "vi"
                else f"🎉 Successfully corrected **{len(logs)} defect instances**!"
            )
            st.success(done_msg)

            # Hiển thị tóm tắt các hạng mục đã sửa
            if fix_stats:
                s_col1, s_col2, s_col3, s_col4 = st.columns(4)
                m1_lbl = "📏 Hộp BBox đã căn & đảo ngược" if lang == "vi" else "📏 Clamped & Inverted BBoxes"
                m2_lbl = "📉 Đa giác đã vá & khớp" if lang == "vi" else "📉 Healed & Aligned Polygons"
                m3_lbl = "👥 Đã lọc trùng & xóa rỗng" if lang == "vi" else "👥 Deduped & Pruned Objects"
                m4_lbl = "🏷️ Thuộc tính & Lỗi chính tả" if lang == "vi" else "🏷️ Imputed Attrs & Fixed Typos"
                s_col1.metric(m1_lbl, fix_stats.get("B01_clamped", 0) + fix_stats.get("B02_inverted", 0))
                s_col2.metric(m2_lbl, fix_stats.get("P01_synthesized", 0) + fix_stats.get("P02_unknotted", 0) + fix_stats.get("P03_aligned", 0))
                s_col3.metric(m3_lbl, fix_stats.get("A01_deduped", 0) + fix_stats.get("B02_zero_removed", 0))
                s_col4.metric(m4_lbl, fix_stats.get("A02_attrs_filled", 0) + fix_stats.get("A03_tl_normalized", 0) + fix_stats.get("C01_typo_fixed", 0))

            log_exp_lbl = "📝 Nhật ký chi tiết các mục đã sửa:" if lang == "vi" else "📝 Detailed Correction Changelog:"
            with st.expander(log_exp_lbl, expanded=True):
                for log_item in logs[:50]:
                    st.markdown(f"- `{log_item}`")
                if len(logs) > 50:
                    more_msg = f"... và {len(logs) - 50} mục khác." if lang == "vi" else f"... and {len(logs) - 50} more items."
                    st.caption(more_msg)

            fixed_json_bytes = json.dumps(fixed_data, indent=2, ensure_ascii=False).encode("utf-8")
            dl_clean_lbl = "💾 Tải Về Tệp BDD100K Đã Sửa Lỗi (JSON)" if lang == "vi" else "💾 Download Cleaned BDD100K JSON"
            st.download_button(
                label=dl_clean_lbl,
                data=fixed_json_bytes,
                file_name=f"bdd100k_cleaned_{file_display_name}.json",
                mime="application/json",
                use_container_width=True,
            )
