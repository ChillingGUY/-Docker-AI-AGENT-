"""
日志管理模組
統一日志格式，集中歸集
提供統一的日志接口，支持文件和控制台輸出
"""
import logging  # Python標準日志模組
import os  # 操作系統接口，用於路徑操作
from datetime import datetime  # 日期時間處理，用於日志文件名
from logging.handlers import RotatingFileHandler  # 日志輪轉處理器，自動管理日志文件大小
from typing import Optional  # 類型提示，可選類型


def setup_logger(
    name: str,  # 日志記錄器名稱，用於區分不同模組的日志
    log_dir: str = "./logs",  # 日志目錄，默認當前目錄下的logs文件夾
    log_level: str = "INFO",  # 日志級別，INFO表示記錄信息級及以上（DEBUG/INFO/WARNING/ERROR/CRITICAL）
    console_output: bool = True  # 是否輸出到控制台，True表示同時輸出到文件和控制台
) -> logging.Logger:  # 返回配置好的日志記錄器對象
    """
    設置日志記錄器
    創建統一的日志格式，支持文件輪轉和控制台輸出
    
    Args:
        name: 日志記錄器名稱，通常使用模組名
        log_dir: 日志目錄路徑
        log_level: 日志級別字符串（DEBUG/INFO/WARNING/ERROR/CRITICAL）
        console_output: 是否同時輸出到控制台
    
    Returns:
        配置好的日志記錄器，可直接使用logger.info()等方法
    """
    # 確保日志目錄存在
    os.makedirs(log_dir, exist_ok=True)  # 創建日志目錄，exist_ok=True表示已存在不報錯
    
    # 創建日志記錄器
    logger = logging.getLogger(name)  # 獲取或創建指定名稱的日志記錄器
    logger.setLevel(getattr(logging, log_level.upper()))  # 設置日志級別，getattr動態獲取logging.INFO等常量
    
    # 避免重複添加handler
    if logger.handlers:  # 如果已有handler（避免重複添加）
        return logger  # 直接返回，不重複配置
    
    # 統一日志格式
    formatter = logging.Formatter(  # 創建格式器，定義日志輸出格式
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',  # 格式：時間-名稱-級別-[文件名:行號]-消息
        datefmt='%Y-%m-%d %H:%M:%S'  # 日期時間格式：年-月-日 時:分:秒
    )
    
    # 文件handler - 按日期和大小輪轉
    log_file = os.path.join(log_dir, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")  # 日志文件路徑，文件名包含日期（如TrainingAgent_20260128.log）
    file_handler = RotatingFileHandler(  # 創建輪轉文件處理器
        log_file,  # 日志文件路徑
        maxBytes=10 * 1024 * 1024,  # 最大文件大小10MB，超過後自動輪轉
        backupCount=5,  # 保留5個備份文件（如.log.1, .log.2等）
        encoding='utf-8'  # 文件編碼UTF-8，支持中文
    )
    file_handler.setLevel(logging.DEBUG)  # 文件handler記錄DEBUG及以上級別（比控制台更詳細）
    file_handler.setFormatter(formatter)  # 應用格式器
    logger.addHandler(file_handler)  # 將handler添加到記錄器
    
    # 控制台handler
    if console_output:  # 如果需要控制台輸出
        console_handler = logging.StreamHandler()  # 創建流處理器（輸出到標準輸出）
        console_handler.setLevel(getattr(logging, log_level.upper()))  # 設置日志級別（通常比文件級別高）
        console_handler.setFormatter(formatter)  # 應用相同的格式器
        logger.addHandler(console_handler)  # 將handler添加到記錄器
    
    return logger  # 返回配置好的日志記錄器
