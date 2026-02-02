#!/bin/bash
# 完整測試腳本

echo "=========================================="
echo "AI Training Agent 完整測試"
echo "=========================================="

# 1. 構建Docker鏡像
echo ""
echo "步驟 1: 構建Docker鏡像"
echo "----------------------------------------"
docker build -f Dockerfile -t ai-training:latest .

if [ $? -ne 0 ]; then
    echo "✗ 鏡像構建失敗"
    exit 1
fi
echo "✓ 鏡像構建成功"

# 2. 運行Docker測試
echo ""
echo "步驟 2: 運行Docker容器測試"
echo "----------------------------------------"
python test_docker.py

if [ $? -ne 0 ]; then
    echo "✗ Docker測試失敗"
    exit 1
fi

# 3. 啟動API服務
echo ""
echo "步驟 3: 啟動API服務"
echo "----------------------------------------"
python -m uvicorn app:app --host 0.0.0.0 --port 8000 &
API_PID=$!
sleep 5

# 4. 運行API測試
echo ""
echo "步驟 4: 運行API測試"
echo "----------------------------------------"
python test_api.py
API_TEST_RESULT=$?

# 5. 停止API服務
echo ""
echo "步驟 5: 停止API服務"
echo "----------------------------------------"
kill $API_PID 2>/dev/null

# 總結
echo ""
echo "=========================================="
echo "測試完成"
echo "=========================================="

if [ $API_TEST_RESULT -eq 0 ]; then
    echo "✓ 所有測試通過"
    exit 0
else
    echo "✗ 部分測試失敗"
    exit 1
fi
