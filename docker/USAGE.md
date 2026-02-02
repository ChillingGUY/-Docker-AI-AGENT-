# 使用說明

## 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 構建Docker訓練鏡像

```bash
docker build -f Dockerfile -t ai-training:latest .
```

### 3. 驗證安裝

```bash
python quick_test.py
```

### 4. 啟動服務

```bash
# 方式1: 直接運行
python run.py

# 方式2: 使用uvicorn
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

### 5. 測試Docker功能

```bash
python test_docker.py
```

### 6. 測試API功能

在另一個終端運行：
```bash
python test_api.py
```

## 完整測試流程

### Windows
```bash
build_and_test.bat
```

### Linux/Mac
```bash
bash run_tests.sh
```

## API使用示例

### 提交訓練任務

```bash
curl -X POST "http://localhost:8000/train" \
  -H "Content-Type: application/json" \
  -d '{
    "epochs": 5,
    "batch_size": 32,
    "learning_rate": 0.001,
    "gpu": false
  }'
```

### 查詢任務狀態

```bash
curl "http://localhost:8000/train/{task_id}"
```

### 查看所有任務

```bash
curl "http://localhost:8000/train"
```

### 查看統計信息

```bash
curl "http://localhost:8000/stats"
```

## 查看日志

所有日志文件保存在 `./logs/` 目錄：

- `TrainingAgent_YYYYMMDD.log` - Agent運行日志
- `TrainingWorker_YYYYMMDD.log` - Worker進程日志
- `training_YYYYMMDD_HHMMSS.log` - 訓練任務日志

## 常見問題

### 1. Docker連接失敗

確保Docker服務正在運行：
```bash
docker ps
```

### 2. 模組導入錯誤

確保已安裝所有依賴：
```bash
pip install -r requirements.txt
```

### 3. 端口被占用

修改 `run.py` 或使用不同端口：
```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8001
```

### 4. 鏡像構建失敗

清理舊鏡像並重新構建：
```bash
docker system prune -a
docker build --no-cache -f Dockerfile -t ai-training:latest .
```

## 性能優化建議

1. **配置時間優化**：
   - 使用預構建的Docker鏡像
   - 緩存依賴包
   - 並行構建多個鏡像

2. **失敗率降低**：
   - 啟用自動重試機制
   - 設置合理的超時時間
   - 監控資源使用情況

3. **日志管理**：
   - 定期清理舊日志
   - 使用日志輪轉
   - 集中存儲日志
