"""
Wrapper entrypoint for QC_tool redirecting to TriModel/app.py.
"""
import os
import sys
from pathlib import Path

trimodel_dir = Path(__file__).resolve().parent / "TriModel"
if str(trimodel_dir) not in sys.path:
    sys.path.insert(0, str(trimodel_dir))

os.chdir(str(trimodel_dir))

import runpy
runpy.run_path(str(trimodel_dir / "app.py"), run_name="__main__")
