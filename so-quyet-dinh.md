# Sổ quyết định

Ghi lại những gì đội đã chốt, và **vì sao**. Ba tuần sau không ai còn nhớ vì sao box lại vẽ
kiểu này — người mới vào đội lại càng không.

**Quyết định đã ghi thì không sửa nội dung.** Đổi ý thì ghi một quyết định mới, và chuyển
trạng thái quyết định cũ thành *Bị thay bởi QĐ-xxx*. Nhờ vậy vẫn truy được vì sao các job
cũ được gán theo cách cũ.

## Danh sách

| Mã | Quyết định | Ngày | Xuất phát từ | Trạng thái |
|---|---|---|---|---|
| [QĐ-001](#qđ-001) | Người ngồi sau xe máy có box `nguoi` riêng | 17/09/2026 | [P-001](problem-backlog.md#p-001) | Hiệu lực |
| [QĐ-002](#qđ-002) | Reviewer trả nguyên job khi mẫu kiểm có trên 10% ảnh sai | 19/09/2026 | Họp tuần 01 | Hiệu lực |
| [QĐ-003](#qđ-003) | Nguyên tắc xử lý khi thấy người, xe, vật thể trên 2D nhưng 3D không đủ căn cứ gán | 29/09/2026 | [P-004](problem-backlog.md#p-004) | Hiệu lực |
| [QĐ-004](#qđ-004) | Quy tắc phân tách box cho thanh chắn giao thông (barrier) dạng gấp khúc | 29/09/2026 | [P-005](problem-backlog.md#p-005) | Hiệu lực |

**Trạng thái:** Hiệu lực · Bị thay bởi QĐ-xxx · Huỷ (ghi lý do)

---

## QĐ-001

**Người ngồi sau xe máy có box `nguoi` riêng**

- **Ngày:** 17/09/2026
- **Người tham gia:** Nguyễn Thanh Đức (`2A202602279`) (chốt), Đoàn Văn Thắng (`2A202602327`), Hoàng Công Chứ (`2A202602187`), Trần Thị Thủy Tiên (`2A202602171`), Đào Ngọc Hiếu (`2A202602081`)
- **Xuất phát từ:** [P-001](problem-backlog.md#p-001)
- **Bối cảnh:** §3.2 của guideline nói mỗi người một box, nhưng hình minh hoạ lại vẽ chung một box. Hai annotator đang làm theo hai cách khác nhau.
- **Các phương án đã cân nhắc:**
  1. *Gộp chung một box với xe* — nhanh hơn, nhưng mất số người trên xe, trong khi dữ liệu dùng để đếm người tham gia giao thông. Loại.
  2. *Box `nguoi` riêng cho từng người* — đúng câu chữ §3.2 và giữ được số người. **Chọn.**
- **Quyết định:** Mỗi người trên xe máy, kể cả người ngồi sau chỉ lộ đầu, có một box `nguoi` riêng. Box xe máy vẫn vẽ như bình thường.
- **Việc phải làm theo:**
  - [x] Rà lại job 101, sửa 37 ảnh đã gộp (Đoàn Văn Thắng)
  - [x] Báo cả đội, ghim trong kênh chat của đội
- **Trạng thái:** Hiệu lực

## QĐ-002

**Reviewer trả nguyên job khi mẫu kiểm có trên 10% ảnh sai**

- **Ngày:** 19/09/2026
- **Người tham gia:** Nguyễn Thanh Đức (`2A202602279`) (chốt), Đoàn Văn Thắng (`2A202602327`)
- **Xuất phát từ:** Họp tổng kết tuần 01 — không phải từ backlog
- **Bối cảnh:** Job 101 bị sửa rải rác từng ảnh qua ba vòng review, tốn thời gian của cả hai bên.
- **Các phương án đã cân nhắc:**
  1. *Sửa từng ảnh như cũ* — ổn khi lỗi lẻ tẻ, nhưng khi lỗi có hệ thống thì reviewer đang làm hộ annotator. Loại.
  2. *Kiểm mẫu 20%, trên 10% sai thì trả nguyên job* — annotator tự rà cả job theo lỗi đã chỉ ra. **Chọn.**
- **Quyết định:** Reviewer kiểm ngẫu nhiên 20% ảnh của mỗi job. Trên 10% số ảnh kiểm bị sai thì trả nguyên job kèm danh sách lỗi mẫu; từ 10% trở xuống thì sửa từng ảnh.
- **Việc phải làm theo:**
  - [x] Áp dụng từ job 106 trở đi (Đoàn Văn Thắng)
- **Trạng thái:** Hiệu lực

## QĐ-003

**Nguyên tắc xử lý khi thấy người, xe, vật thể trên 2D nhưng 3D không đủ căn cứ gán**

- **Ngày:** 29/09/2026
- **Người tham gia:** Đào Ngọc Hiếu (`2A202602081`) (chốt), Đoàn Văn Thắng (`2A202602327`), Nguyễn Thanh Đức (`2A202602279`), Hoàng Công Chứ (`2A202602187`), Trần Thị Thủy Tiên (`2A202602171`)
- **Xuất phát từ:** [P-004](problem-backlog.md#p-004)
- **Bối cảnh:** Dữ liệu nuScenes gồm Point Cloud 3D kết hợp 6 camera 2D. Nhiều trường hợp người đi bộ, xe ô tô hoặc vật thể ở xa (>25–30m) nhìn thấy trên ảnh camera nhưng trên point cloud LiDAR chỉ có 0 điểm hoặc 1–2 điểm nhiễu rời rạc không đủ căn cứ xác định hình học 3D. Annotator phân vân có vẽ cuboid dựa theo camera hay không.
- **Các phương án đã cân nhắc:**
  1. *Vẽ cuboid chỉ dựa trên ảnh 2D camera* — vi phạm nguyên tắc cốt lõi §1 và điều cấm kỵ ở §4.4 ("Không tạo cuboid chỉ dựa trên ảnh 2D nếu không có cơ sở 3D hợp lý trong point cloud"). Gây lỗi nghiêm trọng về vị trí chiều sâu (depth) và độ cao mặt đất. **Loại.**
  2. *Bỏ qua toàn bộ vật thể ở xa* — có thể dẫn đến bỏ sót đối tượng quan trọng dù có cụm điểm 3D. **Loại.**
  3. *Quy tắc 3 cấp độ theo cơ sở 3D point cloud:*
     - **Mức 1 (0 điểm LiDAR hoặc 1–2 điểm nhiễu không đủ cơ sở hình học):** Tuyệt đối KHÔNG gán cuboid (§4.4: không vẽ mò theo ảnh 2D).
     - **Mức 2 (Có cụm điểm tối thiểu ≥ 3–5 điểm):** Dùng camera xác nhận đúng class, căn ground plane ở Side/Front view (§4.1), áp kích thước chuẩn (prior) của đối tượng (pedestrian: ~0.7x0.7x1.7m; car: ~4.5x1.9x1.6m), đáy đặt sát mặt đường.
     - **Mức 3 (Điểm quá phân tán, bị che khuất mập mờ):** Không tự ý vẽ; gắn cờ/tag `can_xem_lai` để Lead đối chiếu frame kế cận (temporal context) trước khi quyết định. **Chọn.**
- **Quyết định:** Áp dụng thống nhất quy tắc 3 cấp độ trên cho toàn bộ các class trong task #1504.
- **Việc phải làm theo:**
  - [x] Phổ biến quy tắc cho cả 4 annotator trong nhóm (Đào Ngọc Hiếu)
  - [x] 4 annotators rà soát và loại bỏ các box vẽ mò không đủ căn cứ 3D trong Job 4051–4054 (Đoàn Văn Thắng, Nguyễn Thanh Đức, Hoàng Công Chứ, Trần Thị Thủy Tiên)
- **Trạng thái:** Hiệu lực

## QĐ-004

**Quy tắc phân tách box cho thanh chắn giao thông (barrier) dạng gấp khúc**

- **Ngày:** 29/09/2026
- **Người tham gia:** Đào Ngọc Hiếu (`2A202602081`) (chốt), Nguyễn Thanh Đức (`2A202602279`), Hoàng Công Chứ (`2A202602187`)
- **Xuất phát từ:** [P-005](problem-backlog.md#p-005)
- **Bối cảnh:** Hàng rào chắn (`barrier`) thi công hoặc dải phân cách được dựng trải dọc theo hình gấp khúc (góc chữ L, góc cua ngã ba). Do 3D cuboid là hình hộp chữ nhật thẳng, chỉ có 1 góc quay yaw cố định.
- **Các phương án đã cân nhắc:**
  1. *Vẽ 1 cuboid bao hết cả cụm gấp khúc* — box sẽ cực kỳ rộng và chứa đầy khoảng trống mặt đường (vi phạm §4.2), đồng thời hướng trục dài (yaw) không thể khớp với cả hai nhánh rào (vi phạm nghiêm trọng §4.3 & §7 về lỗi sai yaw). **Loại.**
  2. *Chia thành nhiều box theo từng đoạn thẳng thẳng hàng (N khúc gấp = N box)* — mỗi đoạn thẳng thẳng hàng có 1 cuboid riêng. Trục dài của mỗi box xoay đúng theo chiều kéo dài của đoạn rào đó (§4.3), chiều rộng ôm khít bề dày rào, hai box tiếp giáp mép nhau tại góc bẻ (§6). **Chọn.**
- **Quyết định:** Tất cả thanh chắn giao thông (`barrier`) dạng gấp khúc hoặc uốn cong đều bắt buộc **chia thành nhiều box theo từng đoạn thẳng thẳng hàng**. Không bao giờ vẽ 1 box bao trùm đường gấp khúc. Tại góc bẻ, hai box đặt tiếp giáp khít mép nhau để không hở vật thể.
- **Việc phải làm theo:**
  - [x] Áp dụng sửa lại dải barrier tại frame 14 Job #4052 (Nguyễn Thanh Đức)
  - [x] Rà soát toàn bộ các frame có `barrier` trên cả 4 job (cả đội)
- **Trạng thái:** Hiệu lực

---

## Mẫu để copy

```markdown
## QĐ-NNN

**Quyết định trong một dòng**

- **Ngày:** dd/mm/yyyy
- **Người tham gia:** @ (chốt), @, @
- **Xuất phát từ:** [P-NNN](problem-backlog.md#p-nnn) | Họp tuần NN | …
- **Bối cảnh:** vì sao phải quyết định
- **Các phương án đã cân nhắc:**
  1. *Phương án* — ưu / nhược. Loại hoặc **Chọn.**
  2. *Phương án* — ưu / nhược. Loại hoặc **Chọn.**
- **Quyết định:** đủ rõ để người không dự họp vẫn làm đúng
- **Việc phải làm theo:**
  - [ ] việc (@người phụ trách)
- **Trạng thái:** Hiệu lực
```

Nhớ thêm một dòng vào bảng **Danh sách** ở đầu file, và đóng mục P-xxx tương ứng trong backlog.
