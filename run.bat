@echo off
cd /d "%~dp0"
py -3 -m src.main %*
if errorlevel 9009 python -m src.main %*
