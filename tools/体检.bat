@echo off
chcp 65001 >nul
cd /d "%~dp0.."
python tools\素材体检.py %*
echo.
echo 报告：素材交付\体检报告.md
pause
