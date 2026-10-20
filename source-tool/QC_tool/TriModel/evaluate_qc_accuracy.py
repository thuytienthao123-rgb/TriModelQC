"""
evaluate_qc_accuracy.py — Bộ công cụ chấm điểm định lượng độ chính xác cho TriModel QC Studio.
Dùng để chạy độc lập trên Terminal, trên CI/CD, hoặc trong Google Colab / Jupyter Notebook.

Cách sử dụng:
1. Tự động kiểm tra nhanh (Zero-Setup Benchmark):
   python evaluate_qc_accuracy.py --self-test

2. Chấm điểm tập Ground Truth do người dùng cung cấp:
   python evaluate_qc_accuracy.py --gt data_sample/sample_valid.json --raw data_sample/sample_with_errors.json

3. Chấm điểm tiêm lỗi (Honeypot Mode) trên tập Ground Truth:
   python evaluate_qc_accuracy.py --gt path/to/ground_truth.json --honeypot --defect-rate 0.35
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Đảm bảo in UTF-8 an toàn trên mọi hệ điều hành (Windows cp1252, Linux, Colab)
if sys.platform == "win32":
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

# Thêm thư mục hiện tại vào sys.path để import qc, ui
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from qc.parser import load_bdd100k, parse_bdd100k_text
from qc.engine import run_qc
from qc.benchmark import (
    inject_honeypot_defects,
    evaluate_qc_detection_accuracy,
    evaluate_quality_improvement,
    generate_benchmark_html_report,
)
from ui.auto_fix import auto_correct_frames


# Màu ANSI in terminal
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner():
    print(f"\n{BOLD}{BLUE}" + "="*75 + f"{RESET}")
    print(f"{BOLD}{GREEN}   TRIMODEL QC STUDIO — QUANTITATIVE ACCURACY & BENCHMARK SUITE{RESET}")
    print(f"{BOLD}{BLUE}   Chứng nhận định lượng khoa học: Precision, Recall, F1 & mIoU Gain{RESET}")
    print(f"{BOLD}{BLUE}" + "="*75 + f"{RESET}\n")


def run_benchmark(
    gt_path: str,
    raw_path: str = None,
    honeypot: bool = False,
    defect_rate: float = 0.35,
    export_html: str = "qc_benchmark_report.html",
    export_json: str = "qc_benchmark_report.json",
):
    print_banner()
    
    # 1. Nạp tập Ground Truth
    gt_file = Path(gt_path)
    if not gt_file.exists():
        print(f"{RED}[LỖI] Không tìm thấy file Ground Truth tại: {gt_path}{RESET}")
        sys.exit(1)

    print(f"{BOLD}📂 [1/4] Đang nạp tập Ground Truth (GT):{RESET} {gt_file.name}")
    gt_frames = load_bdd100k(gt_file)
    total_gt_objs = sum(len(f.objects) for f in gt_frames)
    print(f"   -> Nạp thành công {len(gt_frames)} frames với {total_gt_objs} đối tượng chuẩn 100%.\n")

    # 2. Chuẩn bị tập dữ liệu kiểm thử
    injected_defect_map = {}
    if honeypot or not raw_path:
        print(f"{BOLD}🧪 [2/4] Chế độ Honeypot:{RESET} Đang tiêm {defect_rate:.0%} lỗi nhân tạo mô phỏng thực tế...")
        test_frames, injected_defect_map, manifest = inject_honeypot_defects(
            gt_frames, defect_rate=defect_rate, seed=42
        )
        total_injected = len(manifest)
        print(f"   -> Đã tiêm chính xác {total_injected} lỗi thuộc 12 dạng vi phạm vào {len(test_frames)} frames.\n")
    else:
        raw_file = Path(raw_path)
        print(f"{BOLD}📂 [2/4] Đang nạp tập nhãn Annotator (Raw):{RESET} {raw_file.name}")
        test_frames = load_bdd100k(raw_file)
        print(f"   -> Nạp thành công {len(test_frames)} frames nhãn thô.\n")

    # 3. Chạy QC Engine phát hiện lỗi
    print(f"{BOLD}⚙️  [3/4] Đang thực thi QC Engine & 15 Bộ Luật Kiểm Định...{RESET}")
    report = run_qc(test_frames)
    print(f"   -> Hoàn thành kiểm định! Phát hiện tổng cộng: {len(report.errors)} lỗi vi phạm ({report.error_count()} Errors, {report.warning_count()} Warnings).\n")

    # 4. Đánh giá Định Lượng
    print(f"{BOLD}📊 [4/4] Đang tính toán Ma Trận Nhầm Lẫn & Các Chỉ Số Độ Chính Xác...{RESET}\n")
    
    # Khảo sát phát hiện lỗi
    detection_metrics = evaluate_qc_detection_accuracy(test_frames, report, injected_defect_map)
    
    # Khảo sát cải thiện chất lượng dữ liệu sau sửa lỗi
    improvement_metrics = evaluate_quality_improvement(gt_frames, test_frames)

    # In kết quả dạng bảng đẹp mắt
    print(f"{BOLD}{GREEN}==================== KẾT QUẢ ĐÁNH GIÁ ĐỘ CHÍNH XÁC ===================={RESET}")
    print(f"{BOLD}1. NĂNG LỰC PHÁT HIỆN LỖI (DETECTION POWER):{RESET}")
    print(f"   * True Positives  (Bắt đúng lỗi)   : {GREEN}{detection_metrics.tp}{RESET}")
    print(f"   * False Positives (Báo khống / ảo)  : {YELLOW}{detection_metrics.fp}{RESET}")
    print(f"   * False Negatives (Bỏ sót lỗi)      : {RED}{detection_metrics.fn}{RESET}")
    print(f"   * True Negatives  (Nhãn chuẩn đúng) : {GREEN}{detection_metrics.tn}{RESET}")
    print(f"   ------------------------------------------------------------------")
    print(f"   👉 {BOLD}PRECISION (Độ chuẩn xác)       : {GREEN}{detection_metrics.precision:.2%}{RESET} (Tránh báo sai)")
    print(f"   👉 {BOLD}RECALL    (Độ nhạy bắt lỗi)    : {BLUE}{detection_metrics.recall:.2%}{RESET} (Bắt trúng {detection_metrics.tp}/{detection_metrics.total_ground_truth_errors} lỗi)")
    print(f"   👉 {BOLD}F1-SCORE  (Điểm cân bằng F1)   : {BOLD}{GREEN}{detection_metrics.f1_score:.4f}{RESET}")
    print(f"   👉 {BOLD}ACCURACY  (Độ chính xác chung) : {BOLD}{detection_metrics.accuracy:.2%}{RESET}")
    print(f"   👉 {BOLD}SPECIFICITY (Độ đặc hiệu)      : {detection_metrics.specificity:.2%}{RESET}\n")

    print(f"{BOLD}2. MỨC ĐỘ NÂNG CAO CHẤT LƯỢNG DỮ LIỆU (TRƯỚC VS SAU QC & AUTO-FIX):{RESET}")
    gain_sign = "+" if improvement_metrics.miou_gain >= 0 else ""
    print(f"   * Mean IoU (Độ khớp hộp bao & mask):")
    print(f"     - Trước QC (Raw)   : {improvement_metrics.raw_miou:.4f}")
    print(f"     - Sau QC (Healed)  : {GREEN}{improvement_metrics.post_qc_miou:.4f}{RESET} ({gain_sign}{improvement_metrics.miou_gain:.2%})")
    
    acc_sign = "+" if improvement_metrics.class_acc_gain >= 0 else ""
    print(f"   * Độ chính xác phân loại nhãn (Class Accuracy):")
    print(f"     - Trước QC (Raw)   : {improvement_metrics.raw_class_acc:.2%}")
    print(f"     - Sau QC (Healed)  : {GREEN}{improvement_metrics.post_qc_class_acc:.2%}{RESET} ({acc_sign}{improvement_metrics.class_acc_gain:.2%})")

    print(f"   * Điểm Chất Lượng Nhãn Tổng Hợp (AQI / 100 điểm):")
    print(f"     - Trước QC : {YELLOW}{improvement_metrics.raw_aqi:.1f} / 100{RESET}")
    print(f"     - Sau QC   : {BOLD}{GREEN}{improvement_metrics.post_qc_aqi:.1f} / 100{RESET} (+{improvement_metrics.aqi_gain:.1f} điểm)")
    print(f"{BOLD}{GREEN}======================================================================={RESET}\n")

    # In chi tiết từng rule nếu có
    if detection_metrics.per_rule_stats:
        print(f"{BOLD}3. CHI TIẾT ĐỘ CHÍNH XÁC THEO TỪNG QUY TẮC (RULE BREAKDOWN):{RESET}")
        print(f"{'-'*75}")
        print(f"{'Mã Quy Tắc (Rule)':<25} | {'TP':<4} | {'FN':<4} | {'FP':<4} | {'Precision':<10} | {'Recall':<10}")
        print(f"{'-'*75}")
        for r_name, r_vals in detection_metrics.per_rule_stats.items():
            print(f"{r_name:<25} | {r_vals['TP']:<4} | {r_vals['FN']:<4} | {r_vals['FP']:<4} | {r_vals['Precision']:<10} | {r_vals['Recall (Detection Rate)']:<10}")
        print(f"{'-'*75}\n")

    # Xuất báo cáo HTML
    if export_html:
        html_content = generate_benchmark_html_report(detection_metrics, improvement_metrics)
        with open(export_html, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"📄 {BOLD}Đã xuất Dashboard HTML trực quan tại:{RESET} {export_html}")

    # Xuất báo cáo JSON
    if export_json:
        full_json = {
            "detection_metrics": detection_metrics.to_dict(),
            "quality_improvement": improvement_metrics.to_dict(),
        }
        with open(export_json, "w", encoding="utf-8") as f:
            json.dump(full_json, f, ensure_ascii=False, indent=2)
        print(f"💾 {BOLD}Đã xuất dữ liệu máy đọc JSON tại:{RESET} {export_json}\n")


def main():
    parser = argparse.ArgumentParser(description="TriModel QC Quantitative Accuracy & Benchmark Evaluation")
    parser.add_argument("--gt", type=str, default=None, help="Đường dẫn đến file nhãn chuẩn đối chứng (Ground Truth)")
    parser.add_argument("--raw", type=str, default=None, help="Đường dẫn đến file nhãn thô cần đánh giá (Raw/Annotator)")
    parser.add_argument("--honeypot", action="store_true", help="Bật chế độ tự động tiêm lỗi nhân tạo (Honeypot Mode)")
    parser.add_argument("--defect-rate", type=float, default=0.35, help="Tỷ lệ đối tượng bị tiêm lỗi (mặc định 0.35)")
    parser.add_argument("--self-test", action="store_true", help="Chạy tự động kiểm thử nhanh zero-setup với dữ liệu mẫu")
    parser.add_argument("--export-html", type=str, default="qc_benchmark_report.html", help="Tên file HTML xuất ra")
    parser.add_argument("--export-json", type=str, default="qc_benchmark_report.json", help="Tên file JSON xuất ra")

    args = parser.parse_args()

    if args.self_test or not args.gt:
        sample_gt = str(CURRENT_DIR / "data_sample" / "sample_valid.json")
        sample_raw = str(CURRENT_DIR / "data_sample" / "sample_with_errors.json")
        print(f"{YELLOW}ℹ️  Chạy bài kiểm thử tự động với dữ liệu mẫu BDD100K tích hợp sẵn...{RESET}")
        run_benchmark(
            gt_path=sample_gt,
            raw_path=sample_raw,
            honeypot=args.honeypot,
            defect_rate=args.defect_rate,
            export_html=args.export_html,
            export_json=args.export_json,
        )
    else:
        run_benchmark(
            gt_path=args.gt,
            raw_path=args.raw,
            honeypot=args.honeypot,
            defect_rate=args.defect_rate,
            export_html=args.export_html,
            export_json=args.export_json,
        )


if __name__ == "__main__":
    main()
