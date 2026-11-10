@echo off
title AsTech
rem Se ubica sola en la carpeta donde esta este archivo (no depende de la ruta).
cd /d "%~dp0"
start "AsTech servidor" /min cmd /c "python -m streamlit run app.py --server.headless true --server.port 8501"
timeout /t 4 /nobreak >nul
start "" "http://localhost:8501"
