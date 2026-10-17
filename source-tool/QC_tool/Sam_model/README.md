# Phân Hệ Nghiên Cứu Mô Hình Phân Đoạn SAM-2 (Sam_model)

> **Nhánh phụ trách:** Đoàn Văn Thắng (`2A202602327`) & Nguyễn Thanh Đức (`2A202602279`)

---

## 1. Giới thiệu

Phân hệ này tập trung nghiên cứu ứng dụng mô hình phân đoạn nền tảng **SAM-2 (Segment Anything Model 2)** kết hợp mô hình phát hiện vật thể zero-shot **OwlViT** nhằm:
- Tự động sinh đường viền đa giác phân đoạn (Polygon Segmentation) từ gợi ý Bounding Box.
- Thử nghiệm trên tập dữ liệu hình ảnh camera xe ban đêm (`xanh_sm_night.zip`).
- Khảo sát khả năng tích hợp hỗ trợ cho các bài toán kiểm định BDD100K 2D Segmentation.

---

## 2. Cấu trúc thư mục

- `sam2_model.ipynb`: Jupyter Notebook thực nghiệm (chạy trên Google Colab với GPU hỗ trợ CUDA).
- `xanh_sm_night.zip`: Tập dữ liệu ảnh ban đêm phục vụ kiểm thử mô hình.

---

## 3. Hướng dẫn chạy thực nghiệm

Mở tệp `sam2_model.ipynb` trên Google Colab:
1. Chọn Runtime: Python 3 với GPU T4 hoặc cao hơn.
2. Cài đặt các thư viện yêu cầu:
   ```bash
   pip install git+https://github.com/facebookresearch/sam2.git
   pip install transformers torch torchvision
   ```
3. Giải nén tập dữ liệu `xanh_sm_night.zip` và thực thi tuần tự các cells trong notebook.
