"""
任務隊列管理模組
提供線程安全的任務隊列和狀態存儲
支持任務的添加、查詢、更新和刪除
"""
import queue  # Python標準隊列模組，提供線程安全的隊列實現
import threading  # 線程模組，用於線程鎖保證線程安全
from typing import Dict  # 類型提示，字典類型
from agent.models import TrainingTask  # 導入訓練任務模型


# 簡單內存隊列（後續可替換 Redis / RabbitMQ）
training_queue = queue.Queue(maxsize=100)  # 創建任務隊列，最大容量100，超過會阻塞

# 任務狀態存儲（線程安全）
TASK_STORE: Dict[str, TrainingTask] = {}  # 任務存儲字典，key為task_id，value為TrainingTask對象
_store_lock = threading.Lock()  # 線程鎖，用於保護TASK_STORE的並發訪問


def add_task(task: TrainingTask) -> bool:
    """
    添加任務到隊列和存儲
    線程安全操作，先存儲再入隊
    
    Args:
        task: 訓練任務對象，包含所有任務信息
        
    Returns:
        是否成功添加，True表示成功，False表示隊列已滿
    """
    try:
        with _store_lock:  # 獲取線程鎖，確保線程安全
            TASK_STORE[task.task_id] = task  # 將任務存入字典，以task_id為key
        training_queue.put(task, timeout=10)  # 將任務放入隊列，timeout=10表示最多等待10秒
        return True  # 返回成功
    except queue.Full:  # 如果隊列已滿（10秒內無法放入）
        return False  # 返回失敗


def get_task(task_id: str) -> TrainingTask:
    """
    獲取任務
    從存儲字典中查詢任務
    
    Args:
        task_id: 任務唯一標識符
        
    Returns:
        訓練任務對象，如果不存在返回None
    """
    with _store_lock:  # 獲取線程鎖
        return TASK_STORE.get(task_id)  # 從字典中獲取任務，不存在返回None


def update_task(task: TrainingTask):
    """
    更新任務狀態
    更新存儲字典中的任務信息（如狀態、錯誤信息等）
    
    Args:
        task: 更新後的訓練任務對象
    """
    with _store_lock:  # 獲取線程鎖
        if task.task_id in TASK_STORE:  # 如果任務存在於存儲中
            TASK_STORE[task.task_id] = task  # 更新任務對象


def remove_task(task_id: str):
    """
    移除任務
    從存儲字典中刪除任務（通常用於清理已完成任務）
    
    Args:
        task_id: 任務唯一標識符
    """
    with _store_lock:  # 獲取線程鎖
        TASK_STORE.pop(task_id, None)  # 從字典中移除任務，不存在也不報錯（None為默認值）
