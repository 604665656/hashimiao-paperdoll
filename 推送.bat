@echo off
chcp 65001 >nul
cd /d "%~dp0"
set msg=%~1
if "%msg%"=="" set msg=例行同步 %date% %time%

echo [1/3] 暂存改动...
git add -A
echo [2/3] 提交：%msg%
git commit -m "%msg%"
echo [3/3] 推送...
git push
echo.
echo 完成。改动已同步到 GitHub。
pause
