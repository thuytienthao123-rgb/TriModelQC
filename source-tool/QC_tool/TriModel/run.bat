@echo off
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
python -m streamlit run app.py
