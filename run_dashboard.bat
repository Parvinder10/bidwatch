@echo off
echo Starting BIDWATCH Dashboard...
if exist D:\bidwatch_env\venv\Scripts\streamlit.exe (
    D:\bidwatch_env\venv\Scripts\streamlit.exe run app/main.py
) else (
    streamlit run app/main.py
)
pause
