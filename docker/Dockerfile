# AI訓練標準化鏡像
# 目標：統一環境配置，減少配置時間從30分鐘到5分鐘
FROM python:3.10-slim

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴文件
COPY requirements-training.txt /app/requirements.txt

# 安裝Python依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製訓練腳本
COPY train.py /app/train.py

# 創建日志目錄
RUN mkdir -p /logs

# 設置環境變量
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 默認命令
CMD ["python", "train.py", "--epochs", "5"]
