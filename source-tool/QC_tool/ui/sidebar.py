from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from PIL import Image
import streamlit as st

from qc.models import FrameData
from qc.parser import load_bdd100k
from qc.rules.bbox_rules import ALL_BBOX_RULES
from qc.rules.polygon_rules import ALL_POLYGON_RULES
from qc.rules.attribute_rules import ALL_ATTRIBUTE_RULES
from qc.rules.sequence_rules import ALL_SEQUENCE_RULES

from ui.io_utils import find_matching_image, read_file_bytes, scan_folder


def render_sidebar(ai_model: Any) -> Dict[str, Any]:
    """Render thanh công cụ bên trái (Sidebar) và trả về cấu hình phiên làm việc."""
    # 1. Khối thương hiệu/logo đưa lên vị trí trên cùng của Sidebar
    st.sidebar.markdown("""
    <div class="sidebar-brand-card">
        <div class="sidebar-brand-icon">🛡️</div>
        <div>
            <h3 class="sidebar-brand-title">BDD-QC Suite</h3>
            <p class="sidebar-brand-sub">2D Annotation Quality Control</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1. Nguồn Dữ Liệu
    st.sidebar.subheader("📂 1. Nguồn Dữ Liệu")
    data_source = st.sidebar.radio(
        "Chọn phương thức nạp dữ liệu:",
        options=[
            "⚡ Dùng dữ liệu mẫu (Sample)",
            "📂 Upload nhiều file (JSON / TXT / XML)",
            "🗂️ Quét cả thư mục cục bộ",
        ],
        index=0,
    )

    # 2. Canvas & Ảnh Gốc
    st.sidebar.markdown("---")
    st.sidebar.subheader("📐 2. Canvas & Ảnh Gốc")

    canvas_res = st.sidebar.selectbox(
        "Độ phân giải khung hình (YOLO):",
        options=["1920x1080 (Full HD)", "1280x720 (HD BDD100K)", "2560x1440 (2K)"],
        index=0,
        help="Tọa độ YOLO được chuẩn hóa (0..1), cần kích thước ảnh để tính ra pixel.",
    )
    default_w = 1920 if "1920" in canvas_res else (1280 if "1280" in canvas_res else 2560)
    default_h = 1080 if "1080" in canvas_res else (720 if "720" in canvas_res else 1440)

    uploaded_images_raw = st.sidebar.file_uploader(
        "Tải ảnh minh họa gốc (Tùy chọn):",
        type=["jpg", "jpeg", "png", "webp", "bmp"],
        accept_multiple_files=True,
        help="Upload ảnh gốc tương ứng với frame để hiển thị viền lỗi trên ảnh thật.",
    )
    uploaded_image_map: Dict[str, Any] = {}
    if uploaded_images_raw:
        for _img_f in uploaded_images_raw:
            uploaded_image_map[_img_f.name] = _img_f
            uploaded_image_map[Path(_img_f.name).stem] = _img_f
        st.sidebar.success(f"✅ Đã nạp **{len(uploaded_images_raw)} ảnh** minh họa")

    all_sources: List[Tuple[str, List[FrameData]]] = []
    file_display_name = "batch"

    # Xử lý theo từng Data Source
    if data_source == "⚡ Dùng dữ liệu mẫu (Sample)":
        sample_choice = st.sidebar.selectbox(
            "Chọn tệp dữ liệu mẫu:",
            options=[
                "🔴 sample_with_errors.json (7 vi phạm kỹ thuật)",
                "🟢 sample_valid.json (Bộ nhãn 100% chuẩn quy cách)",
            ],
            index=0,
        )
        sel_file = "sample_valid.json" if "sample_valid" in sample_choice else "sample_with_errors.json"
        base_dir = Path(__file__).parent.parent
        sample_file_path = base_dir / "data_sample" / sel_file

        if sample_file_path.exists():
            try:
                frames_sample = load_bdd100k(sample_file_path)
                all_sources.append((sel_file, frames_sample))
                file_display_name = sample_file_path.stem
                st.sidebar.success(f"✅ Đã nạp `{sel_file}` ({len(frames_sample)} frames)")
            except Exception as ex:
                st.sidebar.error(f"Lỗi đọc file mẫu: {ex}")
        else:
            st.sidebar.error(f"Không tìm thấy file mẫu: {sel_file}")

    elif data_source == "📂 Upload nhiều file (JSON / TXT / XML)":
        st.sidebar.caption("Hỗ trợ chọn nhiều file cùng lúc: `.json`, `.txt` (BDD100K hoặc YOLO), `.xml`")
        uploaded_files = st.sidebar.file_uploader(
            "Chọn file nhãn:",
            type=["json", "txt", "xml"],
            accept_multiple_files=True,
            help="Giữ Ctrl hoặc Cmd để chọn nhiều file cùng lúc.",
        )
        if uploaded_files:
            custom_classes: Optional[List[str]] = None
            for uf in uploaded_files:
                if uf.name.lower() in ("classes.txt", "names.txt", "obj.names"):
                    try:
                        custom_classes = [l.strip() for l in uf.getvalue().decode("utf-8").splitlines() if l.strip()]
                        st.sidebar.info(f"🏷️ Nhận diện classes: {', '.join(custom_classes[:5])}")
                    except Exception:
                        pass

            ok_count = 0
            fail_names = []
            for uf in uploaded_files:
                if uf.name.lower() in ("classes.txt", "names.txt", "obj.names"):
                    continue

                cur_w, cur_h = default_w, default_h
                matched_img = find_matching_image(uf.name, uploaded_image_map)
                if matched_img:
                    try:
                        with Image.open(matched_img) as _tmp_img:
                            cur_w, cur_h = _tmp_img.size
                    except Exception:
                        pass

                frames_parsed = read_file_bytes(
                    uf.getvalue(),
                    uf.name,
                    width=cur_w,
                    height=cur_h,
                    class_names=custom_classes,
                )
                if frames_parsed:
                    all_sources.append((uf.name, frames_parsed))
                    ok_count += 1
                else:
                    fail_names.append(uf.name)

            if ok_count:
                st.sidebar.success(f"✅ Đã nạp thành công **{ok_count}/{len(uploaded_files)} file**")
                file_display_name = "_".join(Path(f.name).stem for f in uploaded_files[:3])
            if fail_names:
                st.sidebar.warning(f"⚠️ Không đọc được: {', '.join(fail_names)}")

    else:  # Quét thư mục
        st.sidebar.caption("Nhập đường dẫn thư mục chứa file nhãn.")
        folder_input = st.sidebar.text_input(
            "Đường dẫn thư mục:",
            placeholder=r"Ví dụ: C:\Users\...\Video_3",
        )
        scan_btn = st.sidebar.button("🔍 Quét thư mục", use_container_width=True)
        if scan_btn and folder_input:
            with st.sidebar:
                with st.spinner("Đang quét..."):
                    folder_sources, folder_classes = scan_folder(
                        folder_input.strip(),
                        default_w=default_w,
                        default_h=default_h,
                    )
            if folder_sources:
                all_sources = folder_sources
                file_display_name = Path(folder_input.strip()).name
                total_frames_found = sum(len(frs) for _, frs in folder_sources)
                st.sidebar.success(
                    f"✅ Tìm thấy **{len(folder_sources)} file** · "
                    f"**{total_frames_found} frames** trong `{Path(folder_input.strip()).name}/`"
                )
                if folder_classes:
                    st.sidebar.info(f"🏷️ Classes: {', '.join(folder_classes[:5])}")
            else:
                st.sidebar.warning("Không tìm thấy file nhãn hợp lệ trong thư mục này.")
        elif scan_btn:
            st.sidebar.warning("Vui lòng nhập đường dẫn thư mục.")

        if all_sources:
            with st.sidebar.expander(f"📄 {len(all_sources)} file tìm thấy", expanded=False):
                for fname, frs in all_sources:
                    st.caption(f"• **{fname}** — {len(frs)} frames")

    # 3. Bộ lọc Rules
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎯 3. Bộ Luật Kiểm Tra")

    enable_bbox = st.sidebar.checkbox("Kiểm tra Bounding Box (B01 - B05)", value=True)
    enable_poly = st.sidebar.checkbox("Kiểm tra Polygon (P01 - P04)", value=True)
    enable_attr = st.sidebar.checkbox("Kiểm tra Thuộc tính & Nhãn (A01 - A03, C01)", value=True)
    enable_seq = st.sidebar.checkbox("Kiểm tra Chuỗi Video (T01 - T02)", value=True)

    active_rules = []
    if enable_bbox:
        active_rules.extend(ALL_BBOX_RULES)
    if enable_poly:
        active_rules.extend(ALL_POLYGON_RULES)
    if enable_attr:
        active_rules.extend(ALL_ATTRIBUTE_RULES)

    active_seq_rules = ALL_SEQUENCE_RULES if enable_seq else []
    total_rules_active = len(active_rules) + len(active_seq_rules)
    total_system_rules = len(ALL_BBOX_RULES) + len(ALL_POLYGON_RULES) + len(ALL_ATTRIBUTE_RULES) + len(ALL_SEQUENCE_RULES)

    st.sidebar.info(f"Đang kích hoạt: **{total_rules_active} / {total_system_rules} rules**")

    # 4. Trợ Lý AI
    enable_ai_check = False
    ai_conf = 0.35
    if ai_model is not None:
        st.sidebar.markdown("---")
        st.sidebar.subheader("🤖 4. Trợ Lý AI Soi Bỏ Sót")
        enable_ai_check = st.sidebar.checkbox(
            "Bật AI soi xe/người BỎ SÓT",
            value=True,
            help="Dùng YOLOv8 quét ảnh và khoanh vùng các vật thể bạn chưa gán nhãn.",
        )
        if enable_ai_check:
            ai_conf = st.sidebar.slider("Độ nhạy AI (Confidence):", 0.20, 0.70, 0.35, 0.05)

    # 5. Điều Khiển QC
    st.sidebar.markdown("---")
    st.sidebar.subheader("🚀 5. Điều Khiển QC")
    btn_col1, btn_col2 = st.sidebar.columns([3, 2])
    run_btn = btn_col1.button(
        "🚀 Bắt đầu",
        use_container_width=True,
        type="primary",
        disabled=not all_sources,
        help="Bắt đầu chạy kiểm tra QC trên các file đã nạp",
    )
    reset_btn = btn_col2.button(
        "🔄 Làm mới",
        use_container_width=True,
        help="Tải lại / Xóa cache kết quả kiểm tra",
    )

    # Team Card
    st.sidebar.markdown("""
    <div class="team-card">
        <div style="font-size: 0.76rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; margin-bottom: 6px;">👥 Đội Ngũ Thực Hiện (N2-04A)</div>
        <div class="team-member-row"><span class="team-member-name">Đào Ngọc Hiếu</span><span class="team-member-role">Leader</span></div>
        <div class="team-member-row"><span class="team-member-name">Đoàn Văn Thắng</span><span class="team-member-role">Data Eng</span></div>
        <div class="team-member-row"><span class="team-member-name">Nguyễn Thanh Đức</span><span class="team-member-role">BBox QC</span></div>
        <div class="team-member-row"><span class="team-member-name">Hoàng Công Chứ</span><span class="team-member-role">Poly QC</span></div>
        <div class="team-member-row"><span class="team-member-name">Trần Thị Thủy Tiên</span><span class="team-member-role">Attr QC</span></div>
    </div>
    """, unsafe_allow_html=True)

    # 6. Chuyển đổi Theme ở dưới cùng của Sidebar
    st.sidebar.markdown("---")
    theme_choice = st.sidebar.radio(
        "Chế độ hiển thị (Theme):",
        options=["🌙 Tối", "☀️ Sáng"],
        index=0,
        horizontal=True,
        help="Chuyển đổi giao diện Sáng / Tối theo nhu cầu làm việc"
    )
    is_dark = ("Tối" in theme_choice or "Dark" in theme_choice)

    return {
        "is_dark": is_dark,
        "all_sources": all_sources,
        "file_display_name": file_display_name,
        "uploaded_image_map": uploaded_image_map,
        "active_rules": active_rules,
        "active_seq_rules": active_seq_rules,
        "total_rules_active": total_rules_active,
        "enable_ai_check": enable_ai_check,
        "ai_conf": ai_conf,
        "run_btn": run_btn,
        "reset_btn": reset_btn,
    }
