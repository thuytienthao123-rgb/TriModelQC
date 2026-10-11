"""
app.py — Giao diện Web tương tác Streamlit cho BDD-QC Tool (Mã đề: N2-04A).
Hỗ trợ kiểm tra chất lượng Bounding Box & Polygon 2D trên dataset BDD100K.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image

from qc.models import ERROR, WARNING, FrameData, QCError, QCReport
from qc.parser import parse_bdd100k_text, load_bdd100k
from qc.engine import run_qc, DEFAULT_RULES
from qc.rules.bbox_rules import ALL_BBOX_RULES
from qc.rules.polygon_rules import ALL_POLYGON_RULES
from qc.rules.attribute_rules import ALL_ATTRIBUTE_RULES
from qc.reporter import generate_csv_str, generate_html_str


# ---------------------------------------------------------------------------
# Cấu hình giao diện Streamlit
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="BDD100K QC Tool (N2-04A)",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS cho giao diện hiện đại
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #94a3b8;
        margin-bottom: 1.2rem;
    }
    .metric-card {
        background-color: #1e293b;
        border-radius: 10px;
        padding: 15px 20px;
        border-left: 4px solid #38bdf8;
    }
    .badge-err {
        background-color: #ef4444;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-warn {
        background-color: #f59e0b;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar: Nguồn dữ liệu & Cấu hình Rule
# ---------------------------------------------------------------------------
st.sidebar.image("https://img.shields.io/badge/QC_Tool-N2--04A-blue?style=for-the-badge", use_container_width=True)
st.sidebar.title("⚙️ Cấu hình QC")

# 1. Chọn nguồn dữ liệu
data_source = st.sidebar.radio(
    "Nguồn file nhãn BDD100K:",
    options=["⚡ Dùng dữ liệu mẫu (sample_with_errors.json)", "📁 Tải lên file JSON mới"],
    index=0,
)

raw_json_str = None
file_display_name = ""

SAMPLE_PATH = Path(__file__).parent / "data_sample" / "sample_with_errors.json"

if data_source == "⚡ Dùng dữ liệu mẫu (sample_with_errors.json)":
    if SAMPLE_PATH.exists():
        raw_json_str = SAMPLE_PATH.read_text(encoding="utf-8")
        file_display_name = "data_sample/sample_with_errors.json"
        st.sidebar.success("✅ Đã nạp file mẫu sẵn có")
    else:
        st.sidebar.error("Không tìm thấy file sample_with_errors.json")
else:
    uploaded_file = st.sidebar.file_uploader("Chọn file JSON BDD100K hoặc CVAT export:", type=["json"])
    if uploaded_file is not None:
        raw_json_str = uploaded_file.getvalue().decode("utf-8")
        file_display_name = uploaded_file.name
        st.sidebar.success(f"✅ Đã tải: {uploaded_file.name}")

# Tải ảnh minh họa (tùy chọn)
uploaded_image = st.sidebar.file_uploader("🖼️ Tải ảnh minh họa gốc (Tùy chọn):", type=["jpg", "jpeg", "png"])

# 2. Bộ lọc Rules
st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Chọn bộ luật kiểm tra")

enable_bbox = st.sidebar.checkbox("Kiểm tra Bounding Box (B01 - B04)", value=True)
enable_poly = st.sidebar.checkbox("Kiểm tra Polygon (P01 - P03)", value=True)
enable_attr = st.sidebar.checkbox("Kiểm tra Thuộc tính & Trùng lặp (A01 - A03)", value=True)

active_rules = []
if enable_bbox:
    active_rules.extend(ALL_BBOX_RULES)
if enable_poly:
    active_rules.extend(ALL_POLYGON_RULES)
if enable_attr:
    active_rules.extend(ALL_ATTRIBUTE_RULES)

st.sidebar.info(f"Đang kích hoạt: **{len(active_rules)} / 10 rules**")

# Thông tin nhóm
st.sidebar.markdown("---")
st.sidebar.caption("👥 **Nhóm thực hiện (N2-04A):**")
st.sidebar.caption("• Đào Ngọc Hiếu (Leader / Pipeline)\n• Đoàn Văn Thắng (Parser & Data)\n• Nguyễn Thanh Đức (BBox Rules)\n• Hoàng Công Chứ (Poly Rules)\n• Trần Thị Thủy Tiên (Attr Rules)")


# ---------------------------------------------------------------------------
# Main Content
# ---------------------------------------------------------------------------
st.markdown('<div class="main-header">🛡️ BDD100K 2D Annotation Quality Control</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Hệ thống Linter & Kiểm tra chất lượng gán nhãn tự động dành cho Annotator & Reviewer (Mã đề: N2-04A)</div>', unsafe_allow_html=True)

if not raw_json_str:
    st.info("👈 Vui lòng chọn hoặc tải lên file JSON ở thanh bên trái để bắt đầu kiểm tra.")
    st.stop()

# Parse JSON
try:
    frames = parse_bdd100k_text(raw_json_str)
except Exception as e:
    st.error(f"❌ Lỗi khi đọc file JSON: {e}")
    st.stop()

# Thực thi QC Engine
report = run_qc(frames, rules=active_rules)

# ---------------------------------------------------------------------------
# Thẻ Thống kê KPI tóm tắt
# ---------------------------------------------------------------------------
col1, col2, col3, col4, col5 = st.columns(5)

total_issues = len(report.errors)
pass_rate = 100.0 if report.total_objects == 0 else max(0.0, 100.0 - (total_issues / report.total_objects * 100))

col1.metric("🖼️ Tổng số Frame", f"{report.total_frames:,}")
col2.metric("🎯 Tổng số Object", f"{report.total_objects:,}")
col3.metric("❌ Số lỗi (ERROR)", f"{report.error_count():,}", delta=f"-{report.error_count()}" if report.error_count() > 0 else "0", delta_color="inverse")
col4.metric("⚠️ Cảnh báo (WARN)", f"{report.warning_count():,}", delta=f"-{report.warning_count()}" if report.warning_count() > 0 else "0", delta_color="inverse")
col5.metric("📈 Tỷ lệ đạt chuẩn", f"{pass_rate:.1f}%", delta=f"{pass_rate:.1f}%")

st.markdown("---")

# ---------------------------------------------------------------------------
# Tabs hiển thị kết quả
# ---------------------------------------------------------------------------
tab_list, tab_visual, tab_charts, tab_docs = st.tabs([
    "📋 Danh sách lỗi phát hiện",
    "🖼️ Visualizer (Trực quan hóa Box lỗi)",
    "📊 Thống kê & Phân tích",
    "📖 Hướng dẫn & Quy chuẩn 10 Rules",
])

# ---------------------------------------------------------------------------
# TAB 1: Danh sách lỗi
# ---------------------------------------------------------------------------
with tab_list:
    st.subheader(f"Danh sách vi phạm ({total_issues} vấn đề)")

    if total_issues == 0:
        st.success("🎉 Xuất sắc! File nhãn hoàn toàn sạch sẽ, không có lỗi hay cảnh báo nào.")
    else:
        # Chuyển đổi thành DataFrame để lọc linh hoạt
        records = []
        for e in report.errors:
            records.append({
                "Frame": e.frame_name,
                "Object ID": e.object_id,
                "Class": e.category,
                "Rule": e.rule_id,
                "Mức độ": e.severity,
                "Chi tiết lỗi": e.message,
            })
        df_errors = pd.DataFrame(records)

        # Thanh công cụ lọc
        fcol1, fcol2, fcol3 = st.columns([2, 2, 4])
        with fcol1:
            severity_filter = st.selectbox("Lọc mức độ:", options=["Tất cả", "ERROR", "WARNING"], index=0)
        with fcol2:
            rules_available = ["Tất cả"] + sorted(list(df_errors["Rule"].unique()))
            rule_filter = st.selectbox("Lọc theo Rule:", options=rules_available, index=0)
        with fcol3:
            search_text = st.text_input("🔍 Tìm kiếm (theo frame, class, object ID...):", "")

        # Áp dụng bộ lọc
        filtered_df = df_errors.copy()
        if severity_filter != "Tất cả":
            filtered_df = filtered_df[filtered_df["Mức độ"] == severity_filter]
        if rule_filter != "Tất cả":
            filtered_df = filtered_df[filtered_df["Rule"] == rule_filter]
        if search_text:
            s = search_text.lower()
            filtered_df = filtered_df[
                filtered_df["Frame"].str.lower().str.contains(s) |
                filtered_df["Object ID"].str.lower().str.contains(s) |
                filtered_df["Class"].str.lower().str.contains(s) |
                filtered_df["Chi tiết lỗi"].str.lower().str.contains(s)
            ]

        # Hiển thị bảng
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Mức độ": st.column_config.TextColumn(
                    "Mức độ",
                    help="ERROR: Bắt buộc sửa | WARNING: Cần kiểm tra lại",
                ),
                "Rule": st.column_config.TextColumn(
                    "Mã Rule",
                    help="Mã quy tắc vi phạm",
                ),
            }
        )

        st.caption(f"Đang hiển thị {len(filtered_df)} / {total_issues} vấn đề.")

        # Nút xuất báo cáo
        st.markdown("##### 📥 Tải xuống báo cáo QC:")
        dcol1, dcol2, _ = st.columns([2, 2, 6])
        with dcol1:
            csv_data = generate_csv_str(report)
            st.download_button(
                label="📄 Tải Báo cáo CSV",
                data=csv_data,
                file_name=f"qc_report_{Path(file_display_name).stem}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with dcol2:
            html_data = generate_html_str(report)
            st.download_button(
                label="🌐 Tải Báo cáo HTML Dashboard",
                data=html_data,
                file_name=f"qc_report_{Path(file_display_name).stem}.html",
                mime="text/html",
                use_container_width=True,
            )

# ---------------------------------------------------------------------------
# TAB 2: Visualizer (Trực quan hóa Box lỗi trên Canvas)
# ---------------------------------------------------------------------------
with tab_visual:
    st.subheader("Trực quan hóa Bounding Box & Polygon bị lỗi")
    st.caption("Khung viền đỏ: Lỗi nghiêm trọng (ERROR) | Khung vàng: Cảnh báo (WARNING) | Khung xanh: Hợp lệ")

    frame_names = [f.name for f in frames]
    selected_frame_name = st.selectbox("Chọn frame cần soi:", options=frame_names, index=0)

    selected_frame = next((f for f in frames if f.name == selected_frame_name), None)

    if selected_frame:
        # Tìm các lỗi ứng với frame này
        frame_errors: Dict[str, List[QCError]] = {}
        for err in report.errors:
            if err.frame_name == selected_frame_name:
                # Có thể object_id có dạng 'obj_a & obj_b'
                for oid in [x.strip() for x in err.object_id.split("&")]:
                    frame_errors.setdefault(oid, []).append(err)

        # Vẽ hình bằng matplotlib
        fig, ax = plt.subplots(figsize=(12, 6.75), dpi=100)
        canvas_w = selected_frame.width
        canvas_h = selected_frame.height

        # Nền canvas hoặc ảnh thực tế
        if uploaded_image:
            try:
                img = Image.open(uploaded_image).convert("RGB")
                ax.imshow(img)
            except Exception:
                ax.imshow([[0]], extent=[0, canvas_w, canvas_h, 0], cmap="gray", aspect="auto")
        else:
            # Tạo nền đen/tối giả lập khung hình 1280x720
            ax.set_facecolor("#0f172a")
            ax.set_xlim(0, canvas_w)
            ax.set_ylim(canvas_h, 0)  # Gốc (0,0) ở góc trên bên trái chuẩn CV

        # Vẽ từng object
        for obj in selected_frame.objects:
            obj_errs = frame_errors.get(obj.id, [])
            has_error = any(e.is_error() for e in obj_errs)
            has_warn = any(e.is_warning() for e in obj_errs)

            if has_error:
                edge_color = "#ef4444"  # Đỏ
                label_color = "#fee2e2"
                status_txt = "[ERR]"
            elif has_warn:
                edge_color = "#f59e0b"  # Vàng
                label_color = "#fef3c7"
                status_txt = "[WARN]"
            else:
                edge_color = "#22c55e"  # Xanh lá
                label_color = "#dcfce7"
                status_txt = "[OK]"

            # Vẽ Box2D
            if obj.box2d:
                bx = obj.box2d
                # Clamping nhẹ để hiển thị nếu out-of-bounds
                rect = patches.Rectangle(
                    (bx.x1, bx.y1),
                    bx.width,
                    bx.height,
                    linewidth=2.2 if (has_error or has_warn) else 1.2,
                    edgecolor=edge_color,
                    facecolor="none",
                    linestyle="--" if (has_error or has_warn) else "-",
                )
                ax.add_patch(rect)

                tag = f"{status_txt} {obj.id}: {obj.category}"
                ax.text(
                    max(5, bx.x1),
                    max(18, bx.y1 - 5),
                    tag,
                    color=edge_color,
                    fontsize=8,
                    weight="bold",
                    bbox=dict(facecolor="#1e293b", edgecolor=edge_color, boxstyle="round,pad=0.2", alpha=0.85),
                )

            # Vẽ Polygon
            if obj.poly2d and obj.poly2d.vertices:
                pts = obj.poly2d.vertices
                poly_patch = patches.Polygon(
                    pts,
                    closed=True,
                    linewidth=2.2 if has_error else 1.5,
                    edgecolor=edge_color,
                    facecolor=edge_color,
                    alpha=0.25,
                    linestyle=":" if has_error else "-",
                )
                ax.add_patch(poly_patch)
                ax.text(
                    pts[0][0],
                    pts[0][1],
                    f"{status_txt} {obj.id} (poly)",
                    color=edge_color,
                    fontsize=8,
                    weight="bold",
                    bbox=dict(facecolor="#1e293b", edgecolor=edge_color, boxstyle="round,pad=0.2", alpha=0.85),
                )

        ax.set_title(f"Khung hình: {selected_frame_name} ({len(selected_frame.objects)} objects)", color="white", fontsize=11)
        ax.set_xticks(range(0, canvas_w + 1, 200))
        ax.set_yticks(range(0, canvas_h + 1, 100))
        ax.tick_params(colors="#94a3b8", labelsize=8)
        for spine in ax.spines.values():
            spine.set_color("#334155")
        fig.tight_layout()

        st.pyplot(fig)

        # Hiển thị các lỗi cụ thể của Frame này
        cur_errs = [e for e in report.errors if e.frame_name == selected_frame_name]
        if cur_errs:
            st.markdown(f"**Danh sách vấn đề trong frame `{selected_frame_name}`:**")
            for e in cur_errs:
                icon = "❌" if e.is_error() else "⚠️"
                st.markdown(f"- {icon} **`{e.object_id}`** (`{e.category}`) | `{e.rule_id}`: {e.message}")
        else:
            st.success("Frame này hoàn toàn hợp lệ!")

# ---------------------------------------------------------------------------
# TAB 3: Biểu đồ & Thống kê
# ---------------------------------------------------------------------------
with tab_charts:
    st.subheader("Phân tích chất lượng dữ liệu")

    if total_issues == 0:
        st.info("Không có dữ liệu lỗi để vẽ biểu đồ.")
    else:
        ccol1, ccol2 = st.columns(2)

        with ccol1:
            st.markdown("##### 📌 Phân bố lỗi theo Rule")
            rule_counts = pd.Series([e.rule_id for e in report.errors]).value_counts()
            fig_r, ax_r = plt.subplots(figsize=(6, 4))
            ax_r.set_facecolor("#1e293b")
            fig_r.patch.set_facecolor("#0f172a")
            bars = ax_r.bar(rule_counts.index, rule_counts.values, color="#38bdf8")
            ax_r.set_ylabel("Số lượng lỗi", color="#94a3b8")
            ax_r.tick_params(colors="#e2e8f0")
            for spine in ax_r.spines.values():
                spine.set_color("#334155")
            for bar in bars:
                yval = bar.get_height()
                ax_r.text(bar.get_x() + bar.get_width()/2.0, yval + 0.1, int(yval), ha="center", va="bottom", color="#7dd3fc", weight="bold")
            fig_r.tight_layout()
            st.pyplot(fig_r)

        with ccol2:
            st.markdown("##### 🚗 Phân bố lỗi theo Loại nhãn (Category)")
            cat_counts = pd.Series([e.category for e in report.errors]).value_counts()
            fig_c, ax_c = plt.subplots(figsize=(6, 4))
            ax_c.set_facecolor("#1e293b")
            fig_c.patch.set_facecolor("#0f172a")
            bars_c = ax_c.bar(cat_counts.index, cat_counts.values, color="#f472b6")
            ax_c.set_ylabel("Số lượng lỗi", color="#94a3b8")
            ax_c.tick_params(colors="#e2e8f0", rotation=25)
            for spine in ax_c.spines.values():
                spine.set_color("#334155")
            for bar in bars_c:
                yval = bar.get_height()
                ax_c.text(bar.get_x() + bar.get_width()/2.0, yval + 0.1, int(yval), ha="center", va="bottom", color="#fbcfe8", weight="bold")
            fig_c.tight_layout()
            st.pyplot(fig_c)

        # Bảng tổng hợp theo Rule
        st.markdown("##### 📋 Bảng tần suất lỗi theo Rule:")
        summary_rows = []
        for r_id in sorted(list(set(e.rule_id for e in report.errors))):
            errs_r = [e for e in report.errors if e.rule_id == r_id]
            err_c = sum(1 for e in errs_r if e.is_error())
            warn_c = sum(1 for e in errs_r if e.is_warning())
            summary_rows.append({
                "Mã Rule": r_id,
                "Tổng số lần": len(errs_r),
                "ERROR": err_c,
                "WARNING": warn_c,
            })
        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# TAB 4: Hướng dẫn & Quy chuẩn 10 Rules
# ---------------------------------------------------------------------------
with tab_docs:
    st.subheader("Quy chuẩn 10 Rules kiểm tra chất lượng BDD100K")
    st.markdown("""
