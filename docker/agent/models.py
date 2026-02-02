"""
數據模型定義
定義訓練任務的數據結構和狀態枚舉
"""
from enum import Enum  # 枚舉類，用於定義固定狀態值
from dataclasses import dataclass, field  # 數據類，自動生成構造函數；field用於設置默認值
from typing import Optional  # 類型提示，可選類型
from datetime import datetime  # 日期時間處理，用於時間戳


class TaskStatus(str, Enum):
    """
    訓練任務狀態枚舉
    繼承str和Enum，既是字符串又是枚舉，便於序列化和比較
    定義任務的完整生命周期狀態
    """
    PENDING = "pending"  # 待處理狀態，任務已創建但未開始執行
    RUNNING = "running"  # 運行中狀態，任務正在執行
    SUCCESS = "success"  # 成功狀態，任務執行成功完成
    FAILED = "failed"  # 失敗狀態，任務執行失敗
    CANCELLED = "cancelled"  # 已取消狀態，任務被用戶或系統取消


@dataclass
class TrainingTask:
    """
    訓練任務數據結構
    使用dataclass自動生成構造函數、__repr__等方法
    包含任務的所有信息和狀態
    """
    task_id: str  # 任務唯一標識符，通常使用UUID
    epochs: int  # 訓練輪數，必須指定
    batch_size: int = 32  # 批次大小，默認32
    learning_rate: float = 0.001  # 學習率，默認0.001
    gpu: bool = False  # 是否使用GPU，默認False（CPU）
    gpu_ids: Optional[str] = None  # GPU設備ID字符串，如"0,1"，None表示使用所有
    status: TaskStatus = TaskStatus.PENDING  # 任務狀態，默認待處理
    error: Optional[str] = None  # 錯誤信息，成功時為None，失敗時包含錯誤描述
    container_id: Optional[str] = None  # Docker容器ID，任務運行時設置
    log_file: Optional[str] = None  # 日志文件路徑，任務運行時設置
    created_at: datetime = field(default_factory=datetime.now)  # 創建時間，使用field確保每次創建時獲取當前時間
    started_at: Optional[datetime] = None  # 開始執行時間，任務開始時設置
    completed_at: Optional[datetime] = None  # 完成時間，任務結束時設置
    retry_count: int = 0  # 當前重試次數，失敗重試時遞增
    max_retries: int = 3  # 最大重試次數，默認3次
    
    def to_dict(self) -> dict:
        """
        轉換為字典
        用於API響應和序列化
        
        Returns:
            包含所有字段的字典，時間字段轉為ISO格式字符串
        """
        return {  # 返回字典
            "task_id": self.task_id,  # 任務ID
            "epochs": self.epochs,  # 訓練輪數
            "batch_size": self.batch_size,  # 批次大小
            "learning_rate": self.learning_rate,  # 學習率
            "gpu": self.gpu,  # GPU標誌
            "gpu_ids": self.gpu_ids,  # GPU設備ID
            "status": self.status.value,  # 狀態值（枚舉轉字符串）
            "error": self.error,  # 錯誤信息
            "container_id": self.container_id,  # 容器ID
            "log_file": self.log_file,  # 日志文件路徑
            "created_at": self.created_at.isoformat() if self.created_at else None,  # 創建時間轉ISO格式（如2026-01-28T19:00:00）
            "started_at": self.started_at.isoformat() if self.started_at else None,  # 開始時間轉ISO格式
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,  # 完成時間轉ISO格式
            "retry_count": self.retry_count,  # 重試次數
            "max_retries": self.max_retries  # 最大重試次數
        }
