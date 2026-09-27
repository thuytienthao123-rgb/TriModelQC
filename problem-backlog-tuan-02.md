# Problem backlog · Tuần 02 (21/09 – 27/09/2026)

Những chỗ gặp trong lúc gán nhãn mà **guideline chưa trả lời được**, cộng các pain point về công cụ trong Tuần 02.

Ghi ngay khi gặp, kể cả lúc chưa biết xử lý thế nào. Một edge case không được ghi lại thì mỗi người sẽ tự xử lý theo một kiểu — và đó là nguồn lớn nhất của nhãn không nhất quán.

## Danh sách

| Mã | Tóm tắt | Loại | Mục guideline | Trạng thái | Kết quả |
|---|---|---|---|---|---|
| [P-001](#p-001) | Job #2677: Point 6 khó xác định khớp vai (`.jpg`) | Guideline chưa nói tới | — | 🟢 Đã đóng | Theo mentor hướng dẫn |
| [P-002](#p-002) | Job #2676: Point 8 bị che khuất khó ước lượng | Guideline chưa nói tới | — | 🟢 Đã đóng | Theo mentor hướng dẫn |
| [P-003](#p-003) | Job #2678: Khoảng cách các point 43-44-45 và 47-48-49 khớp ảnh nhưng sai tỉ lệ | Pain point công cụ | — | 🟢 Đã đóng | Theo mentor hướng dẫn |

**Loại**

| Loại | Nghĩa là |
|---|---|
| Guideline chưa nói tới | Tình huống không có trong guideline |
| Guideline mơ hồ | Đọc guideline ra được hai cách hiểu trở lên |
| Guideline mâu thuẫn | Hai mục trong guideline nói ngược nhau |
| Pain point công cụ | Guideline rõ, nhưng làm trên CVAT chậm hoặc dễ sai |

**Trạng thái:** 🔴 Mở · 🗣️ Đang bàn · ↗️ Hỏi BTC · ✅ Đã chốt (trỏ sang QĐ) · 🛠️ Làm tool (trỏ sang `source-tool/`) · ⚪ Bỏ (ghi lý do)

---

## P-001

**Job #2677: Point 6 khó xác định vị trí khớp vai (human-body-keypoints pre-label)**

- **Loại:** Guideline chưa nói tới
- **Mục guideline:** —
- **Người phát hiện:** Đoàn Văn Thắng (`2A202602327`) · 23/09/2026
- **Link CVAT:** https://cvat.note.transformerlabs.ai/tasks/459/jobs/2677?frame=35 (Job #2677, frame 35)
- **Tên & đuôi file ảnh:** `000420_vp4_run2_2018-05-22-14-25-04.kinect_color_f013920.jpg`
- **Đường dẫn file ảnh đầy đủ:** `w2/human-body-keypoints-prelabel/G05/000420_vp4_run2_2018-05-22-14-25-04.kinect_color_f013920.jpg`
- **Mô tả:** Trong ảnh `000420_vp4_run2_2018-05-22-14-25-04.kinect_color_f013920.jpg` tại Job #2677 (Task 459, frame 35), point 6 (vị trí khớp vai) rất khó xác định chính xác do tư thế người ngồi, góc chụp và quần áo che khuất vị trí giải phẫu chuẩn của vai.
- **Hướng xử lý:** Theo mentor hướng dẫn:
  1. Ước lượng vị trí khớp vai dựa trên tương quan giải phẫu với các điểm lân cận (cổ/khuỷu tay).
  2. Đánh dấu thuộc tính che khuất (`occluded`).
- **Trạng thái:** 🟢 Đã đóng
- **Kết quả:** Đã xử lý theo hướng dẫn của mentor

## P-002

**Job #2676: Point 8 bị che khuất khó ước lượng vị trí (human-body-keypoints pre-label)**

- **Loại:** Guideline chưa nói tới
- **Mục guideline:** —
- **Người phát hiện:** Đoàn Văn Thắng (`2A202602327`) · 23/09/2026
- **Link CVAT:** https://cvat.note.transformerlabs.ai/tasks/459/jobs/2676?frame=25 (Job #2676, frame 25)
- **Mô tả:** Tại Job #2676 (Task 459, frame 25), point 8 bị vật cản hoặc tư thế của đối tượng che khuất, rất khó ước lượng chính xác vị trí giải phẫu thực tế.
- **Hướng xử lý:** Theo mentor hướng dẫn:
  1. Ước lượng vị trí tiềm năng dựa trên hướng xương và các khớp liên quan lân cận.
  2. Gắn cờ che khuất (`occluded`).
- **Trạng thái:** 🟢 Đã đóng
- **Kết quả:** Đã xử lý theo hướng dẫn của mentor

## P-003

**Job #2678: Khoảng cách các point 43-44-45 và 47-48-49 khớp ảnh nhưng sai tỉ lệ (human-face)**

- **Loại:** Pain point công cụ
- **Mục guideline:** —
- **Người phát hiện:** Nguyễn Thanh Đức (`2A202602279`) · 23/09/2026
- **Link CVAT:** https://cvat.note.transformerlabs.ai/tasks/460/jobs/2678?frame=1 (Job #2678, frame 1)
- **Mô tả:** Tại Job #2678, nếu căn khoảng cách giữa cách điểm 43-44-45 và 47-48-49 khớp ảnh nhưng bị sai tỉ lệ trong guideline và ngược lại
- **Hướng xử lý:** Theo mentor hướng dẫn:
  1. Ước lượng toạ độ và đặt các điểm theo ảnh thực tế để đảm bảo độ khớp với khuôn mặt đối tượng.
- **Trạng thái:** 🟢 Đã đóng
- **Kết quả:** Đã xử lý theo hướng dẫn của mentor

---

## Mẫu để copy

```markdown
## P-NNN

**Tóm tắt một dòng**

- **Loại:** Guideline chưa nói tới | Guideline mơ hồ | Guideline mâu thuẫn | Pain point công cụ
- **Mục guideline:** §
- **Người phát hiện:** @ · dd/mm/yyyy
- **Link CVAT / File ảnh:** (bỏ trống nếu không có)
  - https://…/tasks/<id>/jobs/<id>?frame=<n> — frame này có gì
- **Mô tả:**
- **Các cách hiểu:** (với pain point công cụ thì ghi **Hướng đang cân nhắc:**)
  1.
  2.
- **Xử lý tạm trong lúc chờ:**
- **Kết quả:** 🔴 Mở
```

Nhớ thêm một dòng vào bảng **Danh sách** ở đầu file.
