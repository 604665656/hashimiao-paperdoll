@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo ============================================
echo  截图批量入库
echo  把截图放进 素材入库\_inbox 后运行本文件
echo ============================================
echo.
python tools\截图入库.py %*
echo.
echo 产物在 素材入库\out  （index.json / _总览.png / 单只素材 png）
pause
