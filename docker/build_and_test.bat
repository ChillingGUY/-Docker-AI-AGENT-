@echo off
REM Windows批處理腳本 - 構建和測試

echo ==========================================
echo AI Training Agent 構建和測試
echo ==========================================

REM 1. 構建Docker鏡像
echo.
echo 步驟 1: 構建Docker鏡像
echo ----------------------------------------
docker build -f Dockerfile -t ai-training:latest .

if %ERRORLEVEL% NEQ 0 (
    echo ✗ 鏡像構建失敗
    exit /b 1
)
echo ✓ 鏡像構建成功

REM 2. 運行Docker測試
echo.
echo 步驟 2: 運行Docker容器測試
echo ----------------------------------------
python test_docker.py

if %ERRORLEVEL% NEQ 0 (
    echo ✗ Docker測試失敗
    exit /b 1
)

REM 3. 啟動API服務（後台）
echo.
echo 步驟 3: 啟動API服務
echo ----------------------------------------
start /B python -m uvicorn app:app --host 0.0.0.0 --port 8000
timeout /t 5 /nobreak >nul

REM 4. 運行API測試
echo.
echo 步驟 4: 運行API測試
echo ----------------------------------------
python test_api.py
set API_TEST_RESULT=%ERRORLEVEL%

REM 5. 停止API服務
echo.
echo 步驟 5: 停止API服務
echo ----------------------------------------
taskkill /F /IM python.exe /FI "WINDOWTITLE eq uvicorn*" >nul 2>&1

REM 總結
echo.
echo ==========================================
echo 測試完成
echo ==========================================

if %API_TEST_RESULT% EQU 0 (
    echo ✓ 所有測試通過
    exit /b 0
) else (
    echo ✗ 部分測試失敗
    exit /b 1
)
