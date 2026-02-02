# Docker 故障排查指南

## 一、常見錯誤

### 錯誤1: `Error while fetching server API version: (2, 'CreateFile', '系统找不到指定的文件。')`

**原因**：Docker Desktop 未啟動或未安裝

**解決方案**：

#### Windows系統：

1. **檢查Docker Desktop是否安裝**
   ```powershell
   # 檢查Docker是否在PATH中
   docker --version
   ```
   - 如果命令不存在，需要安裝Docker Desktop
   - 下載地址：https://www.docker.com/products/docker-desktop

2. **啟動Docker Desktop**
   - 在開始菜單搜索 "Docker Desktop"
   - 點擊啟動，等待Docker完全啟動
   - 系統托盤會顯示Docker圖標（鯨魚圖標）

3. **驗證Docker是否運行**
   ```powershell
   # 測試Docker連接
   docker ps
   ```
   - 如果成功，會顯示容器列表（可能為空）
   - 如果失敗，會顯示錯誤信息

4. **檢查Docker服務狀態**
   ```powershell
   # 檢查Docker Desktop進程
   Get-Process "Docker Desktop" -ErrorAction SilentlyContinue
   ```

#### 如果Docker Desktop已啟動但仍失敗：

1. **重啟Docker Desktop**
   - 右鍵系統托盤的Docker圖標
   - 選擇 "Restart Docker Desktop"
   - 等待重啟完成

2. **檢查Docker守護進程**
   ```powershell
   # 檢查Docker守護進程
   docker info
   ```

3. **重置Docker Desktop**（最後手段）
   - 打開Docker Desktop設置
   - 選擇 "Troubleshoot"
   - 點擊 "Reset to factory defaults"

## 二、測試腳本改進

測試腳本已改進，現在會：
- ✅ 檢測Docker服務狀態
- ✅ 提供清晰的錯誤提示
- ✅ 給出解決方案建議

### 運行測試：

```powershell
# 基本功能測試（不需要Docker）
python quick_test.py

# Docker完整測試（需要Docker運行）
python test_docker.py
```

## 三、無Docker環境下的測試

如果無法啟動Docker，仍可以測試部分功能：

### 1. 基本功能測試
```powershell
python quick_test.py
```
這會測試：
- ✅ 模組導入
- ✅ 配置管理
- ✅ 數據模型
- ✅ 日志系統
- ⚠️ Docker（會提示需要Docker，但不影響其他測試）

### 2. API服務測試（不執行Docker任務）
```powershell
# 啟動API服務
python run.py

# 在另一個終端測試API
python test_api.py
```
注意：提交訓練任務會失敗（因為需要Docker），但可以測試：
- ✅ API健康檢查
- ✅ 任務列表查詢
- ✅ 統計信息
- ✅ API文檔訪問

## 四、Docker安裝指南

### Windows安裝步驟：

1. **下載Docker Desktop**
   - 訪問：https://www.docker.com/products/docker-desktop
   - 下載Windows版本

2. **安裝要求**
   - Windows 10 64位：專業版、企業版或教育版（版本1903或更高）
   - 啟用Hyper-V和容器Windows功能
   - 至少4GB RAM

3. **安裝步驟**
   - 運行安裝程序
   - 按照提示完成安裝
   - 安裝完成後重啟電腦

4. **首次啟動**
   - 啟動Docker Desktop
   - 接受服務條款
   - 等待Docker引擎啟動（可能需要幾分鐘）

5. **驗證安裝**
   ```powershell
   docker --version
   docker ps
   ```

## 五、常見問題

### Q1: Docker Desktop啟動很慢

**解決方案**：
- 確保有足夠的內存（至少4GB可用）
- 關閉其他佔用資源的程序
- 檢查Windows更新
- 考慮使用WSL 2後端（Docker Desktop設置中）

### Q2: Docker命令提示"permission denied"

**解決方案**：
- 確保以管理員權限運行
- 檢查Docker Desktop是否以管理員身份運行

### Q3: 無法連接到Docker守護進程

**解決方案**：
1. 檢查Docker Desktop是否運行
2. 重啟Docker Desktop
3. 檢查防火牆設置
4. 檢查Docker服務是否啟動

### Q4: 測試時提示鏡像不存在

**解決方案**：
```powershell
# 構建鏡像
docker build -f Dockerfile -t ai-training:latest .

# 驗證鏡像
docker images | grep ai-training
```

## 六、替代方案

如果無法使用Docker，可以：

### 方案1：使用虛擬環境
```powershell
# 創建虛擬環境
python -m venv venv
venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt
pip install -r requirements-training.txt

# 直接運行訓練腳本（不通過Docker）
python train.py --epochs 5
```

### 方案2：使用WSL 2 + Docker
- 安裝WSL 2
- 在WSL 2中安裝Docker
- 在WSL 2中運行項目

## 七、驗證Docker環境

運行以下命令驗證Docker環境：

```powershell
# 1. 檢查Docker版本
docker --version

# 2. 檢查Docker守護進程
docker info

# 3. 測試運行容器
docker run hello-world

# 4. 檢查Docker Compose（如果使用）
docker-compose --version
```

如果所有命令都成功，Docker環境配置正確。

## 八、獲取幫助

如果問題仍未解決：

1. **查看Docker Desktop日志**
   - Docker Desktop → Settings → Troubleshoot → View logs

2. **檢查系統要求**
   - 確保系統滿足Docker Desktop要求

3. **查看項目文檔**
   - `README.md` - 項目說明
   - `USAGE_GUIDE.md` - 使用指南
   - `DESIGN.md` - 設計文檔

4. **社區支持**
   - Docker官方文檔：https://docs.docker.com/
   - Docker社區論壇：https://forums.docker.com/
