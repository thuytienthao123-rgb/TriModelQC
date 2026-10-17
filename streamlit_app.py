"""
streamlit_app.py — Root deployment entrypoint for Streamlit Community Cloud & Cloud Platforms.
Directs execution to source-tool/QC_tool/TriModel/app.py while preserving paths.
"""
import sys
import os
from pathlib import Path

# Thêm thư mục TriModel vào sys.path để các module nội bộ (qc, ui) import tự nhiên
REPO_ROOT = Path(__file__).resolve().parent
TRIMODEL_DIR = REPO_ROOT / "source-tool" / "QC_tool" / "TriModel"

if str(TRIMODEL_DIR) not in sys.path:
    sys.path.insert(0, str(TRIMODEL_DIR))

# Đặt thư mục làm việc về TriModel để các file tĩnh, font, mô hình hoạt động nhất quán
os.chdir(TRIMODEL_DIR)

from app import main

if __name__ == "__main__":
    main()