| Nhóm | Mã Rule | Tên quy tắc | Mô tả chi tiết | Mức độ | Cách khắc phục |
|---|---|---|---|---|---|
| **BBox** | `RULE_B01` | **Out of Bounds** | Tọa độ box vượt ra ngoài khung hình (x<0, y<0, x>1280, y>720) | 🔴 ERROR | Kéo box nằm trọn trong giới hạn ảnh |
| **BBox** | `RULE_B02` | **Inverted / Zero Box** | Tọa độ bị đảo ngược ($x_2 \le x_1$ hoặc $y_2 \le y_1$) hoặc $w, h = 0$ | 🔴 ERROR | Xóa box chấm lỗi hoặc vẽ lại |
| **BBox** | `RULE_B03` | **Too Small Box** | Diện tích $w \times h < 64\\text{px}^2$, nghi ngờ chấm nhầm/nhiễu | 🟡 WARN | Kiểm tra vật thể có thật sự nhận diện được không |
| **BBox** | `RULE_B04` | **Abnormal Ratio** | Tỉ lệ khung hình dị thường ($w/h > 25$ hoặc $h/w > 25$) | 🟡 WARN | Kiểm tra lại viền box bị kéo dài quá mức |
| **Poly** | `RULE_P01` | **Insufficient Vertices** | Đa giác polygon có ít hơn 3 đỉnh | 🔴 ERROR | Bổ sung thêm đỉnh hoặc xóa polygon hỏng |
| **Poly** | `RULE_P02` | **Self-Intersection** | Đa giác bị xoắn nơ, vắt chéo viền (tự cắt chính nó) | 🔴 ERROR | Nắn chỉnh các đỉnh để đường viền không cắt nhau |
| **Poly** | `RULE_P03` | **Mask vs Box Mismatch** | Khung bao polygon lệch quá nhiều so với BBox (IoU < 0.7) | 🟡 WARN | Điều chỉnh lại BBox hoặc viền polygon khớp nhau |
| **Attr** | `RULE_A01` | **Duplicate Object** | Hai box cùng class đè lên nhau với IoU > 0.85 (vẽ trùng lặp) | 🔴 ERROR | Xóa bớt 1 box bị vẽ đè |
| **Attr** | `RULE_A02` | **Missing Attributes** | Thiếu thuộc tính bắt buộc (`occluded`, `truncated`) | 🟡 WARN | Điền đầy đủ thuộc tính trong bảng thuộc tính CVAT |
| **Attr** | `RULE_A03` | **Traffic Light Color** | Vật thể `traffic light` nhưng sai màu hoặc thiếu màu | 🔴 ERROR | Chọn đúng màu đèn: `red`, `green`, `yellow`, `none` |
    """)
