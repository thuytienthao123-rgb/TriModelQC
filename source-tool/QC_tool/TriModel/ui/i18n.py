"""
i18n.py — Hệ thống đa ngôn ngữ (Tiếng Việt & English) cho BDD-QC Tool.
Đảm bảo giao diện 100% thuần Tiếng Việt hoặc 100% thuần Tiếng Anh, không đan xen.
"""

from __future__ import annotations
from typing import Dict, Any
import streamlit as st

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # Header
    "header_pre": {
        "vi": "HỆ THỐNG KIỂM SOÁT CHẤT LƯỢNG // QUY TRÌNH AN TOÀN",
        "en": "QUALITY ASSURANCE SUITE // AUDIT RUNTIME",
    },
    "header_title": {
        "vi": "HỆ THỐNG KIỂM ĐỊNH CHẤT LƯỢNG NHÃN",
        "en": "BDD100K QUALITY CONTROL WORKSPACE",
    },
    "header_sub": {
        "vi": "Bộ công cụ tự động kiểm toán không gian hình học, cấu trúc đa giác và đối soát AI · Dự án N2-04A",
        "en": "Automated Spatial Linter, Polygon Topology Audit & Defect Remediation Engine · Project N2-04A",
    },
    "tag_online": {
        "vi": "HỆ THỐNG TRỰC TUYẾN",
        "en": "AUDIT RUNTIME ONLINE",
    },
    "tag_spec": {
        "vi": "QUY CHUẨN: BDD100K / N2-04A",
        "en": "SPEC: BDD100K / N2-04A",
    },
    "tag_rules": {
        "vi": "{count} BỘ LUẬT ĐÃ NẠP",
        "en": "{count} RULES LOADED",
    },
    "tag_ai_active": {
        "vi": "● TRỢ LÝ AI YOLOV8 ĐANG BẬT",
        "en": "● YOLOV8 AI ACTIVE",
    },
    "tag_ai_offline": {
        "vi": "○ TRỢ LÝ AI ĐANG TẮT",
        "en": "○ AI OFFLINE",
    },

    # Welcome Screen
    "welcome_title": {
        "vi": "📋 Sẵn sàng kiểm tra chất lượng dữ liệu nhãn",
        "en": "📋 Ready for Data Quality Inspection",
    },
    "welcome_desc": {
        "vi": "Hệ thống đã nhận diện cấu trúc tệp nhãn thành công. Bấm nút bên dưới để tiến hành kiểm tra tự động qua 15 bộ luật và đối soát AI.",
        "en": "Dataset structure verified. Click the button below to start automated audit across 15 rules and AI consensus check.",
    },
    "btn_start_audit": {
        "vi": "🚀 BẮT ĐẦU KIỂM TRA",
        "en": "🚀 START AUDIT",
    },
    "btn_reload_welcome": {
        "vi": "🔄 TẢI LẠI TRANG",
        "en": "🔄 RELOAD",
    },

    # Sidebar
    "lang_label": {
        "vi": "🌐 Ngôn ngữ:",
        "en": "🌐 Language:",
    },
    "sec_source": {
        "vi": "📂 1. Nguồn Dữ Liệu",
        "en": "📂 1. Data Source",
    },
    "source_mode": {
        "vi": "Chọn phương thức nạp dữ liệu:",
        "en": "Select data ingestion mode:",
    },
    "opt_sample": {
        "vi": "⚡ Dùng dữ liệu mẫu",
        "en": "⚡ Use Sample Dataset",
    },
    "opt_upload": {
        "vi": "📂 Tải file",
        "en": "📂 Upload Files",
    },
    "opt_folder": {
        "vi": "🗂️ Tải thư mục",
        "en": "🗂️ Upload Folder",
    },
    "sample_select": {
        "vi": "Chọn tệp dữ liệu mẫu:",
        "en": "Choose sample file:",
    },
    "sample_err": {
        "vi": "🔴 sample_with_errors.json (7 lỗi vi phạm)",
        "en": "🔴 sample_with_errors.json (7 sample defects)",
    },
    "sample_val": {
        "vi": "🟢 sample_valid.json (Bộ nhãn chuẩn quy cách)",
        "en": "🟢 sample_valid.json (100% verified labels)",
    },
    "upload_label": {
        "vi": "Chọn các tệp nhãn (giữ Ctrl/Cmd để chọn nhiều tệp):",
        "en": "Select label files (hold Ctrl/Cmd to multi-select):",
    },
    "btn_reset_labels": {
        "vi": "🔄 Đổi tệp nhãn khác",
        "en": "🔄 Reset / Change Labels",
    },
    "folder_label": {
        "vi": "Đường dẫn thư mục chứa nhãn:",
        "en": "Folder path containing labels:",
    },
    "btn_scan": {
        "vi": "🔍 Quét thư mục",
        "en": "🔍 Scan Folder",
    },
    "sec_canvas": {
        "vi": "📐 2. Khung Hình & Ảnh Gốc",
        "en": "📐 2. Canvas & Source Images",
    },
    "canvas_res_label": {
        "vi": "Độ phân giải khung hình:",
        "en": "Canvas Resolution:",
    },
    "upload_images_label": {
        "vi": "Tải ảnh gốc tương ứng (Tùy chọn):",
        "en": "Upload source images (Optional):",
    },
    "btn_reset_images": {
        "vi": "🔄 Đổi bộ ảnh khác / Tải lại",
        "en": "🔄 Clear / Select Other Images",
    },
    "images_loaded_msg": {
        "vi": "✅ Đã nạp {count} ảnh minh họa",
        "en": "✅ Loaded {count} source images",
    },
    "sec_rules": {
        "vi": "🎯 3. Bộ Luật Kiểm Tra",
        "en": "🎯 3. Quality Rules",
    },
    "btn_view_rules": {
        "vi": "📖 Xem chi tiết 15 bộ luật",
        "en": "📖 View All 15 Rules Spec",
    },
    "rule_bbox_lbl": {
        "vi": "Hộp bao giới hạn (B01 - B05)",
        "en": "Bounding Box Geometry (B01 - B05)",
    },
    "rule_bbox_help": {
        "vi": "B01: Tràn viền | B02: Tọa độ âm | B03: Kích thước siêu nhỏ (<64px²) | B04: Dẹt bất thường (>25:1) | B05: Chiếm toàn màn hình (>96%)",
        "en": "B01: Boundary Overflow | B02: Inverted Coords | B03: Tiny Box (<64px²) | B04: Extreme Aspect Ratio (>25:1) | B05: Fullscreen Box (>96%)",
    },
    "rule_poly_lbl": {
        "vi": "Đa giác phân đoạn (P01 - P04)",
        "en": "Polygon Segmentation (P01 - P04)",
    },
    "rule_poly_help": {
        "vi": "P01: Dưới 3 đỉnh | P02: Tự cắt chéo nơ | P03: Lệch khung bao | P04: Đỉnh trùng/Gấp khúc dị thường",
        "en": "P01: Less than 3 points | P02: Self-intersecting | P03: BBox Mismatch | P04: Duplicate Points / Sharp Kinks",
    },
    "rule_attr_lbl": {
        "vi": "Thuộc tính & Phân loại (A01 - A03, C01)",
        "en": "Attributes & Categories (A01 - A03, C01)",
    },
    "rule_attr_help": {
        "vi": "A01: Vẽ trùng lặp 2 hộp | A02: Thiếu thuộc tính che khuất/cắt xén | A03: Thiếu màu đèn giao thông | C01: Sai danh mục chuẩn BDD100K",
        "en": "A01: Duplicate Boxes | A02: Missing occluded/truncated | A03: Traffic light color | C01: Standard Category Mismatch",
    },
    "rule_seq_lbl": {
        "vi": "Chuỗi khung hình liên tục (T01 - T02)",
        "en": "Video Sequence Tracking (T01 - T02)",
    },
    "rule_seq_help": {
        "vi": "T01: Mất dấu ngắt quãng | T02: Nhảy tọa độ giật đột ngột giữa 2 frame liên tiếp",
        "en": "T01: Tracking Lost (Flicker) | T02: Unrealistic Displacement Jump",
    },
    "rules_active_summary": {
        "vi": "Đang kích hoạt: **{active} / {total} bộ luật**",
        "en": "Active: **{active} / {total} rules loaded**",
    },
    "sec_ai": {
        "vi": "🤖 4. Trợ Lý AI Soi Bỏ Sót",
        "en": "🤖 4. AI False-Negative Assistant",
    },
    "ai_enable_lbl": {
        "vi": "Bật AI soi xe và người bị bỏ sót",
        "en": "Enable AI Detection for Missed Objects",
    },
    "ai_conf_lbl": {
        "vi": "Độ nhạy AI:",
        "en": "AI Sensitivity (Confidence):",
    },
    "ai_mode_lbl": {
        "vi": "Chế độ đồng thuận AI:",
        "en": "AI Consensus Mode:",
    },
    "ai_mode_majority": {
        "vi": "Đa số (2/3) - Bắt trọn xe xa",
        "en": "Majority (2/3) - High Recall",
    },
    "ai_mode_strict": {
        "vi": "Tuyệt đối (3/3) - Nghiêm ngặt",
        "en": "Strict (3/3) - High Precision",
    },
    "sec_control": {
        "vi": "🚀 5. Điều Khiển Kiểm Tra",
        "en": "🚀 5. Execution Controls",
    },
    "btn_checking": {
        "vi": "🚀 Bắt Đầu Kiểm Tra",
        "en": "🚀 Run Audit",
    },
    "btn_reload_sidebar": {
        "vi": "🔄 Tải Lại",
        "en": "🔄 Reset",
    },

    # KPI Dashboard
    "kpi_frames": {
        "vi": "TỔNG SỐ KHUNG HÌNH",
        "en": "TOTAL FRAMES",
    },
    "kpi_frames_sub": {
        "vi": "Khung hình đã phân tích",
        "en": "Frames analyzed",
    },
    "kpi_objects": {
        "vi": "TỔNG SỐ VẬT THỂ",
        "en": "TOTAL INSTANCES",
    },
    "kpi_objects_sub": {
        "vi": "Đối tượng gán nhãn",
        "en": "Annotated objects",
    },
    "kpi_errors": {
        "vi": "LỖI NGHIÊM TRỌNG",
        "en": "CRITICAL DEFECTS",
    },
    "kpi_errors_sub": {
        "vi": "Vi phạm cần sửa ngay",
        "en": "Must-fix violations",
    },
    "kpi_warnings": {
        "vi": "CẢNH BÁO",
        "en": "WARNINGS",
    },
    "kpi_warnings_sub": {
        "vi": "Cần xem xét đối chiếu",
        "en": "Suspicious items",
    },
    "kpi_health": {
        "vi": "ĐỘ CHUẨN XÁC",
        "en": "QUALITY SCORE",
    },
    "kpi_health_sub": {
        "vi": "Tỉ lệ dữ liệu đạt chuẩn",
        "en": "Compliance rate",
    },

    # Verdict
    "verdict_pass_title": {
        "vi": "✅ BỘ DỮ LIỆU ĐẠT CHUẨN NGHIỆM THU",
        "en": "✅ DATASET ACCEPTED FOR DEPLOYMENT",
    },
    "verdict_pass_desc": {
        "vi": "Không phát hiện lỗi nghiêm trọng. Dữ liệu nhãn đáp ứng hoàn toàn quy chuẩn BDD100K.",
        "en": "No critical defects detected. The annotations strictly comply with BDD100K specifications.",
    },
    "verdict_fail_title": {
        "vi": "❌ TỪ CHỐI NGHIỆM THU — CẦN KHẮC PHỤC LỖI",
        "en": "❌ REJECTED — DEFECT REMEDIATION REQUIRED",
    },
    "verdict_fail_desc": {
        "vi": "Phát hiện {count} lỗi nghiêm trọng cần xử lý trước khi xuất dữ liệu sang mô hình huấn luyện.",
        "en": "Found {count} critical defects that must be resolved prior to training pipeline export.",
    },

    # Tabs
    "tab_defects": {
        "vi": "📋 Danh Mục Lỗi ({count})",
        "en": "📋 Defect Catalog ({count})",
    },
    "tab_visual": {
        "vi": "🖼️ Soi Nhãn Trực Quan",
        "en": "🖼️ Visual Workspace",
    },
    "tab_analytics": {
        "vi": "📊 Thống Kê & Phân Tích",
        "en": "📊 Quality Telemetry",
    },
    "tab_docs": {
        "vi": "📖 Đặc Tả 15 Quy Tắc",
        "en": "📖 Rules Specification",
    },
}


def get_current_lang() -> str:
    """Lấy ngôn ngữ hiện tại trong session (mặc định 'vi')."""
    return st.session_state.get("qc_lang", "vi")


def set_current_lang(lang: str) -> None:
    """Thiết lập ngôn ngữ hiện tại ('vi' hoặc 'en')."""
    if lang in ("vi", "en"):
        st.session_state["qc_lang"] = lang


def t(key: str, **kwargs: Any) -> str:
    """Lấy chuỗi dịch theo key và ngôn ngữ hiện tại."""
    lang = get_current_lang()
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key
    text = entry.get(lang, entry.get("vi", key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
