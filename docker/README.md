# AI訓練Agent中間件

基於Docker的AI訓練標準化中間件，實現環境配置標準化、日志歸集統一、訓練可控性提升。

## 目標

- ✅ 配置時間從30分鐘縮減到5分鐘
- ✅ 訓練失敗率降低40%
- ✅ 標準化Docker鏡像環境
- ✅ 統一日志歸集
- ✅ 容器生命周期管理
- ✅ 自動重試機制

## 項目結構

```
.
├── agent/                 # Agent核心模組
│   ├── __init__.py
│   ├── agent.py          # 訓練Agent主類
│   ├── config.py          # 配置管理
│   ├── logger.py          # 日志管理
│   └── task_queue.py      # 任務隊列
├── app.py                 # FastAPI應用
├── worker.py              # Worker進程
├── models.py              # 數據模型
├── train.py               # 標準化訓練腳本
├── Dockerfile             # 訓練鏡像Dockerfile
├── Dockerfile.api         # API服務Dockerfile
├── docker-compose.yml     # Docker Compose配置
├── requirements.txt       # API服務依賴
├── requirements-training.txt  # 訓練容器依賴
├── test_docker.py         # Docker測試腳本
├── test_api.py            # API測試腳本
└── run_tests.sh           # 完整測試腳本
```

## 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 構建訓練鏡像

```bash
docker build -f Dockerfile -t ai-training:latest .
```

### 3. 啟動服務

```bash
# 方式1: 直接運行
python -m uvicorn app:app --host 0.0.0.0 --port 8000

# 方式2: 使用Docker Compose
docker-compose up -d
```

### 4. 測試

```bash
# Docker測試
python test_docker.py

# API測試
python test_api.py

# 完整測試
bash run_tests.sh
```

## API文檔

服務啟動後，訪問 http://localhost:8000/docs 查看Swagger文檔。

### 主要端點

- `POST /train` - 提交訓練任務
- `GET /train/{task_id}` - 查詢任務狀態
- `GET /train` - 列出所有任務
- `GET /stats` - 獲取統計信息
- `DELETE /train/{task_id}` - 取消任務
- `GET /health` - 健康檢查

### 示例

```bash
# 提交訓練任務
curl -X POST "http://localhost:8000/train" \
  -H "Content-Type: application/json" \
  -d '{
    "epochs": 5,
    "batch_size": 32,
    "learning_rate": 0.001
  }'

# 查詢任務狀態
curl "http://localhost:8000/train/{task_id}"

# 獲取統計信息
curl "http://localhost:8000/stats"
```

## 功能特性

### 1. 標準化環境配置

- 統一的Docker鏡像，包含所有必要依賴
- 環境變量標準化配置
- 快速部署（5分鐘內完成配置）

### 2. 日志歸集

- 實時日志採集
- 統一日志格式
- 日志文件自動歸檔
- 支持日志查詢和檢索

### 3. 容器生命周期管理

- 自動容器創建和啟動
- 資源清理和回收
- 異常處理和恢復
- 超時控制

### 4. 錯誤處理和重試

- 自動重試機制（最多3次）
- 詳細錯誤日志記錄
- 失敗任務狀態追蹤

### 5. 任務隊列管理

- 異步任務處理
- 任務狀態追蹤
- 任務列表和統計

## 配置說明

### TrainingConfig 參數

- `image`: Docker鏡像名稱
- `epochs`: 訓練輪數
- `batch_size`: 批次大小
- `learning_rate`: 學習率
- `gpu`: 是否使用GPU
- `gpu_ids`: GPU設備ID
- `timeout`: 超時時間（秒）
- `max_retries`: 最大重試次數
- `log_dir`: 日志目錄

## 日志位置

所有日志文件保存在 `./logs/` 目錄下：

- `TrainingAgent_YYYYMMDD.log` - Agent日志
- `TrainingWorker_YYYYMMDD.log` - Worker日志
- `training_YYYYMMDD_HHMMSS.log` - 訓練任務日志

## 性能優化

1. **配置時間優化**: 使用預構建鏡像，減少依賴安裝時間
2. **失敗率降低**: 
   - 自動重試機制
   - 完善的錯誤處理
   - 資源清理保證
3. **日志歸集**: 實時採集，統一格式，便於問題排查

## 故障排查

### Docker連接問題

```bash
# 檢查Docker服務
docker ps

# 檢查Docker socket權限
ls -l /var/run/docker.sock
```

### 鏡像構建失敗

```bash
# 清理舊鏡像
docker system prune -a

# 重新構建
docker build --no-cache -f Dockerfile -t ai-training:latest .
```

### 任務執行失敗

1. 檢查日志文件: `./logs/`
2. 查看容器狀態: `docker ps -a`
3. 檢查API響應: `curl http://localhost:8000/stats`

## 開發

### 添加新的訓練腳本

1. 修改 `train.py` 或創建新的訓練腳本
2. 更新 `Dockerfile` 中的CMD命令
3. 重新構建鏡像

### 擴展API功能

1. 在 `app.py` 中添加新的端點
2. 在 `models.py` 中添加新的數據模型
3. 更新 `worker.py` 處理邏輯

## 許可證

MIT License
