"""
Worker 進程
從隊列中消費訓練任務並執行
採用生產者-消費者模式，後台異步處理訓練任務
"""
import threading  # 線程模組，用於創建後台工作線程
import time  # 時間模組，用於延遲和時間戳
from typing import Optional  # 類型提示，可選類型
from datetime import datetime  # 日期時間處理，用於記錄任務時間

from agent.agent import TrainingAgent  # 導入訓練Agent類
from agent.config import TrainingConfig  # 導入配置類
from agent.logger import setup_logger  # 導入日志設置函數
from agent.task_queue import training_queue, update_task, get_task  # 導入隊列和任務管理函數
from agent.models import TrainingTask, TaskStatus  # 導入任務模型和狀態枚舉


class TrainingWorker:
    """
    訓練任務Worker
    負責從任務隊列中消費任務並執行
    運行在獨立線程中，不阻塞主進程
    """
    
    def __init__(self, log_dir: str = "./logs"):
        """
        初始化Worker
        
        Args:
            log_dir: 日志目錄路徑，用於存儲Worker運行日志
        """
        self.logger = setup_logger("TrainingWorker", log_dir=log_dir)  # 創建Worker專用日志記錄器
        self.running = False  # 運行狀態標誌，False表示未運行
        self.thread: Optional[threading.Thread] = None  # 工作線程對象，None表示未創建
        
    def start(self):
        """
        啟動Worker
        創建後台線程開始處理任務
        """
        if self.running:  # 如果已經在運行
            self.logger.warning("Worker already running")  # 記錄警告，不重複啟動
            return  # 直接返回
            
        self.running = True  # 設置運行標誌為True
        self.thread = threading.Thread(target=self._run, daemon=True)  # 創建守護線程，daemon=True表示主進程退出時自動退出
        self.thread.start()  # 啟動線程，開始執行_run方法
        self.logger.info("Training worker started")  # 記錄啟動日志
    
    def stop(self):
        """
        停止Worker
        設置停止標誌並等待線程結束
        """
        self.running = False  # 設置運行標誌為False，觸發_run循環退出
        if self.thread:  # 如果線程存在
            self.thread.join(timeout=10)  # 等待線程結束，最多等待10秒
        self.logger.info("Training worker stopped")  # 記錄停止日志
    
    def _run(self):
        """
        Worker主循環
        持續從隊列中獲取任務並執行
        運行在獨立線程中
        """
        self.logger.info("Worker loop started")  # 記錄循環開始日志
        
        while self.running:  # 只要運行標誌為True就持續循環
            try:
                # 從隊列獲取任務（阻塞，最多等待1秒）
                try:
                    task = training_queue.get(timeout=1)  # 從隊列獲取任務，timeout=1表示最多等待1秒
                except:  # 如果隊列為空（超時）或其他異常
                    continue  # 繼續下一次循環，不處理異常
                
                self.logger.info(f"Processing task: {task.task_id}")  # 記錄開始處理任務
                
                # 更新任務狀態為運行中
                task.status = TaskStatus.RUNNING  # 設置狀態為運行中
                task.started_at = datetime.now()  # 記錄開始時間
                update_task(task)  # 更新任務狀態到存儲
                
                try:
                    # 創建配置
                    config = TrainingConfig(
                        image="ai-training:latest",
                        epochs=task.epochs,
                        batch_size=task.batch_size,
                        learning_rate=task.learning_rate,
                        gpu=task.gpu,
                        gpu_ids=task.gpu_ids,
                        log_dir="./logs",
                        max_retries=task.max_retries,
                    )
                    
                    # 創建Agent並執行
                    agent = TrainingAgent(config)  # 創建訓練Agent實例
                    success = agent.run(retry_count=task.retry_count)  # 執行訓練，傳入當前重試次數
                    
                    # 更新任務狀態
                    task.completed_at = datetime.now()  # 記錄完成時間
                    task.container_id = agent.container_id  # 保存容器ID
                    task.log_file = agent.log_file_path  # 保存日志文件路徑
                    
                    if success:  # 如果訓練成功
                        task.status = TaskStatus.SUCCESS  # 設置狀態為成功
                        self.logger.info(f"Task {task.task_id} completed successfully")  # 記錄成功日志
                    else:  # 如果訓練失敗
                        task.status = TaskStatus.FAILED  # 設置狀態為失敗
                        task.error = "Training failed"  # 設置錯誤信息
                        self.logger.error(f"Task {task.task_id} failed")  # 記錄失敗日志
                        
                except Exception as e:  # 捕獲執行過程中的異常
                    # 任務失敗
                    task.status = TaskStatus.FAILED  # 設置狀態為失敗
                    task.error = str(e)  # 保存異常信息
                    task.completed_at = datetime.now()  # 記錄完成時間（實際是失敗時間）
                    self.logger.error(f"Task {task.task_id} error: {e}", exc_info=True)  # 記錄錯誤詳情（包括堆棧）
                
                finally:  # 無論成功失敗都執行
                    # 更新任務狀態
                    update_task(task)  # 更新任務狀態到存儲
                    training_queue.task_done()  # 標記任務完成，用於隊列計數
                    
            except Exception as e:  # 捕獲Worker循環中的異常
                self.logger.error(f"Worker error: {e}", exc_info=True)  # 記錄錯誤詳情
                time.sleep(1)  # 等待1秒後繼續，避免快速重試


# 全局Worker實例
_worker: Optional[TrainingWorker] = None  # 全局Worker實例，使用單例模式


def get_worker() -> TrainingWorker:
    """
    獲取全局Worker實例
    單例模式，確保整個應用只有一個Worker實例
    
    Returns:
        全局Worker實例
    """
    global _worker  # 聲明使用全局變量
    if _worker is None:  # 如果實例不存在
        _worker = TrainingWorker()  # 創建新實例
    return _worker  # 返回實例
