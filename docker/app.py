"""
FastAPI 應用主程序
提供訓練任務提交、查詢、管理等API
採用RESTful API設計，支持異步任務處理
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks  # FastAPI框架，HTTP異常，後台任務
from fastapi.responses import JSONResponse  # JSON響應（當前未使用，預留）
from pydantic import BaseModel  # 數據驗證模型基類
import uuid  # UUID生成，用於創建唯一任務ID
from typing import Optional, List  # 類型提示，可選類型和列表

from agent.task_queue import add_task, get_task, update_task, TASK_STORE  # 導入任務隊列管理函數和存儲
from agent.models import TrainingTask, TaskStatus  # 導入任務模型和狀態枚舉
from worker import get_worker  # 導入Worker獲取函數

# 創建 FastAPI 應用
app = FastAPI(  # 創建FastAPI應用實例
    title="AI Training Service",  # API標題，用於文檔
    description="Docker-based AI Training Agent Service - 標準化訓練環境，統一日志歸集",  # API描述
    version="1.0.0"  # API版本號
)

# 啟動時初始化Worker
@app.on_event("startup")  # FastAPI啟動事件裝飾器
async def startup_event():  # 異步啟動事件處理函數
    """應用啟動時初始化Worker"""
    worker = get_worker()  # 獲取全局Worker實例（單例模式）
    worker.start()  # 啟動Worker，開始處理任務隊列
    print("Training worker started")  # 打印啟動信息（用於調試）


@app.on_event("shutdown")  # FastAPI關閉事件裝飾器
async def shutdown_event():  # 異步關閉事件處理函數
    """應用關閉時停止Worker"""
    worker = get_worker()  # 獲取全局Worker實例
    worker.stop()  # 停止Worker，等待任務完成
    print("Training worker stopped")  # 打印停止信息


class TrainRequest(BaseModel):
    """
    提交訓練任務的請求體
    使用Pydantic進行自動數據驗證和序列化
    """
    epochs: int = 5
    batch_size: int = 32
    learning_rate: float = 0.001
    gpu: bool = False
    gpu_ids: Optional[str] = None
    max_retries: int = 3


class TrainResponse(BaseModel):
    """
    提交訓練任務的返回體
    包含任務ID和初始狀態
    """
    task_id: str  # 任務唯一標識符
    status: str  # 任務狀態字符串
    message: str  # 響應消息


class TaskStatusResponse(BaseModel):
    """
    查詢任務狀態返回體
    """
    task_id: str
    status: str
    epochs: int
    batch_size: int
    learning_rate: float
    gpu: bool
    error: Optional[str] = None
    container_id: Optional[str] = None
    log_file: Optional[str] = None
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    retry_count: int


class TaskListResponse(BaseModel):
    """
    任務列表返回體
    包含任務總數和任務列表
    """
    total: int  # 任務總數
    tasks: List[dict]  # 任務字典列表


@app.get("/")  # GET根路徑
async def root():  # 異步根路徑處理函數
    """根路徑，返回服務基本信息"""
    return {  # 返回JSON字典
        "service": "AI Training Agent Service",  # 服務名稱
        "version": "1.0.0",  # 版本號
        "description": "基於Docker的AI訓練中間件，標準化環境配置，統一日志歸集"  # 服務描述
    }


@app.get("/health")  # GET健康檢查端點
async def health_check():  # 異步健康檢查函數
    """健康檢查，用於監控服務狀態"""
    worker = get_worker()  # 獲取Worker實例
    return {  # 返回健康狀態
        "status": "healthy",  # 服務狀態
        "worker_running": worker.running if worker else False  # Worker運行狀態
    }


@app.post("/train", response_model=TrainResponse)  # POST提交訓練任務，指定響應模型
async def submit_training(req: TrainRequest):  # 異步提交訓練任務函數
    """
    提交一個新的訓練任務
    創建任務對象，加入隊列，返回任務ID
    """
    try:
        # 生成唯一任務 ID
        task_id = str(uuid.uuid4())  # 生成UUID並轉為字符串，確保唯一性

        # 創建訓練任務對象
        task = TrainingTask(
            task_id=task_id,
            epochs=req.epochs,
            batch_size=req.batch_size,
            learning_rate=req.learning_rate,
            gpu=req.gpu,
            gpu_ids=req.gpu_ids,
            max_retries=req.max_retries,
            status=TaskStatus.PENDING,
        )

        # 添加到隊列和存儲
        if not add_task(task):  # 嘗試添加任務到隊列，失敗返回False
            raise HTTPException(  # 拋出HTTP異常
                status_code=503,  # 503服務不可用
                detail="Task queue is full, please try again later"  # 錯誤詳情：隊列已滿
            )

        return TrainResponse(  # 返回響應對象
            task_id=task_id,  # 任務ID
            status=task.status.value,  # 任務狀態值（枚舉轉字符串）
            message="Training task submitted successfully"  # 成功消息
        )
    except Exception as e:  # 捕獲所有異常
        raise HTTPException(  # 拋出HTTP異常
            status_code=500,  # 500內部服務器錯誤
            detail=f"Failed to submit training task: {str(e)}"  # 錯誤詳情
        )


@app.get("/train/{task_id}", response_model=TaskStatusResponse)  # GET查詢任務狀態，路徑參數task_id
async def get_task_status(task_id: str):  # 異步查詢任務狀態函數
    """
    查詢訓練任務狀態
    根據任務ID查詢任務信息和當前狀態
    """
    task = get_task(task_id)  # 從存儲中獲取任務對象

    if not task:  # 如果任務不存在
        raise HTTPException(  # 拋出HTTP異常
            status_code=404,  # 404未找到
            detail="Task not found"  # 錯誤詳情
        )

    return TaskStatusResponse(
        task_id=task.task_id,
        status=task.status.value,
        epochs=task.epochs,
        batch_size=task.batch_size,
        learning_rate=task.learning_rate,
        gpu=task.gpu,
        error=task.error,
        container_id=task.container_id,
        log_file=task.log_file,
        created_at=task.created_at.isoformat() if task.created_at else None,
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        retry_count=task.retry_count,
    )


@app.get("/train", response_model=TaskListResponse)  # GET任務列表，查詢參數
async def list_tasks(status: Optional[str] = None, limit: int = 50):  # 異步任務列表函數，可選狀態過濾和數量限制
    """
    列出所有訓練任務
    支持按狀態過濾和數量限制
    
    Args:
        status: 可選的狀態過濾，如"pending"、"running"等
        limit: 返回數量限制，默認50
    """
    tasks = list(TASK_STORE.values())  # 獲取所有任務對象列表
    
    # 狀態過濾
    if status:  # 如果指定了狀態過濾
        try:
            status_enum = TaskStatus(status)  # 將字符串轉為狀態枚舉
            tasks = [t for t in tasks if t.status == status_enum]  # 過濾出匹配狀態的任務
        except ValueError:  # 如果狀態字符串無效
            raise HTTPException(  # 拋出HTTP異常
                status_code=400,  # 400錯誤請求
                detail=f"Invalid status: {status}"  # 錯誤詳情
            )
    
    # 按創建時間排序（最新的在前）
    tasks.sort(key=lambda x: x.created_at, reverse=True)  # 按創建時間降序排序（最新的在前）
    
    # 限制數量
    tasks = tasks[:limit]  # 切片取前limit個任務
    
    return TaskListResponse(  # 返回任務列表響應
        total=len(tasks),  # 任務總數
        tasks=[task.to_dict() for task in tasks]  # 將任務對象轉為字典列表
    )


@app.delete("/train/{task_id}")  # DELETE取消任務，路徑參數task_id
async def cancel_task(task_id: str):  # 異步取消任務函數
    """
    取消訓練任務（僅限待處理或運行中的任務）
    已完成的任務無法取消
    """
    task = get_task(task_id)  # 從存儲中獲取任務對象

    if not task:  # 如果任務不存在
        raise HTTPException(  # 拋出HTTP異常
            status_code=404,  # 404未找到
            detail="Task not found"  # 錯誤詳情
        )

    if task.status in [TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED]:  # 如果任務已完成、失敗或已取消
        raise HTTPException(  # 拋出HTTP異常
            status_code=400,  # 400錯誤請求
            detail=f"Cannot cancel task with status: {task.status.value}"  # 錯誤詳情：無法取消已完成任務
        )

    # 更新任務狀態
    task.status = TaskStatus.CANCELLED  # 設置狀態為已取消
    task.error = "Task cancelled by user"  # 設置錯誤信息
    update_task(task)  # 更新任務狀態到存儲

    return {  # 返回取消成功響應
        "task_id": task_id,  # 任務ID
        "status": "cancelled",  # 狀態
        "message": "Task cancelled successfully"  # 成功消息
    }


@app.get("/stats")  # GET統計信息端點
async def get_stats():  # 異步獲取統計信息函數
    """
    獲取統計信息
    統計各狀態任務數量和成功率
    """
    tasks = list(TASK_STORE.values())  # 獲取所有任務對象列表
    
    stats = {  # 構建統計字典
        "total": len(tasks),  # 總任務數
        "pending": len([t for t in tasks if t.status == TaskStatus.PENDING]),  # 待處理任務數
        "running": len([t for t in tasks if t.status == TaskStatus.RUNNING]),  # 運行中任務數
        "success": len([t for t in tasks if t.status == TaskStatus.SUCCESS]),  # 成功任務數
        "failed": len([t for t in tasks if t.status == TaskStatus.FAILED]),  # 失敗任務數
        "cancelled": len([t for t in tasks if t.status == TaskStatus.CANCELLED])  # 已取消任務數
    }
    
    # 計算成功率
    completed = stats["success"] + stats["failed"]  # 已完成任務數（成功+失敗）
    if completed > 0:  # 如果有已完成任務
        stats["success_rate"] = round(stats["success"] / completed * 100, 2)  # 計算成功率（保留2位小數）
    else:  # 如果沒有已完成任務
        stats["success_rate"] = 0.0  # 成功率為0
    
    return stats  # 返回統計信息
