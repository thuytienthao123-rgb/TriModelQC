from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from PIL import Image
import streamlit as st

from qc.models import FrameData
from qc.rules.bbox_rules import ALL_BBOX_RULES
from qc.rules.polygon_rules import ALL_POLYGON_RULES
from qc.rules.attribute_rules import ALL_ATTRIBUTE_RULES
from qc.rules.sequence_rules import ALL_SEQUENCE_RULES

from ui.io_utils import find_matching_image, read_file_bytes, scan_folder
from ui.i18n import t, get_current_lang, set_current_lang
from ui.cvat_bridge import CVATBridge, create_cvat_mock_session


def render_sidebar(ai_model: Any) -> Dict[str, Any]:
    """
    Render thanh công cụ bên trái (Sidebar).
    Hỗ trợ chuyển đổi ngôn ngữ song phương (Tiếng Việt / English),
    tinh giản nhận diện thương hiệu, và cung cấp bảng tra cứu 15 bộ luật.
    """
    # 1. Biểu tượng khiên ở góc trên bên trái (Đã xóa tên & mô tả phụ theo yêu cầu)
    st.sidebar.markdown("""
    <div style="display: flex; align-items: center; justify-content: flex-start; margin-bottom: 8px; padding-top: 4px;">
        <div style="width: 44px; height: 44px; border-radius: 12px; background: rgba(0, 229, 255, 0.08); border: 1.5px solid rgba(0, 229, 255, 0.35); display: flex; align-items: center; justify-content: center; font-size: 1.55rem; box-shadow: 0 4px 14px rgba(0, 229, 255, 0.15);">
            🛡️
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Chuyển đổi ngôn ngữ hệ thống (Tiếng Việt / English)
    curr_lang = get_current_lang()
    lang_labels = ["Tiếng Việt 🇻🇳", "English 🇺🇸"]
    lang_idx = 0 if curr_lang == "vi" else 1

    selected_lang = st.sidebar.radio(
        "🌐 Ngôn ngữ / Language:",
        options=lang_labels,
        index=lang_idx,
        key="qc_sidebar_lang_radio",
        horizontal=True,
        help="Chuyển đổi ngôn ngữ giao diện (Switch Interface Language)",
    )
    new_lang = "vi" if "Tiếng Việt" in selected_lang else "en"
    if new_lang != curr_lang:
        set_current_lang(new_lang)
        st.rerun()

    # Chuyển đổi giao diện Sáng / Tối (Theme Mode)
    cur_theme = st.session_state.get("global_theme_mode", "dark")
    theme_labels = ["🌙 Dark (Tối)", "☀️ Light (Sáng)"]
    theme_idx = 0 if cur_theme == "dark" else 1

    selected_theme = st.sidebar.radio(
        "🎨 Giao diện / Theme:",
        options=theme_labels,
        index=theme_idx,
        key="qc_sidebar_theme_radio",
        horizontal=True,
        help="Chuyển đổi giữa chế độ nền tối (Dark Mode) và nền sáng (Light Mode)",
    )
    new_theme = "dark" if "Dark" in selected_theme else "light"
    if new_theme != cur_theme:
        st.session_state["global_theme_mode"] = new_theme
        st.rerun()

    is_dark = (new_theme == "dark")

    # 1. Nguồn Dữ Liệu
    st.sidebar.markdown("---")
    st.sidebar.subheader(t("sec_source"))

    opt_cvat = "🌐 Đồng Bộ Trực Tuyến CVAT" if curr_lang == "vi" else "🌐 Online CVAT Sync"
    source_options = [
        t("opt_upload"),
        t("opt_folder"),
        opt_cvat,
    ]
    data_source = st.sidebar.radio(
        t("source_mode"),
        options=source_options,
        index=0,
    )

    # 2. Canvas & Ảnh Gốc
    st.sidebar.markdown("---")
    st.sidebar.subheader(t("sec_canvas"))

    res_options = (
        ["1920x1080 (Chuẩn Full HD)", "1280x720 (Chuẩn BDD100K)", "2560x1440 (Độ nét cao 2K)"]
        if curr_lang == "vi"
        else ["1920x1080 (Full HD)", "1280x720 (HD BDD100K)", "2560x1440 (2K)"]
    )
    canvas_res = st.sidebar.selectbox(
        t("canvas_res_label"),
        options=res_options,
        index=0,
        help="Tọa độ chuẩn hóa (0..1) cần kích thước khung hình để tính ra pixel thực tế.",
    )
    default_w = 1920 if "1920" in canvas_res else (1280 if "1280" in canvas_res else 2560)
    default_h = 1080 if "1080" in canvas_res else (720 if "720" in canvas_res else 1440)

    # Bộ nạp ảnh kèm nút Reload/Reset bộ ảnh
    img_reset_counter = st.session_state.get("img_reset_counter", 0)
    img_uploader_key = f"uploader_imgs_{img_reset_counter}"

    uploaded_images_raw = st.sidebar.file_uploader(
        t("upload_images_label"),
        type=["jpg", "jpeg", "png", "webp", "bmp"],
        accept_multiple_files=True,
        key=img_uploader_key,
        help="Upload ảnh gốc tương ứng với frame để hiển thị viền lỗi trên ảnh thật.",
    )

    col_img_info, col_img_reload = st.sidebar.columns([3, 2])
    with col_img_reload:
        if st.button(t("btn_reset_images"), use_container_width=True, help="Xóa bộ ảnh hiện tại để chọn bộ ảnh mới"):
            st.session_state["img_reset_counter"] = img_reset_counter + 1
            st.session_state["qc_ai_missed_cache"] = {}
            st.rerun()

    uploaded_image_map: Dict[str, Any] = {}
    if uploaded_images_raw:
        for _img_f in uploaded_images_raw:
            uploaded_image_map[_img_f.name] = _img_f
            uploaded_image_map[Path(_img_f.name).stem] = _img_f
        with col_img_info:
            st.caption(t("images_loaded_msg", count=len(uploaded_images_raw)))

    # Tự động gộp bộ ảnh đã nạp từ CVAT hoặc Mock Session (nếu có) để AI và Canvas sử dụng
    cvat_imgs = st.session_state.get("cvat_image_map", {})
    if cvat_imgs:
        for k, v in cvat_imgs.items():
            if k not in uploaded_image_map:
                uploaded_image_map[k] = v

    all_sources: List[Tuple[str, List[FrameData]]] = []
    file_display_name = "batch"

    # Xử lý theo từng Data Source
    if data_source == source_options[0]:  # 1. Multi upload (Mặc định - Khởi động sạch 100%)
        if curr_lang == "vi":
            st.sidebar.caption("Hỗ trợ tệp: .json, .txt hoặc .xml")
        else:
            st.sidebar.caption("Supported formats: .json (BDD100K) / .txt (YOLO) / .xml")

        lbl_reset_counter = st.session_state.get("lbl_reset_counter", 0)
        lbl_uploader_key = f"uploader_lbls_{lbl_reset_counter}"

        uploaded_files = st.sidebar.file_uploader(
            t("upload_label"),
            type=["json", "txt", "xml"],
            accept_multiple_files=True,
            key=lbl_uploader_key,
            help="Giữ Ctrl hoặc Cmd để chọn nhiều tệp cùng lúc.",
        )

        if uploaded_files:
            col_lbl_info, col_lbl_reload = st.sidebar.columns([3, 2])
            with col_lbl_info:
                st.caption(f"✅ {len(uploaded_files)} tệp nhãn" if curr_lang == "vi" else f"✅ {len(uploaded_files)} files")
            with col_lbl_reload:
                if st.button(t("btn_reset_labels"), use_container_width=True, help="Xóa bộ tệp nhãn hiện tại để chọn tệp mới", key="btn_reset_lbl_active"):
                    st.session_state["lbl_reset_counter"] = lbl_reset_counter + 1
                    st.session_state["qc_report"] = None
                    st.session_state["qc_frames"] = None
                    st.session_state["qc_sources"] = None
                    st.session_state["qc_ai_missed_cache"] = {}
                    st.rerun()
        else:
            if st.sidebar.button(t("btn_reset_labels"), use_container_width=True, help="Làm mới bộ chọn tệp nhãn", key="btn_reset_lbl_empty"):
                st.session_state["lbl_reset_counter"] = lbl_reset_counter + 1
                st.session_state["qc_report"] = None
                st.session_state["qc_frames"] = None
                st.session_state["qc_sources"] = None
                st.session_state["qc_ai_missed_cache"] = {}
                st.rerun()

        if uploaded_files:
            custom_classes: Optional[List[str]] = None
            for uf in uploaded_files:
                if uf.name.lower() in ("classes.txt", "names.txt", "obj.names"):
                    try:
                        custom_classes = [l.strip() for l in uf.getvalue().decode("utf-8").splitlines() if l.strip()]
                        st.sidebar.info(f"🏷️ Danh mục: {', '.join(custom_classes[:5])}" if curr_lang == "vi" else f"🏷️ Classes: {', '.join(custom_classes[:5])}")
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
                msg_uf = f"✅ Đã nạp thành công {ok_count}/{len(uploaded_files)} tệp" if curr_lang == "vi" else f"✅ {ok_count}/{len(uploaded_files)} files loaded"
                st.sidebar.success(msg_uf)
                file_display_name = "_".join(Path(f.name).stem for f in uploaded_files[:3])
            if fail_names:
                msg_fail = f"⚠️ Không đọc được: {', '.join(fail_names)}" if curr_lang == "vi" else f"⚠️ Failed: {', '.join(fail_names)}"
                st.sidebar.warning(msg_fail)

    elif data_source == source_options[1]:  # 2. Tải thư mục
        st.sidebar.caption(t("folder_label"))
        folder_input = st.sidebar.text_input(
            t("folder_label"),
            placeholder=r"C:\Users\...\Video_3",
            label_visibility="collapsed",
        )
        scan_btn = st.sidebar.button(t("btn_scan"), use_container_width=True)
        if scan_btn and folder_input:
            scan_spinner = "Đang quét thư mục..." if curr_lang == "vi" else "Scanning folder..."
            with st.sidebar:
                with st.spinner(scan_spinner):
                    folder_sources, folder_classes = scan_folder(
                        folder_input.strip(),
                        default_w=default_w,
                        default_h=default_h,
                    )
            if folder_sources:
                all_sources = folder_sources
                file_display_name = Path(folder_input.strip()).name
                total_frames_found = sum(len(frs) for _, frs in folder_sources)
                found_msg = (
                    f"✅ Tìm thấy {len(folder_sources)} tệp · {total_frames_found} khung hình (`{Path(folder_input.strip()).name}`)"
                    if curr_lang == "vi"
                    else f"✅ {len(folder_sources)} files · {total_frames_found} frames (`{Path(folder_input.strip()).name}`)"
                )
                st.sidebar.success(found_msg)
                if folder_classes:
                    lbl_cls = "🏷️ Danh mục:" if curr_lang == "vi" else "🏷️ Classes:"
                    st.sidebar.info(f"{lbl_cls} {', '.join(folder_classes[:5])}")
            else:
                no_f_msg = "Không tìm thấy tệp nhãn hợp lệ trong thư mục này." if curr_lang == "vi" else "No valid label files found in this directory."
                st.sidebar.warning(no_f_msg)
        elif scan_btn:
            dir_warn = "Vui lòng nhập đường dẫn thư mục." if curr_lang == "vi" else "Please enter a valid directory path."
            st.sidebar.warning(dir_warn)

        if all_sources:
            exp_files_lbl = f"📄 {len(all_sources)} tệp" if curr_lang == "vi" else f"📄 {len(all_sources)} files"
            with st.sidebar.expander(exp_files_lbl, expanded=False):
                unit_fr = "khung hình" if curr_lang == "vi" else "frames"
                for fname, frs in all_sources:
                    st.caption(f"• **{fname}** — {len(frs)} {unit_fr}")

    elif data_source == source_options[2]:  # 3. CVAT Sync
        st.sidebar.markdown(
            """<div style="font-size: 0.76rem; color: #00e5ff; font-weight: 700; margin-bottom: 6px;">🌐 KẾT NỐI CVAT REST API</div>""",
            unsafe_allow_html=True
        )

        col_pr1, col_pr2 = st.sidebar.columns(2)
        with col_pr1:
            if st.button("🐳 Docker Local", use_container_width=True, help="Tự động nạp cấu hình CVAT Docker đang chạy tại localhost:8080"):
                st.session_state["cvat_input_server_url"] = "http://localhost:8080"
                st.session_state["cvat_input_token"] = "9e72a959c91cbfbd3bb011c047ba2f1e49022eb9"
                st.session_state["cvat_input_job_id"] = 1
                st.rerun()
        with col_pr2:
            if st.button("☁️ CVAT.ai", use_container_width=True, help="Sử dụng CVAT Cloud (app.cvat.ai)"):
                st.session_state["cvat_input_server_url"] = "https://app.cvat.ai"
                st.session_state["cvat_input_token"] = ""
                st.session_state["cvat_input_job_id"] = 88
                st.rerun()

        cvat_url = st.sidebar.text_input(
            "CVAT Server URL:",
            value=st.session_state.get("cvat_input_server_url", st.session_state.get("cvat_server_url", "http://localhost:8080")),
            help="Ví dụ: http://localhost:8080 (Docker local) hoặc https://app.cvat.ai.",
            key="cvat_input_server_url",
        )
        st.session_state["cvat_server_url"] = cvat_url

        cvat_token = st.sidebar.text_input(
            "API Token:",
            value=st.session_state.get("cvat_input_token", st.session_state.get("cvat_token", "")),
            type="password",
            help="Tạo token tại CVAT: Profile -> API Tokens.",
            key="cvat_input_token",
        )
        st.session_state["cvat_token"] = cvat_token

        cvat_job_id = st.sidebar.number_input(
            "Job ID:" if curr_lang == "vi" else "Job ID:",
            min_value=1,
            max_value=999999,
            value=int(st.session_state.get("cvat_input_job_id", st.session_state.get("cvat_job_id", 1))),
            step=1,
            key="cvat_input_job_id",
        )
        st.session_state["cvat_job_id"] = cvat_job_id

        col_cvat_btn1, col_cvat_btn2 = st.sidebar.columns(2)
        with col_cvat_btn1:
            btn_fetch_lbl = "📥 Nạp Từ CVAT" if curr_lang == "vi" else "📥 Fetch CVAT"
            if st.button(btn_fetch_lbl, use_container_width=True, type="primary", key="btn_fetch_cvat"):
                bridge = CVATBridge(server_url=cvat_url, token=cvat_token)
                with st.spinner("Đang kết nối và kéo nhãn + ảnh từ CVAT..." if curr_lang == "vi" else "Connecting & fetching annotations and images from CVAT..."):
                    ok, frames_cvat, meta_info = bridge.fetch_job_as_frames(cvat_job_id, fetch_images=True)
                    if ok:
                        st.session_state["cvat_bridge"] = bridge
                        st.session_state["cvat_meta"] = meta_info
                        st.session_state["cvat_frames"] = frames_cvat
                        img_map = meta_info.get("image_map", {})
                        st.session_state["cvat_image_map"] = img_map
                        uploaded_image_map.update(img_map)
                        st.session_state["qc_ai_missed_cache"] = {}
                        n_imgs = len(img_map) // 2 if img_map else 0
                        st.sidebar.success(f"✅ Đã kéo {len(frames_cvat)} frame ({meta_info.get('total_shapes', 0)} shapes) + {n_imgs} ảnh gốc từ CVAT!")
                        st.rerun()
                    else:
                        st.sidebar.error(f"❌ Không thể nạp từ CVAT: {meta_info.get('error')}")

        with col_cvat_btn2:
            btn_mock_lbl = "🧪 Test Mô Phỏng" if curr_lang == "vi" else "🧪 Mock Test"
            if st.button(btn_mock_lbl, use_container_width=True, key="btn_mock_cvat", help="Chạy thử nghiệm mô phỏng CVAT local ngay lập tức mà không cần tài khoản hay server"):
                frames_cvat, meta_info = create_cvat_mock_session()
                bridge = CVATBridge(server_url=cvat_url, token="mock_token_demo")
                st.session_state["cvat_bridge"] = bridge
                st.session_state["cvat_meta"] = meta_info
                st.session_state["cvat_frames"] = frames_cvat
                img_map = meta_info.get("image_map", {})
                st.session_state["cvat_image_map"] = img_map
                uploaded_image_map.update(img_map)
                st.session_state["qc_ai_missed_cache"] = {}
                st.sidebar.info("🧪 Đã nạp thành công phiên mô phỏng CVAT Local kèm ảnh nền mô phỏng!")
                st.rerun()

        # Nạp dữ liệu vào pipeline nếu đã có cvat_frames
        if "cvat_frames" in st.session_state and st.session_state["cvat_frames"]:
            cvat_frames_data = st.session_state["cvat_frames"]
            all_sources.append((f"cvat_job_{cvat_job_id}", cvat_frames_data))
            file_display_name = f"CVAT Job #{cvat_job_id}"
            has_imgs = bool(st.session_state.get("cvat_image_map"))
            st.sidebar.caption(
                f"🔗 Đang kết nối CVAT Job #{cvat_job_id} ({len(cvat_frames_data)} frames{' 📷 kèm ảnh thật' if has_imgs else ''})"
                if curr_lang == "vi"
                else f"🔗 Connected CVAT Job #{cvat_job_id} ({len(cvat_frames_data)} frames{' 📷 with real images' if has_imgs else ''})"
            )

    # 3. Bộ lọc Rules & Nút tra cứu Luật/Rules
    st.sidebar.markdown("---")
    st.sidebar.subheader(t("sec_rules"))

    # Nút bật popup giải thích chi tiết 15 bộ luật
    with st.sidebar.popover(t("btn_view_rules"), use_container_width=True):
        if curr_lang == "vi":
            st.markdown("""
            ### 📜 Danh Mục 15 Quy Chuẩn Kiểm Tra (QC Rules)
            ---
            #### 📐 1. Hộp Bao Giới Hạn
            - **`RULE_B01` — Tràn viền ảnh [🔴 LỖI]**: Tọa độ hộp nằm ngoài phạm vi ảnh ($x_1 < 0, y_1 < 0, x_2 > W, y_2 > H$).
            - **`RULE_B02` — Tọa độ âm / Hộp rỗng [🔴 LỖI]**: $x_2 \le x_1$ hoặc $y_2 \le y_1$ hoặc diện tích bằng 0px.
            - **`RULE_B03` — Kích thước quá nhỏ [🟡 CẢNH BÁO]**: Diện tích $w \times h < 64\text{px}^2$ (nghi ngờ điểm chấm rác hoặc nhiễu).
            - **`RULE_B04` — Tỉ lệ dị thường [🟡 CẢNH BÁO]**: Tỉ lệ $w/h > 25$ hoặc $h/w > 25$ (hộp bị kéo dẹt thành đường chỉ).
            - **`RULE_B05` — Hộp chiếm toàn màn hình [🟡 CẢNH BÁO]**: Diện tích hộp bao phủ $> 96\%$ diện tích toàn ảnh.

            #### 📉 2. Đa Giác Phân Đoạn
            - **`RULE_P01` — Thiếu đỉnh đa giác [🔴 LỖI]**: Đa giác có ít hơn 3 đỉnh, không thể khép kín diện tích.
            - **`RULE_P02` — Tự cắt viền hình nơ [🔴 LỖI]**: Đa giác tự giao chéo các cạnh tạo đa giác phức hợp.
            - **`RULE_P03` — Lệch khung bao [🟡 CẢNH BÁO]**: Độ khớp $\text{IoU}(\text{Box}(\text{poly}), \text{box2d}) < 0.70$.
            - **`RULE_P04` — Đỉnh trùng / Gấp khúc dị thường [🟡 CẢNH BÁO]**: Có 2 đỉnh liên tiếp trùng nhau hoặc góc nhọn gấp khúc $< 3.5^\circ$.

            #### 👥 3. Thuộc Tính & Phân Loại
            - **`RULE_A01` — Vẽ đè trùng lặp [🔴 LỖI]**: 2 hộp cùng loại nhãn chồng lên nhau với $\text{IoU} > 0.85$.
            - **`RULE_A02` — Thiếu thuộc tính bắt buộc [🟡 CẢNH BÁO]**: Thiếu thuộc tính `occluded` hoặc `truncated`.
            - **`RULE_A03` — Màu đèn giao thông không hợp lệ [🔴 LỖI]**: Nhãn `traffic light` có màu ngoài danh mục chuẩn.
            - **`RULE_C01` — Sai phân loại chuẩn BDD100K [🔴 LỖI / 🟡 CẢNH BÁO]**: Tên nhãn không chuẩn hoặc sai chính tả.

            #### 🎬 4. Chuỗi Khung Hình Video
            - **`RULE_T01` — Mất dấu vật thể [🟡 CẢNH BÁO]**: Xuất hiện ở Frame $k-1$ và $k+1$ nhưng biến mất ở Frame $k$.
            - **`RULE_T02` — Nhảy vọt tọa độ [🟡 CẢNH BÁO]**: Hộp nhảy vị trí bất thường $> 35\%$ kích thước ảnh giữa 2 frame.

            #### 🤖 5. Trợ Lý AI
            - **`RULE_AI01` — Đối soát AI phát hiện bỏ sót [🔴 LỖI / 🟡 CẢNH BÁO]**: AI phát hiện xe hoặc người có độ tin cậy cao chưa được gán nhãn.
            """)
        else:
            st.markdown("""
            ### 📜 Specification: 15 Quality Control Rules
            ---
            #### 📐 1. Bounding Box Geometry
            - **`RULE_B01` — Out of Bounds [🔴 ERROR]**: Coordinates exceed canvas frame ($x_1 < 0, y_1 < 0, x_2 > W, y_2 > H$).
            - **`RULE_B02` — Inverted / Zero Box [🔴 ERROR]**: $x_2 \le x_1$ or $y_2 \le y_1$ or area is 0px.
            - **`RULE_B03` — Too Small Box [🟡 WARNING]**: Area $w \times h < 64\text{px}^2$ (noise or micro artifact).
            - **`RULE_B04` — Abnormal Aspect Ratio [🟡 WARNING]**: Aspect ratio $w/h > 25$ or $h/w > 25$ (unrealistically thin box).
            - **`RULE_B05` — Fullscreen Box [🟡 WARNING]**: Box covers $> 96\%$ of entire image area.

            #### 📉 2. Polygon Topology
            - **`RULE_P01` — Insufficient Vertices [🔴 ERROR]**: Polygon contains fewer than 3 vertices.
            - **`RULE_P02` — Self-Intersection [🔴 ERROR]**: Self-crossing bowtie or complex non-simple polygon.
            - **`RULE_P03` — Mask vs Box Mismatch [🟡 WARNING]**: $\text{IoU}(\text{Box}(\text{poly}), \text{box2d}) < 0.70$.
            - **`RULE_P04` — Spike or Duplicate Vertices [🟡 WARNING]**: Adjacent duplicate points or sharp fold $< 3.5^\circ$.

            #### 👥 3. Attributes & Category Ontology
            - **`RULE_A01` — Duplicate Annotation [🔴 ERROR]**: Two identical-class boxes overlap with $\text{IoU} > 0.85$.
            - **`RULE_A02` — Missing Attributes [🟡 WARNING]**: Missing `occluded` or `truncated` attributes.
            - **`RULE_A03` — Invalid Traffic Light Color [🔴 ERROR]**: Color value outside `[red, yellow, green, none]`.
            - **`RULE_C01` — Category Ontology Mismatch [🔴 ERROR / 🟡 WARNING]**: Non-standard or misspelled class name.

            #### 🎬 4. Video Sequence Tracking
            - **`RULE_T01` — Object Flicker / Lost Track [🟡 WARNING]**: Present at Frame $k-1$ and $k+1$, but omitted at Frame $k$.
            - **`RULE_T02` — Sudden Displacement Jump [🟡 WARNING]**: Center position jumps $> 35\%$ frame dimensions between adjacent frames.

            #### 🤖 5. AI Assistant
            - **`RULE_AI01` — AI False-Negative Detection [🔴 ERROR / 🟡 WARNING]**: High-confidence unlabeled vehicle or pedestrian.
            """)

    enable_bbox = st.sidebar.checkbox(
        t("rule_bbox_lbl"),
        value=True,
        help=t("rule_bbox_help")
    )
    enable_poly = st.sidebar.checkbox(
        t("rule_poly_lbl"),
        value=True,
        help=t("rule_poly_help")
    )
    enable_attr = st.sidebar.checkbox(
        t("rule_attr_lbl"),
        value=True,
        help=t("rule_attr_help")
    )
    enable_seq = st.sidebar.checkbox(
        t("rule_seq_lbl"),
        value=True,
        help=t("rule_seq_help")
    )

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

    st.sidebar.caption(t("rules_active_summary", active=total_rules_active, total=total_system_rules))

    # 4. Trợ Lý AI
    enable_ai_check = False
    ai_conf = 0.20
    ai_ensemble_mode = "majority"
    if ai_model is not None:
        st.sidebar.markdown("---")
        st.sidebar.subheader(t("sec_ai"))
        enable_ai_check = st.sidebar.checkbox(
            t("ai_enable_lbl"),
            value=True,
            help="Dùng Tri-Model YOLOv8 quét ảnh và khoanh vùng các vật thể bạn chưa gán nhãn." if curr_lang == "vi" else "Uses Tri-Model YOLOv8 to scan images and highlight missed annotations.",
        )
        if enable_ai_check:
            ai_conf = st.sidebar.slider(
                t("ai_conf_lbl"),
                0.15, 0.70, 0.20, 0.05,
                help="Ngưỡng 0.20 được khuyến nghị để bắt trọn xe nhỏ ở xa trong ảnh 1080p." if curr_lang == "vi" else "0.20 confidence threshold recommended for small distant vehicles in 1080p."
            )
            mode_choice = st.sidebar.radio(
                t("ai_mode_lbl"),
                [t("ai_mode_majority"), t("ai_mode_strict")],
                index=0,
            )
            ai_ensemble_mode = "strict" if ("Strict" in mode_choice or "Tuyệt đối" in mode_choice) else "majority"

    # 5. Điều Khiển QC
    st.sidebar.markdown("---")
    st.sidebar.subheader(t("sec_control"))
    btn_col1, btn_col2 = st.sidebar.columns([3, 2])
    run_btn = btn_col1.button(
        t("btn_checking"),
        use_container_width=True,
        type="primary",
        disabled=not all_sources,
        help="Bắt đầu chạy kiểm tra QC trên các file đã nạp" if curr_lang == "vi" else "Run automated QC audit on loaded files",
    )
    reset_btn = btn_col2.button(
        t("btn_reload_sidebar"),
        use_container_width=True,
        help="Tải lại / Xóa cache kết quả kiểm tra" if curr_lang == "vi" else "Reload & clear audit cache",
    )

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
        "ai_ensemble_mode": ai_ensemble_mode,
        "run_btn": run_btn,
        "reset_btn": reset_btn,
    }
