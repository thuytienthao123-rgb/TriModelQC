@echo off
set PYTHONIOENCODING=utf-8
title BDD100K QC Tool (Tri-Model AI)
echo ========================================================
echo   Dang khoi dong BDD100K QC Tool (Tri-Model AI Assistant)
echo ========================================================
cd /d "%~dp0source-tool\QC_tool"
python -m streamlit run app.py
if %ERRORLEVEL% NEQ 0 (
    echo [!] Gap loi khi khoi chay Streamlit.
    pause
)
