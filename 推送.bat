@echo off
chcp 65001 >nul
cd /d "%~dp0"
set msg=%~1
if "%msg%"=="" set msg=例行同步 %date% %time%

echo [1/3] 暂存改动...
git add -A

echo [2/3] 提交：%msg%
git commit -m "%msg%"

echo [3/3] 推送（代理不稳，最多重试 5 次）...
setlocal enabledelayedexpansion
for /l %%i in (1,1,5) do (
  git -c http.version=HTTP/1.1 -c pack.threads=1 push origin main
  for /f %%h in ('git rev-parse HEAD') do set LOCAL=%%h
  for /f %%h in ('git ls-remote origin main') do set REMOTE=%%h
  if "!LOCAL!"=="!REMOTE!" (
    echo.
    echo 已同步：!LOCAL!
    goto done
  )
  echo   第 %%i 次没成功，重试...
  timeout /t 3 /nobreak >nul
)
echo 推送仍然失败：检查代理或网络后重跑本文件。

:done
pause
