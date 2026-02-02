# 完整使用指南

## 一、系統概述

本系統是一個基於Docker的AI訓練Agent中間件，主要解決以下問題：
- **環境配置不統一**：通過標準化Docker鏡像解決
- **日志分散**：通過統一日志歸集解決
- **配置耗時長**：從30分鐘縮減到5分鐘
- **失敗率高**：通過自動重試機制降低40%

## 二、快速開始

### 2.1 環境準備

**系統要求**：
- Python 3.10+
- Docker Desktop（Windows/Mac）或 Docker Engine（Linux）
- 至少4GB可用內存

**安裝依賴**：
```bash
# 安裝Python依賴
pip install -r requirements.txt

# 驗證Docker是否運行
docker ps
```

### 2.2 構建Docker鏡像

```bash
# 構建訓練鏡像（標準化環境）
docker build -f Dockerfile -t ai-training:latest .

# 驗證鏡像構建成功
docker images | grep ai-training
```

**構建時間**：首次構建約5-10分鐘（下載基礎鏡像和依賴），後續構建約1-2分鐘（使用緩存）

### 2.3 啟動服務

**方式1：直接運行**
```bash
python run.py
```

**方式2：使用uvicorn**
```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

**方式3：使用Docker Compose**
```bash
docker-compose up -d
```

服務啟動後，訪問：
- API文檔：http://localhost:8000/docs
- 健康檢查：http://localhost:8000/health

## 三、API使用詳解

### 3.1 提交訓練任務

**端點**：`POST /train`

**請求體**：
```json
{
  "epochs": 5,              // 訓練輪數（必填）
  "batch_size": 32,         // 批次大小（可選，默認32）
  "learning_rate": 0.001,   // 學習率（可選，默認0.001）
  "gpu": false,             // 是否使用GPU（可選，默認false）
  "gpu_ids": "0,1",         // GPU設備ID（可選，僅gpu=true時有效）
  "max_retries": 3          // 最大重試次數（可選，默認3）
}
```

**響應**：
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Training task submitted successfully"
}
```

**使用curl**：
```bash
curl -X POST "http://localhost:8000/train" \
  -H "Content-Type: application/json" \
  -d '{
    "epochs": 5,
    "batch_size": 32,
    "learning_rate": 0.001
  }'
```

**使用Python**：
```python
import requests

response = requests.post(
    "http://localhost:8000/train",
    json={
        "epochs": 5,
        "batch_size": 32,
        "learning_rate": 0.001
    }
)
task_id = response.json()["task_id"]
print(f"Task ID: {task_id}")
```

### 3.2 查詢任務狀態

**端點**：`GET /train/{task_id}`

**響應**：
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",           // pending/running/success/failed/cancelled
  "epochs": 5,
  "batch_size": 32,
  "learning_rate": 0.001,
  "gpu": false,
  "error": null,                 // 失敗時包含錯誤信息
  "container_id": "abc123...",   // Docker容器ID
  "log_file": "./logs/training_20260128_190000.log",
  "created_at": "2026-01-28T19:00:00",
  "started_at": "2026-01-28T19:00:01",
  "completed_at": null,          // 完成時才有值
  "retry_count": 0
}
```

**使用curl**：
```bash
curl "http://localhost:8000/train/550e8400-e29b-41d4-a716-446655440000"
```

### 3.3 列出所有任務

**端點**：`GET /train?status=running&limit=10`

**查詢參數**：
- `status`（可選）：過濾狀態（pending/running/success/failed/cancelled）
- `limit`（可選）：返回數量限制，默認50

**響應**：
```json
{
  "total": 10,
  "tasks": [
    {
      "task_id": "...",
      "status": "running",
      ...
    }
  ]
}
```

### 3.4 取消任務

**端點**：`DELETE /train/{task_id}`

**限制**：只能取消pending或running狀態的任務

**響應**：
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "cancelled",
  "message": "Task cancelled successfully"
}
```

### 3.5 獲取統計信息

**端點**：`GET /stats`

**響應**：
```json
{
  "total": 100,
  "pending": 5,
  "running": 2,
  "success": 80,
  "failed": 10,
  "cancelled": 3,
  "success_rate": 88.89
}
```

## 四、任務狀態說明

### 4.1 狀態轉換

```
PENDING → RUNNING → SUCCESS/FAILED
   ↓         ↓
CANCELLED  (可取消)
```

### 4.2 狀態詳解

- **PENDING**：任務已創建，等待Worker處理
- **RUNNING**：任務正在執行中
- **SUCCESS**：任務執行成功
- **FAILED**：任務執行失敗（已重試）
- **CANCELLED**：任務被取消

## 五、日志查看

### 5.1 日志文件位置

所有日志文件保存在 `./logs/` 目錄：

```
logs/
├── TrainingAgent_20260128.log      # Agent運行日志
├── TrainingWorker_20260128.log     # Worker進程日志
└── training_20260128_190000.log    # 訓練任務日志（每個任務一個）
```

### 5.2 日志格式

```
2026-01-28 19:00:00 - TrainingAgent - INFO - [agent.py:62] - Training agent started
2026-01-28 19:00:01 - TrainingAgent - INFO - [agent.py:165] - Container started: abc123def456
2026-01-28 19:00:02 - TrainingAgent - INFO - [agent.py:202] - [TRAIN] Epoch 1/5 started
```

### 5.3 查看日志

**查看Agent日志**：
```bash
tail -f logs/TrainingAgent_20260128.log
```

**查看任務日志**：
```bash
cat logs/training_20260128_190000.log
```

