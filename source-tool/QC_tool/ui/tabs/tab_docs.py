from __future__ import annotations
import streamlit as st


def render_tab_docs():
    """Render Tab 4: Quy chuẩn 12 Rules & Hướng dẫn sửa lỗi cho Annotator."""
    st.markdown("""
    <div style="margin-bottom: 16px;">
        <h3 style="margin: 0; color: #f8fafc; font-size: 1.25rem;">📖 Quy Chuẩn 12 Rules & Hướng Dẫn Sửa Lỗi Cho Annotator</h3>
        <p style="margin: 2px 0 0 0; color: #94a3b8; font-size: 0.85rem;">Quy định chuẩn hóa dữ liệu 2D Bounding Box, Polygon Segmentation và Video Tracking (Đề tài N2-04A)</p>
    </div>
    """, unsafe_allow_html=True)

    r_tab1, r_tab2, r_tab3, r_tab4, r_tab5 = st.tabs([
        "📐 BBox Rules (B01-B04)",
        "📉 Polygon Rules (P01-P03)",
        "👥 Attribute Rules (A01-A03)",
        "🎬 Video Sequence (T01-T02)",
        "🤖 AI Cross-check (AI01)",
    ])

    with r_tab1:
        st.markdown(r"""
        #### 📐 Nhóm Luật Bounding Box (Phụ trách: Nguyễn Thanh Đức)
        - **`RULE_B01` — Out of Bounds (🔴 ERROR):**
          - *Công thức:* Tọa độ vượt ngoài kích thước ảnh ($x_1 < 0, y_1 < 0, x_2 > W, y_2 > H$).
          - *Nguyên nhân:* Vẽ tràn viền ảnh hoặc kéo chuột trượt ra mép canvas.
          - *Cách sửa:* Thu nhỏ box hoặc kéo box nằm trọn trong giới hạn $[0, W] \times [0, H]$.
        - **`RULE_B02` — Inverted / Zero Box (🔴 ERROR):**
          - *Công thức:* $x_2 \le x_1$ hoặc $y_2 \le y_1$ hoặc diện tích bằng 0.
          - *Nguyên nhân:* Bị đảo ngược điểm kéo chuột hoặc click vô tình tạo box rỗng.
          - *Cách sửa:* Xóa box 0px và vẽ lại sao cho $x_2 > x_1$ và $y_2 > y_1$.
        - **`RULE_B03` — Too Small Box (🟡 WARNING):**
          - *Công thức:* Diện tích $w \times h < 64\text{px}^2$.
          - *Nguyên nhân:* Chấm nhầm điểm ảnh rác, nhiễu hoặc vật thể quá xa không thể nhận diện.
          - *Cách sửa:* Nếu là vật thể thật hãy giữ lại; nếu là click nhầm hãy xóa bỏ.
        - **`RULE_B04` — Abnormal Aspect Ratio (🟡 WARNING):**
          - *Công thức:* Tỉ lệ $w/h > 25$ hoặc $h/w > 25$.
          - *Nguyên nhân:* Kéo dẹt box bất thường, box biến dạng thành 1 đường thẳng mảnh.
          - *Cách sửa:* Căn chỉnh lại chiều rộng và chiều cao bao khít vật thể thực tế.
        - **`RULE_B05` — Extreme Scale / Screen Filler (🟡 WARNING):**
          - *Công thức:* Diện tích box chiếm $> 96\%$ diện tích toàn khung hình.
          - *Nguyên nhân:* Kéo nhầm chuột từ góc này sang góc kia màn hình bao toàn ảnh.
          - *Cách sửa:* Xóa box nếu là thao tác vô tình kéo toàn cảnh.
        """)

    with r_tab2:
        st.markdown(r"""
        #### 📉 Nhóm Luật Polygon Topology (Phụ trách: Hoàng Công Chứ)
        - **`RULE_P01` — Insufficient Vertices (🔴 ERROR):**
          - *Công thức:* Số đỉnh polygon $< 3$.
          - *Nguyên nhân:* Bấm enter kết thúc vẽ khi mới chỉ có 1 hoặc 2 điểm.
          - *Cách sửa:* Đa giác khép kín cần ít nhất 3 đỉnh. Hãy vẽ bổ sung thêm điểm hoặc dùng Auto-Fix sinh từ BBox.
        - **`RULE_P02` — Self-Intersection (🔴 ERROR):**
          - *Công thức:* Đa giác tự cắt viền (xoắn hình nơ, phức hợp).
          - *Nguyên nhân:* Thứ tự các đỉnh bị đảo lộn chéo nhau khi vẽ tay nhanh.
          - *Cách sửa:* Dùng 1-Click Auto-Fix (Shapely unknotting) hoặc vẽ lại polygon đơn giản theo chiều kim đồng hồ.
        - **`RULE_P03` — Mask vs Box Mismatch (🟡 WARNING):**
          - *Công thức:* $\text{IoU}(\text{Box}(\text{poly}), \text{box2d}) < 0.70$.
          - *Nguyên nhân:* BBox và Segmentation mask của cùng 1 vật thể không ăn khớp nhau.
          - *Cách sửa:* Điều chỉnh lại BBox sao cho bao khít với ranh giới của polygon (Auto-Fix có thể tự căn chuẩn).
        - **`RULE_P04` — Spike or Duplicate Vertices (🟡 WARNING):**
          - *Hiện tượng:* Đa giác có 2 đỉnh kế tiếp trùng vị trí (< 0.8px) hoặc góc nhọn gấp khúc dị thường (< 3.5°).
          - *Cách sửa:* Xóa đỉnh trùng hoặc làm mượt góc đa giác.
        """)

    with r_tab3:
        st.markdown(r"""
        #### 👥 Nhóm Luật Thuộc Tính & Trùng Lặp (Phụ trách: Trần Thị Thủy Tiên)
        - **`RULE_A01` — Duplicate Object (🔴 ERROR):**
          - *Công thức:* 2 box cùng class chồng đè lên nhau với $\text{IoU} > 0.85$.
          - *Nguyên nhân:* Annotator vẽ đè 2 lần cho cùng một vật thể mà quên xóa nhãn cũ.
          - *Cách sửa:* Kiểm tra danh sách nhãn và xóa bớt 1 trong 2 box trùng lặp.
        - **`RULE_A02` — Missing Attributes (🟡 WARNING):**
          - *Yêu cầu:* Thiếu 2 thuộc tính bắt buộc là `occluded` (bị che khuất) hoặc `truncated` (bị cắt xén).
          - *Cách sửa:* Mở panel thuộc tính và đánh dấu giá trị True/False chính xác.
        - **`RULE_A03` — Traffic Light Color (🔴 ERROR):**
          - *Yêu cầu:* Vật thể là `traffic light` nhưng thuộc tính `color` không nằm trong `['red', 'yellow', 'green', 'none']`.
          - *Cách sửa:* Khai báo đúng màu sắc trạng thái của đèn giao thông.
        - **`RULE_C01` — Category Ontology & Spelling (🔴 ERROR / 🟡 WARNING):**
          - *Yêu cầu:* Tên class phải thuộc bộ nhãn BDD100K; không được để trống hoặc gõ sai chính tả (ví dụ: `cars` -> `car`, `traffic_light` -> `traffic light`).
          - *Cách sửa:* Đổi lại đúng danh từ số ít theo quy chuẩn BDD100K.
        """)

    with r_tab4:
        st.markdown(r"""
        #### 🎬 Nhóm Luật Chuỗi Video Tracking (Phụ trách: Đào Ngọc Hiếu)
        - **`RULE_T01` — Object Flicker / Lost Track (🟡 WARNING):**
          - *Hiện tượng:* Vật thể xuất hiện ở Frame $k-1$ và $k+1$ nhưng biến mất ở Frame $k$.
          - *Nguyên nhân:* Annotator bị sót nhãn ở khung hình giữa chuỗi.
          - *Cách sửa:* Bổ sung nhãn liên tục hoặc dùng tính năng nội suy (interpolation).
        - **`RULE_T02` — Position Drift / Sudden Jump (🟡 WARNING):**
          - *Hiện tượng:* Box bị nhảy vọt vị trí bất thường ($> 35\%$ kích thước khung hình) giữa 2 frame liên tiếp.
          - *Nguyên nhân:* Gán nhầm ID vật thể hoặc nhảy nhầm tọa độ box.
          - *Cách sửa:* Kiểm tra ID liên kết hoặc căn chỉnh lại tọa độ cho mượt mà.
        """)

    with r_tab5:
        st.markdown(r"""
        #### 🤖 Nhóm Trợ Lý AI Cross-check (Tích hợp: YOLOv8)
        - **`RULE_AI01` — AI Missed Object (🔴 ERROR / 🟡 WARNING):**
          - *Hiện tượng:* AI quét ảnh gốc và phát hiện xe, người, xe buýt, xe tải nhưng trong file nhãn chưa có BBox tương ứng.
          - *Độ tin cậy:* Confidence $\ge 60\%$ xếp loại ERROR; $35\% - 60\%$ xếp loại WARNING.
          - *Cách sửa:* Đối chiếu với ảnh gốc xem có phải vật thể thật bị bỏ sót không, nếu có hãy vẽ bổ sung nhãn.
        """)
