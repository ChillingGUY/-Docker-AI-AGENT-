"""
配置管理模組
統一管理訓練任務的所有配置參數
"""
from dataclasses import dataclass  # 數據類裝飾器，自動生成__init__等方法
from typing import Optional  # 類型提示，表示可選類型
import os  # 操作系統接口，用於路徑操作


@dataclass
class TrainingConfig:
    """
    訓練配置類
    使用dataclass自動生成構造函數和字符串表示
    包含Docker、訓練參數、資源限制等所有配置
    """
    # Docker鏡像配置
    image: str = "ai-training:latest"  # Docker鏡像名稱，默認使用latest標籤
    image_tag: str = "latest"  # 鏡像標籤，用於版本管理
    
    # 訓練參數
    epochs: int = 5  # 訓練輪數，默認5輪
    batch_size: int = 32  # 批次大小，每次訓練的樣本數
    learning_rate: float = 0.001  # 學習率，控制模型參數更新步長
    
    # 資源配置
    gpu: bool = False  # 是否使用GPU，False表示僅使用CPU
    gpu_ids: Optional[str] = None  # GPU設備ID，如"0,1"表示使用前兩個GPU
    memory_limit: str = "4g"  # 內存限制，4GB
    cpu_count: int = 2  # CPU核心數，分配2個核心
    
    # 超時配置（秒）
    timeout: int = 3600  # 超時時間，3600秒=1小時，超過此時間自動終止
    
    # 日志配置
    log_dir: str = "./logs"  # 日志目錄路徑，相對路徑
    log_level: str = "INFO"  # 日志級別，INFO表示記錄信息級及以上
    
    # 重試配置
    max_retries: int = 3  # 最大重試次數，失敗後最多重試3次
    retry_delay: int = 5  # 重試延遲，失敗後等待5秒再重試
    
    # Docker配置
    docker_network: Optional[str] = None  # Docker網絡模式，None使用默認bridge
    docker_volumes: Optional[dict] = None  # Docker卷掛載配置，None使用默認配置
    
    # 環境變量
    env_vars: Optional[dict] = None  # 容器環境變量，None使用默認配置
    
    def __post_init__(self):
        """
        初始化後處理
        dataclass在__init__後自動調用此方法
        用於設置默認值和驗證配置
        """
        # 確保日志目錄存在
        os.makedirs(self.log_dir, exist_ok=True)  # 創建日志目錄，exist_ok=True表示已存在不報錯
        
        # 設置默認環境變量
        if self.env_vars is None:  # 如果未指定環境變量
            self.env_vars = {  # 設置默認環境變量字典
                "PYTHONUNBUFFERED": "1",  # Python無緩衝輸出，確保日志實時顯示
                "CUDA_VISIBLE_DEVICES": self.gpu_ids if self.gpu_ids else ""  # GPU可見設備
            }
        
        # 設置默認卷掛載
        if self.docker_volumes is None:  # 如果未指定卷掛載
            self.docker_volumes = {  # 設置默認卷掛載字典
                os.path.abspath(self.log_dir): {  # 主機絕對路徑（日志目錄）
                    "bind": "/logs",  # 容器內掛載點
                    "mode": "rw"  # 讀寫模式，允許容器讀寫日志
                }
            }