**搜索錯誤**：
```bash
grep -i error logs/*.log
```

## 六、測試驗證

### 6.1 快速驗證

```bash
# 基本功能測試
python quick_test.py
```

### 6.2 Docker測試

```bash
# 測試Docker功能
python test_docker.py
```

**測試內容**：
1. Docker連接測試
2. 鏡像構建測試
3. 容器運行測試
4. 日志歸集測試

### 6.3 API測試

**前提**：服務已啟動

```bash
# 測試API端點
python test_api.py
```

**測試內容**：
1. 健康檢查
2. 任務提交
3. 狀態查詢
4. 任務列表
5. 統計信息

### 6.4 完整測試

**Windows**：
```bash
build_and_test.bat
```

**Linux/Mac**：
```bash
bash run_tests.sh
```

## 七、常見問題

### 7.1 Docker連接失敗

**問題**：`docker.errors.DockerException: Error while fetching server API version`

**解決方案**：
1. 確保Docker服務正在運行
2. 檢查Docker socket權限（Linux）
3. 重啟Docker服務

```bash
# Windows/Mac: 重啟Docker Desktop
# Linux: 
sudo systemctl restart docker
```

### 7.2 鏡像構建失敗

**問題**：`docker.errors.BuildError`

**解決方案**：
1. 檢查網絡連接
2. 清理舊鏡像
3. 重新構建

```bash
# 清理舊鏡像
docker system prune -a

# 重新構建
docker build --no-cache -f Dockerfile -t ai-training:latest .
```

### 7.3 任務執行失敗

**問題**：任務狀態為FAILED

**排查步驟**：
1. 查看任務日志：`logs/training_*.log`
2. 查看Agent日志：`logs/TrainingAgent_*.log`
3. 檢查容器狀態：`docker ps -a`
4. 查看容器日志：`docker logs <container_id>`

### 7.4 端口被占用

**問題**：`Address already in use`

**解決方案**：
1. 使用不同端口
2. 停止占用端口的進程

```bash
# 使用不同端口
python -m uvicorn app:app --host 0.0.0.0 --port 8001

# Windows: 查找占用進程
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac: 查找占用進程
lsof -i :8000
kill -9 <PID>
```

### 7.5 隊列已滿

**問題**：`Task queue is full`

**解決方案**：
1. 等待任務完成
2. 增加隊列大小（修改task_queue.py）
3. 使用分布式隊列（Redis/RabbitMQ）

## 八、性能優化

### 8.1 配置時間優化

**目標**：從30分鐘縮減到5分鐘

**實現**：
1. 預構建鏡像（一次性）
2. 使用Docker層緩存
3. 並行構建多個鏡像

```bash
# 預構建鏡像
docker build -f Dockerfile -t ai-training:latest .

# 後續直接使用，無需重新構建
```

### 8.2 失敗率降低

**目標**：降低40%失敗率

**實現**：
1. 自動重試機制（最多3次）
2. 超時控制（防止無限運行）
3. 資源清理（防止資源泄漏）

**配置**：
```python
# 在提交任務時設置
{
  "max_retries": 3,  # 最大重試次數
  ...
}
```

### 8.3 日志優化

**實現**：
1. 日志輪轉（10MB，保留5個備份）
2. 級別過濾（控制台INFO，文件DEBUG）
3. 異步寫入（減少IO阻塞）

## 九、擴展使用

### 9.1 自定義訓練腳本

修改 `train.py` 或創建新的訓練腳本：

```python
# train_custom.py
def train(epochs, batch_size, learning_rate):
    # 自定義訓練邏輯
    pass
```

更新Dockerfile：
```dockerfile
COPY train_custom.py /app/train.py
```

### 9.2 使用GPU

**提交任務時**：
```json
{
  "gpu": true,
  "gpu_ids": "0,1"  // 使用GPU 0和1
}
```

**要求**：
- 安裝NVIDIA Docker Runtime
- 配置nvidia-docker

### 9.3 自定義配置

修改 `agent/config.py` 中的默認值：

```python
class TrainingConfig:
    timeout: int = 7200  # 2小時超時
    max_retries: int = 5  # 最多重試5次
    memory_limit: str = "8g"  # 8GB內存
```

## 十、監控和維護

### 10.1 健康檢查

定期檢查服務健康狀態：
```bash
curl http://localhost:8000/health
```

### 10.2 統計監控

查看任務統計：
```bash
curl http://localhost:8000/stats
```

### 10.3 日志清理

定期清理舊日志：
```bash
# 保留最近7天的日志
find logs/ -name "*.log" -mtime +7 -delete
```

### 10.4 容器清理

清理停止的容器：
```bash
docker container prune -f
```

## 十一、最佳實踐

1. **預構建鏡像**：提前構建鏡像，避免運行時構建
2. **資源限制**：設置合理的內存和CPU限制
3. **日志管理**：定期清理舊日志，避免磁盤滿
4. **監控告警**：集成監控系統，及時發現問題
5. **備份恢復**：定期備份任務狀態和日志

## 十二、故障排查流程

1. **檢查服務狀態**：`GET /health`
2. **查看統計信息**：`GET /stats`
3. **檢查日志文件**：`logs/*.log`
4. **檢查Docker狀態**：`docker ps -a`
5. **查看容器日志**：`docker logs <container_id>`
6. **重啟服務**：`python run.py`

## 十三、聯繫和支持

- 查看設計文檔：`DESIGN.md`
- 查看API文檔：http://localhost:8000/docs
- 查看日志：`logs/` 目錄
