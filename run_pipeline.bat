@echo off
echo Running BIDWATCH Data Pipeline and Investigative Engine...
if exist D:\bidwatch_env\venv\Scripts\python.exe (
    D:\bidwatch_env\venv\Scripts\python.exe src/ingestion/pipeline.py
    D:\bidwatch_env\venv\Scripts\python.exe src/indicators/investigative_engine.py
) else (
    python src/ingestion/pipeline.py
    python src/indicators/investigative_engine.py
)
echo Done!
pause
