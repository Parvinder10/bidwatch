@echo off
echo Running BIDWATCH Pytest Suite...
if exist D:\bidwatch_env\venv\Scripts\pytest.exe (
    D:\bidwatch_env\venv\Scripts\pytest.exe -v tests/
) else (
    pytest -v tests/
)
pause
