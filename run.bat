@echo off
cd /d %~dp0
if exist .venv\Scripts\python.exe (
  .venv\Scripts\python.exe -m livetranslate.main
) else (
  C:\Users\Admin\LiveTranslate-venv\Scripts\python.exe -m livetranslate.main
)
pause
