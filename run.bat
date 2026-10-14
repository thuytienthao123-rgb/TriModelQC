@echo off
set PYTHONIOENCODING=utf-8
cd /d "%~dp0source-tool\QC_tool"
python -m streamlit run app.py
