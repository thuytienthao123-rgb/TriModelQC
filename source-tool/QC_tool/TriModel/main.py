"""
main.py — Điểm khởi chạy CLI cho BDD-QC Tool.
Phụ trách chính: Đào Ngọc Hiếu (2A202602081)

Cách dùng:
  python main.py --input data_sample/sample_with_errors.json
  python main.py --input data_sample/sample_with_errors.json --output report.html
  python main.py --input data_sample/sample_with_errors.json --output report.csv
  python main.py --input data_sample/sample_with_errors.json --only-errors
"""

from __future__ import annotations
import argparse
import logging
import sys
from pathlib import Path

from qc.parser import load_bdd100k
from qc.engine import run_qc
from qc.reporter import print_report_console, export_csv, export_html


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bdd-qc",
        description=(
            "BDD-QC Tool — Kiểm tra chất lượng nhãn BDD100K tự động.\n"
            "Phát hiện lỗi hình học, polygon tự cắt, vẽ trùng và thiếu thuộc tính."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ví dụ:\n"
            "  python main.py --input annotations.json\n"
            "  python main.py --input annotations.json --output report.html\n"
            "  python main.py --input annotations.json --output report.csv --only-errors\n"
        ),
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        metavar="FILE",
        help="Đường dẫn file JSON nhãn BDD100K cần kiểm tra.",
    )
    parser.add_argument(
        "--output", "-o",
        metavar="FILE",
        default=None,
        help=(
            "Đường dẫn file đầu ra. Định dạng tự động theo đuôi mở rộng:\n"
            "  .html  → báo cáo HTML (dark mode, có tìm kiếm)\n"
            "  .csv   → bảng CSV cho annotator tự tra cứu\n"
            "Không chỉ định → chỉ in lên terminal."
        ),
    )
    parser.add_argument(
        "--only-errors",
        action="store_true",
        default=False,
        help="Chỉ hiển thị ERROR, bỏ qua WARNING.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="In thêm log chi tiết (parse, số frame, số object...).",
    )
    parser.add_argument(
        "--ai-check",
        action="store_true",
        default=False,
        help="Bật kiểm tra tự động bằng Tri-Model AI Ensemble (soi vật thể bỏ sót & sai nhãn).",
    )
    parser.add_argument(
        "--images-dir",
        default=None,
        metavar="DIR",
        help="Thư mục chứa ảnh tương ứng với các frame (dùng khi bật --ai-check).",
    )
    parser.add_argument(
        "--ensemble-mode",
        choices=["strict", "majority"],
        default="strict",
        help="Cơ chế đồng thuận Tri-Model: strict (cả 3 model) hoặc majority (2/3 model).",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.35,
        help="Ngưỡng độ tin cậy AI (Confidence threshold, mặc định 0.35).",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    # 1. Parse file nhãn
    print(f"\n[>] Dang doc file nhan: {args.input}")
    try:
        frames = load_bdd100k(args.input)
    except (FileNotFoundError, ValueError) as exc:
        print(f"❌  Lỗi đọc file: {exc}", file=sys.stderr)
        return 1

    print(f"[OK] Da load {len(frames)} frame(s).")

    # 2. Chạy QC engine
    print("[..] Dang chay kiem tra rules co ban...")
    report = run_qc(frames)

    # 2b. Chạy Tri-Model AI Ensemble nếu được bật
    if args.ai_check:
        print("[..] Dang kich hoat Tri-Model AI QC Assistant...")
        try:
            from PIL import Image
            from qc.ai_detector import TriModelQCAssistant
            from qc.models import QCError

            assistant = TriModelQCAssistant()
            if not assistant.is_ready():
                print("[!] Khong the khoi tao mo hinh AI (thieu weights).")
            else:
                img_dir = Path(args.images_dir) if args.images_dir else Path(args.input).parent
                print(f"[..] Quet anh tu: {img_dir} (che do: {args.ensemble_mode})")
                for frame in frames:
                    cand_img = img_dir / frame.name
                    if not cand_img.is_file():
                        cand_img = img_dir / f"{Path(frame.name).stem}.jpg"
                    if cand_img.is_file():
                        img_pil = Image.open(cand_img).convert("RGB")
                        ai_res = assistant.check_missed_and_mismatched(
                            img_pil,
                            frame.objects,
                            conf_thresh=args.conf,
                            ensemble_mode=args.ensemble_mode,
                        )
                        # Báo lỗi bỏ sót (RULE_AI01)
                        for m_idx, m_obj in enumerate(ai_res.get("missed", []), 1):
                            mbx = m_obj["box2d"]
                            m_cat = m_obj["category"]
                            m_conf = m_obj["confidence"]
                            agreed_cnt = m_obj.get("agreement_count", 3)
                            report.add(QCError(
                                rule_id="RULE_AI01",
                                severity="ERROR" if agreed_cnt >= 3 or m_conf >= 0.60 else "WARNING",
                                frame_name=frame.name,
                                object_id=f"missed_{m_idx:02d}",
                                category=m_cat,
                                message=(
                                    f"MISSED: Bo sot [{m_cat}] tai "
                                    f"[{int(mbx.x1)}, {int(mbx.y1)}, {int(mbx.x2)}, {int(mbx.y2)}] "
                                    f"([AI {agreed_cnt}/3 Dong thuan], WBF conf: {m_conf:.0%})"
                                ),
                            ))
                        # Báo lỗi sai class (RULE_AI02)
                        for mm_idx, mm_obj in enumerate(ai_res.get("mismatched", []), 1):
                            report.add(QCError(
                                rule_id="RULE_AI02",
                                severity="WARNING",
                                frame_name=frame.name,
                                object_id=mm_obj["user_obj_id"],
                                category=mm_obj["user_category"],
                                message=(
                                    f"Nghi van sai nhan: Nguoi gan la [{mm_obj['user_category']}] "
                                    f"nhung AI dong thuan xac dinh la [{mm_obj['ai_category']}] "
                                    f"(IoU {mm_obj['iou']:.0%}, conf: {mm_obj['confidence']:.0%})"
                                ),
                            ))
                print(f"[OK] Da hoan tat quet AI.")
        except Exception as ex:
            print(f"[!] Loi khi chay AI check: {ex}", file=sys.stderr)

    # 3. Xuất báo cáo
    show_warnings = not args.only_errors

    if args.output is None:
        print_report_console(report, show_warnings=show_warnings)
    else:
        out_path = Path(args.output)
        suffix = out_path.suffix.lower()
        if suffix == ".html":
            print_report_console(report, show_warnings=show_warnings)
            export_html(report, out_path)
        elif suffix == ".csv":
            print_report_console(report, show_warnings=show_warnings)
            export_csv(report, out_path)
        else:
            print(f"[!] Dinh dang '{suffix}' khong duoc ho tro. Dung .html hoac .csv.")
            print_report_console(report, show_warnings=show_warnings)

    # 4. Exit code: 1 nếu có ERROR (để dùng trong CI/CD pipeline)
    return 1 if report.error_count() > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
