# Sổ quyết định

Ghi lại những gì đội đã chốt, và **vì sao**. Ba tuần sau không ai còn nhớ vì sao box lại vẽ
kiểu này — người mới vào đội lại càng không.

**Quyết định đã ghi thì không sửa nội dung.** Đổi ý thì ghi một quyết định mới, và chuyển
trạng thái quyết định cũ thành *Bị thay bởi QĐ-xxx*. Nhờ vậy vẫn truy được vì sao các job
cũ được gán theo cách cũ.

## Danh sách

| Mã | Quyết định | Ngày | Xuất phát từ | Trạng thái |
|---|---|---|---|---|
| [QĐ-001](#qđ-001) | Người ngồi sau xe máy có box `nguoi` riêng | 17/09/2026 | [P-001](problem-backlog-tuan-01.md#p-001) | Hiệu lực |
| [QĐ-002](#qđ-002) | Reviewer trả nguyên job khi mẫu kiểm có trên 10% ảnh sai | 19/09/2026 | Họp tuần 01 | Hiệu lực |
| [QĐ-003](#qđ-003) | Không tạo 3D box khi chỉ thấy trên 2D camera mà LiDAR có 0 điểm hoặc 1–2 điểm nhiễu | 03/10/2026 | [P-001](problem-backlog-tuan-03.md#p-001) (Mentor 1) | Hiệu lực |
| [QĐ-004](#qđ-004) | Chia nhỏ N box theo từng đoạn thẳng cho dải rào chắn thi công gấp khúc hoặc kéo dài | 03/10/2026 | [P-002](problem-backlog-tuan-03.md#p-002) (Mentor 1) | Hiệu lực |

> **Ghi chú Tuần 03 (28/09 – 04/10/2026):** Sau buổi làm việc với Mentor lần 1 ngày 03/10/2026, nhóm đã chốt được phương án xử lý chính thức cho 2 vướng mắc kỹ thuật 3D Cuboid và ban hành [QĐ-003](#qđ-003) và [QĐ-004](#qđ-004). Cả 4 annotator đã áp dụng chỉnh sửa nhãn tương ứng.

**Trạng thái:** Hiệu lực · Bị thay bởi QĐ-xxx · Huỷ (ghi lý do)

---

## QĐ-001

**Người ngồi sau xe máy có box `nguoi` riêng**

- **Ngày:** 17/09/2026
- **Người tham gia:** Nguyễn Thanh Đức (`2A202602279`) (chốt), Đoàn Văn Thắng (`2A202602327`), Hoàng Công Chứ (`2A202602187`), Trần Thị Thủy Tiên (`2A202602171`), Đào Ngọc Hiếu (`2A202602081`)
- **Xuất phát từ:** [P-001](problem-backlog-tuan-01.md#p-001)
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

**Không tạo 3D box khi chỉ thấy trên 2D camera mà LiDAR có 0 điểm hoặc 1–2 điểm nhiễu**

- **Ngày:** 03/10/2026
- **Người tham gia:** Đào Ngọc Hiếu (`2A202602081`) (Lead chốt), Hoàng Công Chứ (`2A202602187`), Trần Thị Thủy Tiên (`2A202602171`), Đoàn Văn Thắng (`2A202602327`), Nguyễn Thanh Đức (`2A202602279`) cùng Mentor buổi 1
- **Xuất phát từ:** [P-001](problem-backlog-tuan-03.md#p-001)
- **Bối cảnh:** Quan sát thấy người đi bộ hoặc ô tô ở xa trên 2D camera nhưng dữ liệu LiDAR chỉ có 0 điểm (Job #4053 frame 26) hoặc chỉ có 1–2 điểm nhiễu rời rạc (Job #4054 frame 35). Annotator phân vân có vẽ box phỏng đoán hay bỏ qua.
- **Các phương án đã cân nhắc:**
  1. *Vẽ box ước lượng dựa theo ảnh 2D* — không có cơ sở 3D thực tế, vi phạm nặng nguyên tắc gán nhãn 3D và sai tâm/kích thước/yaw. Loại.
  2. *Bỏ qua hoàn toàn nếu 0 điểm hoặc 1–2 điểm nhiễu; chỉ gán khi có cụm điểm tối thiểu (≥ 3–5 điểm)* — đúng tinh thần §1 & §4.4 của Guideline: "không tạo cuboid chỉ dựa trên ảnh 2D nếu không có cơ sở 3D". **Chọn.**
- **Quyết định:** Tuyệt đối không tạo 3D cuboid nếu đối tượng hoàn toàn không có điểm phản xạ (0 điểm) hoặc chỉ có 1–2 điểm laser nhiễu rời rạc trên point cloud. Chỉ dựng box khi có cụm điểm tối thiểu (≥ 3–5 điểm) khớp góc nhìn camera, căn đáy tiếp xúc ground plane và áp kích thước prior chuẩn.
- **Việc phải làm theo:**
  - [x] Hoàng Công Chứ rà lại Job #4053 frame 26, xác nhận không tạo box cho xe 0 điểm, tháo tag `can_xem_lai`
  - [x] Trần Thị Thủy Tiên rà lại Job #4054 frame 35, xác nhận không tạo box cho người chỉ có 1–2 điểm nhiễu, tháo tag `can_xem_lai`
  - [x] Thông báo toàn nhóm áp dụng cho đợt review chéo lần 2
- **Trạng thái:** Hiệu lực

## QĐ-004

**Chia nhỏ N box theo từng đoạn thẳng cho dải rào chắn thi công gấp khúc hoặc kéo dài**

- **Ngày:** 03/10/2026
- **Người tham gia:** Đào Ngọc Hiếu (`2A202602081`) (Lead chốt), Đoàn Văn Thắng (`2A202602327`), Nguyễn Thanh Đức (`2A202602279`), Hoàng Công Chứ (`2A202602187`), Trần Thị Thủy Tiên (`2A202602171`) cùng Mentor buổi 1
- **Xuất phát từ:** [P-002](problem-backlog-tuan-03.md#p-002)
- **Bối cảnh:** Rào chắn công trường (`barrier`) tại Job #4051 (frame 0–10) kéo dài và gấp khúc hình chữ L quanh lề đường, chưa rõ quy cách vẽ box nên annotator tạm hoãn gán dẫn đến thiếu label rào chắn.
- **Các phương án đã cân nhắc:**
  1. *Vẽ 1 box to bao trùm toàn bộ đường gấp khúc* — box phình to chứa toàn mặt đường (lỗi vi phạm §4.2) và làm sai lệch nghiêm trọng góc xoay yaw (§4.3 & §7). Loại.
  2. *Chia nhỏ thành N box tương ứng với N đoạn thẳng thẳng hàng* — mỗi box ôm sát một đoạn rào chắn thẳng, trục dài dọc theo dải rào, chuẩn xác yaw và kích thước theo §4.3 & §6. **Chọn.**
- **Quyết định:** Khi gặp dải rào chắn (`barrier`) kéo dài hoặc gấp khúc, bắt buộc chia nhỏ thành nhiều box thẳng hàng (N khúc gập/đoạn thẳng = N box). Mỗi box căn khít mép cụm điểm, hướng trục dài theo chiều dài của đoạn đó.
- **Việc phải làm theo:**
  - [x] Đoàn Văn Thắng gán bổ sung nhãn `barrier` cho các đoạn rào chắn tại Job #4051 (frame 0–10) theo quy tắc chia N box
  - [x] Nguyễn Thanh Đức kiểm tra đối chiếu khi review chéo lần 2 Job #4051; đã trả về yêu cầu Thắng sửa do rào chắn vẽ không cố định, số lượng khung box bị nhảy khác nhau giữa các frame
  - [ ] Đoàn Văn Thắng hoàn thiện khóa cố định số lượng khung box barrier (N box) và vị trí/kích thước đồng nhất qua toàn bộ 11 frames (0–10)
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
