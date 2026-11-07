@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo 重新生成结构参考卡...
python tools\参考卡生成.py
echo.
echo 产物在 参考卡\
pause
