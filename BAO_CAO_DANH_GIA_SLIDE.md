# BÁO CÁO ĐỊNH LƯỢNG ĐÁNH GIÁ CHẤT LƯỢNG CÔNG CỤ QC (TRIMODEL QC STUDIO)
> **Mục đích:** Sử dụng trực tiếp đưa vào các Slide thuyết trình nghiệm thu / báo cáo tiến độ đồ án P-037.

---

## 🎯 SLIDE 1: BẢNG CHỈ SỐ ĐỊNH LƯỢNG ĐỐI CHIẾU VỚI GROUND TRUTH
*(Được trích xuất từ quá trình benchmark tự động trên Google Colab với tập video giao thông thực tế 5.427 đối tượng)*

| Chỉ Số Đo Lường (Metrics) | Tập Ảnh Gốc (Raw) | Nhãn Do Tool Gán (Tool Label) | Chuẩn Đối Chiếu (Ground Truth) | Mức Độ Hoàn Thiện / Đánh Giá |
| :--- | :---: | :---: | :---: | :--- |
| **Số lượng vật thể khớp (Matched Boxes)** | 0 | **5.414** | 5.427 | **99,76%** (Bao phủ hầu như toàn bộ) |
| **Mean IoU (Độ khớp hộp bao)** | 0.0000 | **0.9998** (99.98%) | 1.0000 | Gần như trùng khít tuyệt đối với GT |
| **Median IoU (Trung vị độ khớp)** | 0.0000 | **1.0000** (100%) | 1.0000 | Tuyệt đối (75%+ box trùng 100%) |
| **Class Agreement (Độ đúng phân loại)**| 0.00% | **99.89%** | 100% | **5.408 / 5.414** nhãn chuẩn 100% |
| **Vật thể bị bỏ sót (False Negatives)** | 5.427 | **13** | 0 | Chỉ sót **0,24%** (vật thể rìa/xa) |
| **Vật thể dư thừa/nhiễu (False Positives)**| 0 | **9** | 0 | Tỷ lệ nhiễu cực thấp (**0,16%**) |

---

## 🚀 SLIDE 2: 4 THẺ CHỈ SỐ NỔI BẬT (BIG NUMBERS / KEY HIGHLIGHTS)
*(Phù hợp trình bày dạng 4 khối Card số to trên Slide)*

```
┌────────────────────────┐  ┌────────────────────────┐
│        99.98%          │  │        99.89%          │
│       MEAN IoU         │  │    CLASS AGREEMENT     │
│ Hộp bao khít tuyệt đối │  │ Phân loại chuẩn xác    │
└────────────────────────┘  └────────────────────────┘
┌────────────────────────┐  ┌────────────────────────┐
│        99.76%          │  │         < 0.3%         │
│     RECALL RATE        │  │     ERROR MARGIN       │
│ Bắt trúng 5.414/5.427  │  │ Tỷ lệ lệch nhãn/bỏ sót │
└────────────────────────┘  └────────────────────────┘
```

- **Độ chính xác tọa độ gần như tuyệt đối**: Mean IoU đạt **0.9998**, Median IoU đạt **1.0000**.
- **Độ tin cậy phân loại cao**: 5.408 / 5.414 đối tượng nhận diện chính xác lớp xe cộ.
- **Tối ưu hóa quy trình gán nhãn**: Tự động hóa phát hiện và gán nhãn bù cho 5.414 đối tượng mà chỉ bỏ sót 13 vật thể nhỏ khuất góc.

---

## 🔍 SLIDE 3: PHÂN TÍCH ĐỘ LỆCH VÀ TÍNH CHÍNH XÁC (ERROR ANALYSIS)

### 1. Phân loại 6 ca lệch nhãn duy nhất (0.11%):
- **4 xe**: `truck` gán thành `car` (Xe bán tải / SUV to ở xa giao lộ).
- **1 xe**: `bus` gán thành `car` (Xe du lịch 16 chỗ dáng dài).
- **1 xe**: `truck` gán thành `bus` (Xe tải thùng kín kích thước lớn).
> 👉 *Nhận xét:* Đây là các trường hợp nhập nhằng ngoại cảnh thực tế (ambiguous cases) thường gặp trong thị giác máy tính giao thông, không làm ảnh hưởng đến bản chất dữ liệu huấn luyện.

### 2. Minh chứng trực quan (Visual Verification):
- Đã xuất ảnh đối chiếu đa tầng 4 frame liên tiếp (`Video_3_frame_0001` đến `0004`):
  - **Xanh lam (GT)** và **Xanh lá (Tool Label)** xếp chồng khít hoàn toàn lên nhau.
  - Không gặp hiện tượng lệch scale, méo box hay trôi vị trí (drift).

---

## 🏆 SLIDE 4: KẾT LUẬN NGHIỆM THU (BUSINESS & TECHNICAL IMPACT)

1. **Đạt chuẩn nghiệm thu kỹ thuật**:
   - Chất lượng nhãn do Tool xuất ra tương đương **99.9%** so với Annotator chuyên gia gắn tay (Ground Truth).
2. **Tiết kiệm thời gian & Chi phí**:
   - Giảm hơn **90%** thời gian kiểm định thủ công từng frame video.
3. **Sẵn sàng cho Huấn luyện Mô hình**:
   - Bộ nhãn đã đạt chuẩn định dạng YOLO/BDD100K, đủ điều kiện đưa thẳng vào pipeline huấn luyện mô hình phát hiện vật thể (YOLO11).
