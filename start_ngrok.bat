@echo off
REM Simple launcher: Streamlit (port 8501) + ngrok http 8501 （后台运行版）

setlocal

REM 获取脚本所在目录（例如 E:\chowey\）
set "SCRIPT_DIR=%~dp0"
set "NGROK_EXE=%SCRIPT_DIR%ngrok.exe"

REM 检查 ngrok.exe 是否存在
if not exist "%NGROK_EXE%" (
    echo NGROK EXE NOT FOUND: %NGROK_EXE%
    echo Please make sure ngrok.exe is in the same directory as this script.
    pause
    goto :eof
)

REM -----------------------------
REM 启动 Streamlit （最小化的 cmd 窗口，方便看到报错）
REM 行为等同于：E: / cd \chowey / streamlit run app.py ...
REM 使用你之前手动可用的 streamlit 命令
REM -----------------------------
start "Streamlit" /min cmd /k "cd /d %SCRIPT_DIR% && streamlit run app.py --server.address 0.0.0.0 --server.port 8501"

REM 稍等 2 秒，确保 Streamlit 先起来
timeout /t 2 /nobreak >nul

REM -----------------------------
REM 启动 ngrok （最小化的 cmd 窗口）
REM 行为等同于：E: / cd \chowey / .\ngrok.exe http 8501
REM -----------------------------
start "ngrok" /min cmd /k "cd /d %SCRIPT_DIR% && ngrok.exe http 8501"

endlocal
exit /b 0


