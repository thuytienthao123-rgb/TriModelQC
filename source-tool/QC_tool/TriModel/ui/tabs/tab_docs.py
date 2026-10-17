from __future__ import annotations
import streamlit as st
from ui.i18n import get_current_lang


def render_tab_docs():
    """Render Tab 4: Quy chuẩn 15 Quy tắc & Hướng dẫn sửa lỗi cho Annotator."""
    lang = get_current_lang()

    if lang == "vi":
        st.markdown("""
        <div style="margin-bottom: 16px;">
            <h3 style="margin: 0; color: #f8fafc; font-size: 1.25rem;">📖 Đặc Tả 15 Quy Tắc Kiểm Tra & Hướng Dẫn Khắc Phục Lỗi</h3>
            <p style="margin: 2px 0 0 0; color: #94a3b8; font-size: 0.85rem;">Quy chuẩn kiểm soát chất lượng nhãn Bounding Box, Polygon Topology và Chuỗi Video (Dự án N2-04A)</p>
        </div>
        """, unsafe_allow_html=True)

        r_tab1, r_tab2, r_tab3, r_tab4, r_tab5 = st.tabs([
            "📐 Hộp Bao Bounding Box (B01-B05)",
            "📉 Đa Giác Phân Đoạn (P01-P04)",
            "👥 Thuộc Tính & Phân Loại (A01-C01)",
            "🎬 Chuỗi Khung Hình Video (T01-T02)",
            "🤖 Đối Soát Trợ Lý AI (AI01)",
        ])

        with r_tab1:
            st.markdown(r"""
            #### 📐 Nhóm Quy Tắc Hình Học Hộp Bao (Bounding Box)
            - **`RULE_B01` — Tràn Viền Ảnh (🔴 LỖI NGHIÊM TRỌNG):**
              - *Mô tả:* Tọa độ hộp nằm ngoài phạm vi kích thước ảnh ($x_1 < 0, y_1 < 0, x_2 > W, y_2 > H$).
              - *Nguyên nhân:* Vẽ tràn viền ảnh hoặc thao tác chuột ra ngoài vùng canvas.
              - *Khắc phục:* Thu nhỏ hộp hoặc kéo toàn bộ hộp nằm trọn trong phạm vi $[0, W] \times [0, H]$.
            - **`RULE_B02` — Tọa Độ Đảo Ngược / Hộp Rỗng (🔴 LỖI NGHIÊM TRỌNG):**
              - *Mô tả:* $x_2 \le x_1$ hoặc $y_2 \le y_1$ hoặc diện tích bằng 0px.
              - *Nguyên nhân:* Kéo chuột đảo ngược điểm đầu cuối hoặc nhấn chuột vô tình tạo hộp rỗng.
              - *Khắc phục:* Xóa hộp 0px và vẽ lại sao cho $x_2 > x_1$ và $y_2 > y_1$.
            - **`RULE_B03` — Kích Thước Quá Nhỏ (🟡 CẢNH BÁO):**
              - *Mô tả:* Diện tích hộp $w \times h < 64\text{px}^2$.
              - *Nguyên nhân:* Nhấp nhầm điểm ảnh nhiễu hoặc vật thể quá xa không đủ độ chi tiết.
              - *Khắc phục:* Nếu là vật thể thật hãy giữ lại; nếu là điểm ảnh rác hãy xóa bỏ.
            - **`RULE_B04` — Tỉ Lệ Dị Thường (🟡 CẢNH BÁO):**
              - *Mô tả:* Tỉ lệ chiều rộng/chiều cao $w/h > 25$ hoặc $h/w > 25$.
              - *Nguyên nhân:* Hộp bị kéo dẹt bất thường thành một đường mảnh.
              - *Khắc phục:* Căn chỉnh lại chiều rộng và chiều cao sao cho bao khít vật thể thực tế.
            - **`RULE_B05` — Hộp Bao Trọn Màn Hình (🟡 CẢNH BÁO):**
              - *Mô tả:* Diện tích hộp chiếm $> 96\%$ diện tích toàn khung hình.
              - *Nguyên nhân:* Thao tác nhầm kéo từ góc này sang góc kia bao trọn toàn bộ ảnh.
              - *Khắc phục:* Xóa hộp nếu là thao tác kéo nhầm toàn cảnh.
            """)

        with r_tab2:
            st.markdown(r"""
            #### 📉 Nhóm Quy Tắc Cấu Trúc Đa Giác (Polygon Topology)
            - **`RULE_P01` — Thiếu Đỉnh Đa Giác (🔴 LỖI NGHIÊM TRỌNG):**
              - *Mô tả:* Số đỉnh của đa giác $< 3$.
              - *Nguyên nhân:* Kết thúc thao tác vẽ khi mới chỉ có 1 hoặc 2 điểm.
              - *Khắc phục:* Đa giác khép kín cần tối thiểu 3 đỉnh. Vẽ thêm đỉnh hoặc dùng chức năng Tự Động Sửa.
            - **`RULE_P02` — Tự Cắt Viền Hình Nơ (🔴 LỖI NGHIÊM TRỌNG):**
              - *Mô tả:* Các cạnh của đa giác tự giao cắt nhau tạo thành hình nơ phức hợp.
              - *Nguyên nhân:* Thứ tự các đỉnh bị đảo lộn chéo nhau khi vẽ tay nhanh.
              - *Khắc phục:* Sử dụng công cụ Tự Động Sửa (Unknotting) hoặc vẽ lại theo chiều kim đồng hồ.
            - **`RULE_P03` — Sai Lệch Giữa Mặt Nạ Và Hộp Bao (🟡 CẢNH BÁO):**
              - *Mô tả:* Độ khớp $\text{IoU}(\text{Box}(\text{poly}), \text{box2d}) < 0.70$.
              - *Nguyên nhân:* Hộp bao BBox và đường biên Polygon của cùng một vật thể không đồng bộ.
              - *Khắc phục:* Điều chỉnh lại BBox sao cho ôm khít hoàn toàn ranh giới của Polygon.
            - **`RULE_P04` — Đỉnh Trùng Lặp / Gấp Khúc Dị Thường (🟡 CẢNH BÁO):**
              - *Mô tả:* Đa giác có 2 đỉnh kế tiếp trùng vị trí (< 0.8px) hoặc góc nhọn gấp khúc $< 3.5^\circ$.
              - *Khắc phục:* Xóa bỏ đỉnh thừa hoặc làm mượt góc đa giác.
            """)

        with r_tab3:
            st.markdown(r"""
            #### 👥 Nhóm Quy Tắc Thuộc Tính & Phân Loại
            - **`RULE_A01` — Vẽ Đè Trùng Lặp (🔴 LỖI NGHIÊM TRỌNG):**
              - *Mô tả:* 2 hộp cùng loại nhãn chồng đè lên nhau với $\text{IoU} > 0.85$.
              - *Nguyên nhân:* Người gán nhãn vẽ 2 lần cho cùng một vật thể mà quên xóa nhãn cũ.
              - *Khắc phục:* Kiểm tra danh sách nhãn và xóa 1 trong 2 hộp trùng lặp.
            - **`RULE_A02` — Thiếu Thuộc Tính Bắt Buộc (🟡 CẢNH BÁO):**
              - *Mô tả:* Thiếu 2 thuộc tính chuẩn bắt buộc: `occluded` (bị che khuất) hoặc `truncated` (bị cắt mép).
              - *Khắc phục:* Điền đầy đủ giá trị Đúng/Sai cho các thuộc tính này.
            - **`RULE_A03` — Màu Đèn Giao Thông Sai Quy Chuẩn (🔴 LỖI NGHIÊM TRỌNG):**
              - *Mô tả:* Vật thể `traffic light` có thuộc tính màu ngoài danh mục `[red, yellow, green, none]`.
              - *Khắc phục:* Khai báo đúng màu trạng thái của đèn tín hiệu.
            - **`RULE_C01` — Danh Mục Chuẩn & Lỗi Chính Tả (🔴 LỖI / 🟡 CẢNH BÁO):**
              - *Mô tả:* Tên nhãn không thuộc bộ danh mục BDD100K hoặc sai chính tả (ví dụ: `cars` thay vì `car`).
              - *Khắc phục:* Đổi lại đúng danh từ số ít theo chuẩn quy định.
            """)

        with r_tab4:
            st.markdown(r"""
            #### 🎬 Nhóm Quy Tắc Chuỗi Khung Hình Video (Temporal Tracking)
            - **`RULE_T01` — Mất Dấu Vật Thể (🟡 CẢNH BÁO):**
              - *Mô tả:* Vật thể xuất hiện ở Frame $k-1$ và Frame $k+1$ nhưng bị biến mất ở Frame $k$.
              - *Nguyên nhân:* Người gán nhãn bỏ sót một khung hình ở giữa chuỗi video.
              - *Khắc phục:* Bổ sung nhãn liên tục hoặc dùng tính năng nội suy tọa độ.
            - **`RULE_T02` — Nhảy Vọt Tọa Độ Bất Thường (🟡 CẢNH BÁO):**
              - *Mô tả:* Hộp bị dịch chuyển vị trí đột ngột ($> 35\%$ kích thước khung hình) giữa 2 frame liên tiếp.
              - *Nguyên nhân:* Gán nhầm mã định danh (Track ID) giữa 2 vật thể khác nhau.
              - *Khắc phục:* Kiểm tra lại mã Track ID hoặc chỉnh lại vị trí hộp cho chuyển động mượt mà.
            """)

        with r_tab5:
            st.markdown(r"""
            #### 🤖 Nhóm Đối Soát Bằng Trợ Lý AI
            - **`RULE_AI01` — Đối Soát AI Phát Hiện Bỏ Sót (🔴 LỖI / 🟡 CẢNH BÁO):**
              - *Mô tả:* Hệ thống AI đa mô hình quét ảnh và phát hiện phương tiện/người chưa có nhãn tương ứng.
              - *Độ tin cậy:* Mức tin cậy $\ge 60\%$ xếp vào Lỗi; mức $35\% - 60\%$ xếp vào Cảnh báo.
              - *Khắc phục:* Đối chiếu với ảnh thực tế để xác nhận và bổ sung nhãn bị bỏ quên.
            """)

    else:
        st.markdown("""
        <div style="margin-bottom: 16px;">
            <h3 style="margin: 0; color: #f8fafc; font-size: 1.25rem;">📖 15 Quality Control Rules Specification & Guidelines</h3>
            <p style="margin: 2px 0 0 0; color: #94a3b8; font-size: 0.85rem;">Standard quality criteria for Bounding Box, Polygon Topology, and Video Sequence Tracking (Project N2-04A)</p>
        </div>
        """, unsafe_allow_html=True)

        r_tab1, r_tab2, r_tab3, r_tab4, r_tab5 = st.tabs([
            "📐 Bounding Box Geometry (B01-B05)",
            "📉 Polygon Topology (P01-P04)",
            "👥 Attributes & Ontology (A01-C01)",
            "🎬 Video Tracking Sequence (T01-T02)",
            "🤖 AI Assistant Audit (AI01)",
        ])

        with r_tab1:
            st.markdown(r"""
            #### 📐 Bounding Box Geometry Rules
            - **`RULE_B01` — Boundary Overflow (🔴 CRITICAL ERROR):**
              - *Formula:* Box coordinates exceed canvas boundary ($x_1 < 0, y_1 < 0, x_2 > W, y_2 > H$).
              - *Cause:* Dragging box out of image frame or mouse slipping beyond viewport.
              - *Fix:* Clamp box coordinates within $[0, W] \times [0, H]$.
            - **`RULE_B02` — Inverted / Zero-Area Box (🔴 CRITICAL ERROR):**
              - *Formula:* $x_2 \le x_1$ or $y_2 \le y_1$ or area equals 0px.
              - *Cause:* Inverted drag order or accidental zero-pixel click.
              - *Fix:* Remove 0px boxes and ensure $x_2 > x_1$ and $y_2 > y_1$.
            - **`RULE_B03` — Too Small Box (🟡 WARNING):**
              - *Formula:* Area $w \times h < 64\text{px}^2$.
              - *Cause:* Noise artifacts or distant objects lacking identifiable pixels.
              - *Fix:* Retain genuine targets; delete accidental clicks.
            - **`RULE_B04` — Abnormal Aspect Ratio (🟡 WARNING):**
              - *Formula:* Ratio $w/h > 25$ or $h/w > 25$.
              - *Cause:* Box stretched into an ultra-thin line.
              - *Fix:* Adjust width and height to match the true physical object silhouette.
            - **`RULE_B05` — Fullscreen Filler Box (🟡 WARNING):**
              - *Formula:* Box area covers $> 96\%$ of total frame area.
              - *Cause:* Accidental whole-screen corner-to-corner drag.
              - *Fix:* Remove accidental whole-frame annotations.
            """)

        with r_tab2:
            st.markdown(r"""
            #### 📉 Polygon Topology Rules
            - **`RULE_P01` — Insufficient Vertices (🔴 CRITICAL ERROR):**
              - *Formula:* Number of vertices $< 3$.
              - *Cause:* Drawing finalized before completing at least 3 points.
              - *Fix:* Closed polygon requires at least 3 points. Add missing vertices or use Auto-Fix.
            - **`RULE_P02` — Self-Intersecting Polygon (🔴 CRITICAL ERROR):**
              - *Formula:* Polygon perimeter crosses over itself (complex bowtie polygon).
              - *Cause:* Vertex ordering reversed during manual polygon drawing.
              - *Fix:* Use 1-Click Auto-Fix (Shapely unknotting) or redraw clockwise.
            - **`RULE_P03` — Mask vs BBox Mismatch (🟡 WARNING):**
              - *Formula:* Alignment $\text{IoU}(\text{Box}(\text{poly}), \text{box2d}) < 0.70$.
              - *Cause:* Bounding box and segmentation mask boundary out of sync.
              - *Fix:* Realign bounding box to enclose the polygon boundary tightly.
            - **`RULE_P04` — Spike or Duplicate Vertices (🟡 WARNING):**
              - *Formula:* Consecutive vertices $< 0.8\text{px}$ apart or interior angle $< 3.5^\circ$.
              - *Fix:* Remove duplicate points or smooth acute kink angles.
            """)

        with r_tab3:
            st.markdown(r"""
            #### 👥 Attributes & Category Ontology Rules
            - **`RULE_A01` — Duplicate Annotation (🔴 CRITICAL ERROR):**
              - *Formula:* Two boxes of the same category overlap with $\text{IoU} > 0.85$.
              - *Cause:* Annotator labeled the same instance twice without removing previous box.
              - *Fix:* Delete redundant overlapping box.
            - **`RULE_A02` — Missing Mandatory Attributes (🟡 WARNING):**
              - *Requirement:* Missing mandatory boolean attributes: `occluded` or `truncated`.
              - *Fix:* Assign proper True/False status.
            - **`RULE_A03` — Invalid Traffic Light Color (🔴 CRITICAL ERROR):**
              - *Requirement:* Traffic light color not in standard set `['red', 'yellow', 'green', 'none']`.
              - *Fix:* Assign valid state color.
            - **`RULE_C01` — Category Ontology & Spelling (🔴 ERROR / 🟡 WARNING):**
              - *Requirement:* Class name must strictly follow BDD100K ontology without spelling errors.
              - *Fix:* Map label to standard singular noun format.
            """)

        with r_tab4:
            st.markdown(r"""
            #### 🎬 Video Sequence Tracking Rules
            - **`RULE_T01` — Object Tracking Flicker (🟡 WARNING):**
              - *Formula:* Object exists in Frame $k-1$ and $k+1$, but omitted in Frame $k$.
              - *Cause:* Unintentional omission in middle video frames.
              - *Fix:* Annotate missing frame or enable linear interpolation.
            - **`RULE_T02` — Unrealistic Displacement Jump (🟡 WARNING):**
              - *Formula:* Box center shifts $> 35\%$ frame dimensions between adjacent frames.
              - *Cause:* Track ID misassignment or jumping coordinates.
              - *Fix:* Re-link correct Track ID or smooth trajectory.
            """)

        with r_tab5:
            st.markdown(r"""
            #### 🤖 AI Consensus Audit Rules
            - **`RULE_AI01` — AI Missed Object Detection (🔴 ERROR / 🟡 WARNING):**
              - *Description:* Multi-model YOLOv8 detects high-confidence vehicle or person without corresponding label.
              - *Confidence:* Confidence $\ge 60\%$ flagged as ERROR; $35\% - 60\%$ flagged as WARNING.
              - *Fix:* Inspect source image to verify genuine missed targets and add annotations.
            """)
