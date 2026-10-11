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
    print("[..] Dang chay kiem tra...")
    report = run_qc(frames)

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
