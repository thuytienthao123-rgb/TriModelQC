"""
cvat_bridge.py — Module kết nối và đồng bộ 2 chiều giữa TriModel QC và CVAT.
Hỗ trợ:
1. Đọc trực tiếp Annotations từ CVAT (local CVAT hoặc cvat.ai) qua REST API.
2. Nạp nhãn về hệ thống QC để chạy 15 rules + AI Tri-Model Ensemble.
3. Nạp ngược lại CVAT (Two-way Push): Đẩy các box bổ sung, polygon vừa sinh tự động
   vào trực tiếp Job trên CVAT (PATCH /api/jobs/{id}/annotations).
4. Đẩy danh sách lỗi thành Issue lên CVAT (POST /api/issues).
5. Chế độ Mô phỏng Offline (Mock Mode) giúp kiểm thử local tức thì mà không cần server CVAT.
"""

from __future__ import annotations
import io
import json
import logging
from pathlib import Path
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image, ImageDraw

from qc.models import FrameData, LabeledObject, BBox2D, Polygon2D, QCReport, QCError

logger = logging.getLogger(__name__)


class CVATBridge:
    def __init__(self, server_url: str = "https://app.cvat.ai", token: str = ""):
        self.server_url = server_url.rstrip("/")
        self.token = token.strip()

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
        }
        if self.token:
            # CVAT hỗ trợ cả Token và Bearer
            if self.token.lower().startswith("token ") or self.token.lower().startswith("bearer "):
                headers["Authorization"] = self.token
            else:
                headers["Authorization"] = f"Token {self.token}"
        return headers

    def _request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Tuple[bool, Any]:
        url = f"{self.server_url}{endpoint}"
        req = urllib.request.Request(url, method=method, headers=self._headers())
        body = json.dumps(data).encode("utf-8") if data is not None else None

        try:
            with urllib.request.urlopen(req, data=body, timeout=15) as resp:
                resp_text = resp.read().decode("utf-8")
                if resp_text:
                    return True, json.loads(resp_text)
                return True, {}
        except urllib.error.HTTPError as e:
            try:
                err_content = json.loads(e.read().decode("utf-8"))
            except Exception:
                err_content = str(e)
            return False, f"HTTP {e.code}: {err_content}"
        except urllib.error.URLError as e:
            return False, f"Connection Error: {e.reason}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def get_job_info(self, job_id: int) -> Tuple[bool, Any]:
        """Lấy thông tin chi tiết của Job từ CVAT."""
        return self._request("GET", f"/api/jobs/{job_id}")

    def get_task_labels(self, task_id: int) -> Tuple[bool, Any]:
        """Lấy danh sách nhãn (labels) của Task để ánh xạ name <-> label_id."""
        labels_list = []
        # 1. Thử gọi trực tiếp /api/labels?task_id={task_id} (CVAT v2.2+ chuẩn)
        ok_l, res_l = self._request("GET", f"/api/labels?task_id={task_id}")
        if ok_l:
            if isinstance(res_l, list):
                labels_list = res_l
            elif isinstance(res_l, dict) and "results" in res_l:
                labels_list = res_l["results"]

        # 2. Dự phòng lấy từ /api/tasks/{task_id} (CVAT cũ hơn)
        if not labels_list:
            ok, res = self._request("GET", f"/api/tasks/{task_id}")
            if ok and isinstance(res, dict):
                raw_labels = res.get("labels", [])
                if isinstance(raw_labels, list):
                    labels_list = raw_labels

        label_map = {}
        for l in labels_list:
            if isinstance(l, dict):
                lid = l.get("id")
                lname = l.get("name")
                if lid is not None and lname:
                    label_map[lname.lower()] = lid
                    label_map[lid] = lname
        return True, label_map

    def fetch_job_annotations(self, job_id: int) -> Tuple[bool, Any]:
        """Lấy danh sách shapes (BBoxes, Polygons) từ Job."""
        return self._request("GET", f"/api/jobs/{job_id}/annotations")

    def fetch_frame_image(self, job_id: int, frame_idx: int, quality: str = "compressed") -> Optional[Image.Image]:
        """Tải trực tiếp ảnh khung hình từ CVAT Job qua REST API."""
        url = f"{self.server_url}/api/jobs/{job_id}/data?type=frame&number={frame_idx}&quality={quality}"
        req = urllib.request.Request(url, method="GET", headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = resp.read()
                return Image.open(io.BytesIO(data)).convert("RGB")
        except Exception as e:
            logger.warning("Không thể tải ảnh frame %s từ CVAT Job %s: %s", frame_idx, job_id, e)
            return None

    def fetch_job_as_frames(self, job_id: int, fetch_images: bool = True) -> Tuple[bool, List[FrameData], Dict[str, Any]]:
        """
        Kéo toàn bộ nhãn và ảnh khung hình từ Job trên CVAT, chuyển đổi sang List[FrameData] chuẩn của TriModel QC.
        Tự động nạp ảnh từ CVAT để Trợ lý AI có thể phát hiện xe bị bỏ sót (MISSED) và hiển thị trực quan.
        """
        # 1. Lấy thông tin job để biết task_id và khoảng frame
        ok_job, job_data = self.get_job_info(job_id)
        task_id = job_data.get("task_id") if (ok_job and isinstance(job_data, dict)) else None

        # 2. Lấy label map từ task
        label_map: Dict[Any, Any] = {}
        if task_id:
            ok_lbl, lmap = self.get_task_labels(task_id)
            if ok_lbl and isinstance(lmap, dict):
                label_map = lmap

        # 3. Kéo annotations
        ok_ann, ann_data = self.fetch_job_annotations(job_id)
        if not ok_ann or not isinstance(ann_data, dict):
            return False, [], {"error": ann_data}

        shapes = ann_data.get("shapes", [])
        tracks = ann_data.get("tracks", [])

        # Gom nhóm theo frame_id
        frames_dict: Dict[int, List[LabeledObject]] = {}

        # Parse shapes tĩnh
        for s in shapes:
            f_idx = s.get("frame", 0)
            if f_idx not in frames_dict:
                frames_dict[f_idx] = []

            s_type = s.get("type", "rectangle")
            s_id = str(s.get("id", f"obj_{len(frames_dict[f_idx])+1}"))
            lbl_id = s.get("label_id")
            category = label_map.get(lbl_id, f"label_{lbl_id}") if label_map else f"class_{lbl_id}"
            points = s.get("points", [])

            # Thuộc tính occluded / truncated
            attrs = {
                "occluded": bool(s.get("occluded", False)),
                "truncated": False,
            }
            for a in s.get("attributes", []):
                aname = str(a.get("name", "")).lower()
                aval = a.get("value")
                if "trunc" in aname:
                    attrs["truncated"] = (str(aval).lower() in ("true", "1", "yes"))
                elif "trafficlight" in aname or "color" in aname:
                    attrs["trafficLightColor"] = str(aval)

            box2d = None
            poly2d = None

            if s_type == "rectangle" and len(points) >= 4:
                x1, y1, x2, y2 = points[0], points[1], points[2], points[3]
                box2d = BBox2D(x1=min(x1, x2), y1=min(y1, y2), x2=max(x1, x2), y2=max(y1, y2))
            elif s_type == "polygon" and len(points) >= 6:
                verts = [(points[i], points[i+1]) for i in range(0, len(points), 2)]
                poly2d = Polygon2D(vertices=verts)
                box2d = poly2d.bounding_box()

            if box2d or poly2d:
                frames_dict[f_idx].append(LabeledObject(
                    id=s_id,
                    category=category,
                    box2d=box2d,
                    poly2d=poly2d,
                    attributes=attrs,
                ))

        # Parse tracks (chuỗi video tracking)
        for tr in tracks:
            tr_id = str(tr.get("id", f"track_{len(frames_dict)+1}"))
            lbl_id = tr.get("label_id")
            category = label_map.get(lbl_id, f"label_{lbl_id}") if label_map else f"class_{lbl_id}"
            for s in tr.get("shapes", []):
                if s.get("outside", False):
                    continue
                f_idx = s.get("frame", 0)
                if f_idx not in frames_dict:
                    frames_dict[f_idx] = []
                s_type = s.get("type", "rectangle")
                points = s.get("points", [])
                attrs = {"occluded": bool(s.get("occluded", False)), "truncated": False}
                for a in s.get("attributes", []):
                    aname = str(a.get("name", "")).lower()
                    aval = a.get("value")
                    if "trunc" in aname:
                        attrs["truncated"] = (str(aval).lower() in ("true", "1", "yes"))

                box2d = None
                poly2d = None
                if s_type == "rectangle" and len(points) >= 4:
                    x1, y1, x2, y2 = points[0], points[1], points[2], points[3]
                    box2d = BBox2D(x1=min(x1, x2), y1=min(y1, y2), x2=max(x1, x2), y2=max(y1, y2))
                elif s_type == "polygon" and len(points) >= 6:
                    verts = [(points[i], points[i+1]) for i in range(0, len(points), 2)]
                    poly2d = Polygon2D(vertices=verts)
                    box2d = poly2d.bounding_box()

                if box2d or poly2d:
                    frames_dict[f_idx].append(LabeledObject(
                        id=f"{tr_id}_{f_idx}",
                        category=category,
                        box2d=box2d,
                        poly2d=poly2d,
                        attributes=attrs,
                    ))

        # Đảm bảo các frame trong khoảng start_frame..stop_frame đều có mặt kể cả khi người dùng xóa sạch nhãn
        if ok_job and isinstance(job_data, dict):
            start_f = int(job_data.get("start_frame", 0))
            stop_f = int(job_data.get("stop_frame", max(frames_dict.keys()) if frames_dict else 0))
            for f_i in range(start_f, stop_f + 1):
                if f_i not in frames_dict:
                    frames_dict[f_i] = []

        # Xây dựng danh sách FrameData & Tải ảnh khung hình tương ứng
        frames_res: List[FrameData] = []
        image_map: Dict[str, Image.Image] = {}

        for f_idx in sorted(frames_dict.keys()):
            fname = f"cvat_job{job_id}_frame_{f_idx:04d}.jpg"
            img = None
            if fetch_images:
                img = self.fetch_frame_image(job_id, f_idx)

            if img is not None:
                image_map[fname] = img
                image_map[Path(fname).stem] = img
                fw, fh = img.size
            else:
                fw, fh = 1920, 1080

            frames_res.append(FrameData(
                name=fname,
                objects=frames_dict[f_idx],
                width=fw,
                height=fh,
            ))

        meta_info = {
            "job_id": job_id,
            "task_id": task_id,
            "total_shapes": len(shapes) + sum(len(tr.get("shapes", [])) for tr in tracks),
            "total_frames": len(frames_res),
            "label_map": label_map,
            "image_map": image_map,
        }
        return True, frames_res, meta_info

    def push_healed_annotations_to_job(
        self,
        job_id: int,
        frames: List[FrameData],
        label_map: Optional[Dict[str, int]] = None,
    ) -> Tuple[bool, Any]:
        """
        Nạp ngược lại CVAT (Two-Way Sync):
        Gửi các Bounding Box và Polygon mới/đã sửa từ TriModel QC sang Job trên CVAT qua PATCH /api/jobs/{id}/annotations?action=create
        """
        shapes_payload = []
        lmap = label_map or {}

        for f_idx, fr in enumerate(frames):
            for obj in fr.objects:
                # Tìm label_id phù hợp
                cat_lower = obj.category.lower()
                lid = lmap.get(cat_lower, 1)

                # Nạp BBox nếu có
                if obj.box2d:
                    shapes_payload.append({
                        "type": "rectangle",
                        "frame": f_idx,
                        "label_id": lid,
                        "points": [
                            float(round(obj.box2d.x1, 2)),
                            float(round(obj.box2d.y1, 2)),
                            float(round(obj.box2d.x2, 2)),
                            float(round(obj.box2d.y2, 2)),
                        ],
                        "occluded": bool(obj.attributes.get("occluded", False)),
                        "outside": False,
                        "z_order": 0,
                    })

                # Nạp Polygon nếu có
                if obj.poly2d and len(obj.poly2d.vertices) >= 3:
                    pts_flat = []
                    for vx, vy in obj.poly2d.vertices:
                        pts_flat.extend([float(round(vx, 2)), float(round(vy, 2))])
                    shapes_payload.append({
                        "type": "polygon",
                        "frame": f_idx,
                        "label_id": lid,
                        "points": pts_flat,
                        "occluded": bool(obj.attributes.get("occluded", False)),
                        "outside": False,
                        "z_order": 0,
                    })

        if not shapes_payload:
            return False, "Không có nhãn nào để nạp vào CVAT."

        # CVAT API: PUT /api/jobs/{id}/annotations thay thế toàn bộ nhãn đã chữa lành cho job
        endpoint = f"/api/jobs/{job_id}/annotations"
        payload = {
            "version": 0,
            "tags": [],
            "shapes": shapes_payload,
            "tracks": [],
        }
        ok, res = self._request("PUT", endpoint, payload)
        if ok:
            return True, {
                "message": f"Nạp thành công {len(shapes_payload)} shapes vào CVAT Job #{job_id}!",
                "count": len(shapes_payload),
            }
        return False, res

    def push_issues_to_cvat(
        self,
        job_id: int,
        report: QCReport,
        max_issues: int = 15,
    ) -> Tuple[bool, Any]:
        """Tạo các Issue cắm cờ đỏ chỉ điểm lỗi trên từng frame của CVAT Job."""
        if not report or not report.errors:
            return False, "Không có lỗi nào để tạo Issue."

        created = 0
        errors_to_push = report.errors[:max_issues]
        for err in errors_to_push:
            # Ước lượng frame index từ tên frame
            frame_idx = 0
            try:
                digits = "".join([c for c in err.frame_name if c.isdigit()])
                if digits:
                    frame_idx = int(digits[-4:])
            except Exception:
                frame_idx = 0

            issue_payload = {
                "job_id": job_id,
                "frame": frame_idx,
                "position": [100.0, 100.0, 300.0, 300.0],
                "comments": [
                    {"message": f"[{err.rule_id}] {err.severity}: {err.message} (Obj: {err.object_id})"}
                ],
            }
            ok, _ = self._request("POST", "/api/issues", issue_payload)
            if ok:
                created += 1

        return True, f"Đã gắn thành công {created} Issue cắm cờ đỏ lên CVAT Job #{job_id}!"


def create_cvat_mock_session() -> Tuple[List[FrameData], Dict[str, Any]]:
    """Tạo dữ liệu mô phỏng CVAT đầy đủ (BBoxes, Polygons, lỗi vi phạm và vật thể bỏ sót) để người dùng test local ngay lập tức."""
    f1_objs = [
        LabeledObject(
            id="cvat_101",
            category="car",
            box2d=BBox2D(x1=320.0, y1=450.0, x2=580.0, y2=690.0),
            attributes={"occluded": False, "truncated": False},
        ),
        LabeledObject(
            id="cvat_102",
            category="bus",
            box2d=BBox2D(x1=780.0, y1=320.0, x2=1180.0, y2=750.0),
            attributes={"occluded": True, "truncated": False},
        ),
        LabeledObject(
            id="cvat_103",
            category="traffic sign",
            box2d=BBox2D(x1=1420.0, y1=150.0, x2=1490.0, y2=230.0),
            poly2d=Polygon2D(vertices=[
                (1420.0, 190.0),
                (1455.0, 150.0),
                (1490.0, 190.0),
                (1455.0, 230.0),
            ]),
            attributes={"occluded": False, "truncated": False},
        ),
        # Đối tượng cố tình có lỗi tự cắt polygon để kiểm tra Rule P02
        LabeledObject(
            id="cvat_104",
            category="pedestrian",
            box2d=BBox2D(x1=210.0, y1=500.0, x2=280.0, y2=670.0),
            poly2d=Polygon2D(vertices=[
                (210.0, 500.0),
                (280.0, 670.0),
                (280.0, 500.0),
                (210.0, 670.0),
            ]),
            attributes={"occluded": False, "truncated": True},
        ),
    ]

    f2_objs = [
        LabeledObject(
            id="cvat_201",
            category="truck",
            box2d=BBox2D(x1=500.0, y1=380.0, x2=920.0, y2=780.0),
            attributes={"occluded": False, "truncated": False},
        ),
        LabeledObject(
            id="cvat_202",
            category="car",
            box2d=BBox2D(x1=980.0, y1=460.0, x2=1220.0, y2=640.0),
            attributes={"occluded": False, "truncated": False},
        ),
    ]

    frames = [
        FrameData(name="cvat_job88_frame_0001.jpg", objects=f1_objs, width=1920, height=1080),
        FrameData(name="cvat_job88_frame_0002.jpg", objects=f2_objs, width=1920, height=1080),
    ]

    # Tạo ảnh mô phỏng có nền đường thực tế để hiển thị Canvas & Trợ lý AI
    image_map: Dict[str, Image.Image] = {}
    for fr in frames:
        sim_img = Image.new("RGB", (1920, 1080), color=(15, 23, 42))
        draw = ImageDraw.Draw(sim_img)
        # Vẽ mặt đường phối cảnh và vạch tim đường vàng
        draw.polygon([(100, 1080), (750, 380), (1170, 380), (1820, 1080)], fill=(30, 41, 59))
        draw.line([(960, 420), (960, 1050)], fill=(245, 158, 11), width=6)
        image_map[fr.name] = sim_img
        image_map[Path(fr.name).stem] = sim_img

    meta = {
        "job_id": 88,
        "task_id": 12,
        "mode": "offline_mock",
        "total_shapes": len(f1_objs) + len(f2_objs),
        "total_frames": 2,
        "label_map": {"car": 1, "bus": 2, "truck": 3, "pedestrian": 4, "traffic sign": 5},
        "image_map": image_map,
    }
    return frames, meta
