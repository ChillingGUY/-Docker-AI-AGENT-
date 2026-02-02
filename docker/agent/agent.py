"""
AI 訓練 Agent 核心模組
負責容器生命周期管理、日志歸集、錯誤處理
"""
import docker  # Docker Python SDK，用於與Docker守護進程通信
import os  # 操作系統接口，用於文件路徑和目錄操作
import time  # 時間相關功能，用於超時控制和時間戳
import threading  # 線程支持（當前未使用，預留擴展）
from typing import Optional, Callable  # 類型提示，提高代碼可讀性
from datetime import datetime  # 日期時間處理，用於日志時間戳

from agent.logger import setup_logger  # 導入日志設置函數
from agent.config import TrainingConfig  # 導入訓練配置類


class TrainingAgent:
    """
    AI 訓練 Agent
    負責：
    - 創建並啟動 Docker 訓練容器
    - 管理容器生命周期
    - 實時採集訓練日志
    - 處理超時、異常、清理資源
    - 支持重試機制
    """

    def __init__(self, config: TrainingConfig):
        """
        初始化 Agent
        
        Args:
            config: 訓練配置對象，包含所有訓練參數和Docker配置
        """
        self.config = config  # 保存配置對象，供後續方法使用
        self.client = docker.from_env()  # 從環境變量創建Docker客戶端（讀取DOCKER_HOST等）
        self.logger = setup_logger("TrainingAgent", log_dir=config.log_dir)  # 創建專用日志記錄器
        
        # 當前運行的容器對象
        self.container: Optional[docker.models.containers.Container] = None  # 容器對象，用於操作容器
        self.container_id: Optional[str] = None  # 容器ID，用於標識和查詢
        
        # 日志文件路徑
        self.log_file_path = os.path.join(  # 拼接日志文件路徑
            config.log_dir,  # 日志目錄
            f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"  # 帶時間戳的日志文件名
        )
        
        # 狀態追蹤
        self.start_time: Optional[float] = None  # 訓練開始時間（Unix時間戳）
        self.is_running = False  # 運行狀態標誌，用於控制日志流

    def run(self, retry_count: int = 0) -> bool:
        """
        執行一次訓練任務
        
        Args:
            retry_count: 當前重試次數，用於遞歸重試
            
        Returns:
            是否成功，True表示訓練成功完成
        """
        self.logger.info(f"Training agent started (attempt {retry_count + 1}/{self.config.max_retries + 1})")  # 記錄開始日志，顯示重試次數
        self.start_time = time.time()  # 記錄開始時間，用於計算總耗時
        
        # 確保日志目錄存在
        os.makedirs(self.config.log_dir, exist_ok=True)  # 創建日志目錄，exist_ok=True表示已存在不報錯

        try:
            # 檢查鏡像是否存在
            self._ensure_image()  # 確保Docker鏡像可用，不存在則嘗試拉取
            
            # 啟動容器
            self._start_container()  # 創建並啟動Docker容器
            self.is_running = True  # 設置運行標誌為True
            
            # 實時採集日志
            self._stream_logs()  # 實時讀取容器日志並寫入文件
            
            # 等待完成
            success = self._wait_for_completion()  # 等待容器結束並檢查退出碼
            
            if success:  # 如果訓練成功
                self.logger.info(f"Training completed successfully in {time.time() - self.start_time:.2f}s")  # 記錄成功日志和耗時
                return True  # 返回成功
            else:  # 如果訓練失敗
                raise RuntimeError("Training failed")  # 拋出異常觸發重試機制
                
        except TimeoutError as e:  # 捕獲超時異常
            self.logger.error(f"Training timeout: {e}")  # 記錄超時錯誤
            self._kill_container()  # 強制終止容器
            if retry_count < self.config.max_retries:  # 如果還有重試機會
                self.logger.info(f"Retrying after {self.config.retry_delay}s...")  # 記錄重試信息
                time.sleep(self.config.retry_delay)  # 等待指定時間後重試
                return self.run(retry_count + 1)  # 遞歸調用，重試次數+1
            raise  # 重試次數用完，重新拋出異常
            
        except Exception as e:  # 捕獲其他所有異常
            self.logger.error(f"Training agent error: {e}", exc_info=True)  # 記錄錯誤詳情（包括堆棧）
            self._kill_container()  # 強制終止容器
            
            # 重試機制
            if retry_count < self.config.max_retries:  # 如果還有重試機會
                self.logger.info(f"Retrying after {self.config.retry_delay}s...")  # 記錄重試信息
                time.sleep(self.config.retry_delay)  # 等待指定時間
                return self.run(retry_count + 1)  # 遞歸重試
            raise  # 重試次數用完，拋出異常
            
        finally:
            self.is_running = False  # 重置運行標誌
            self._cleanup_container()  # 清理容器資源
            self.logger.info("Training agent finished")  # 記錄完成日志

    def _ensure_image(self):
        """確保Docker鏡像存在，不存在則嘗試拉取"""
        try:
            self.client.images.get(self.config.image)  # 嘗試獲取本地鏡像
            self.logger.info(f"Image {self.config.image} found")  # 鏡像存在，記錄日志
        except docker.errors.ImageNotFound:  # 如果鏡像不存在
            self.logger.warning(f"Image {self.config.image} not found, attempting to pull...")  # 記錄警告
            try:
                self.client.images.pull(self.config.image)  # 從Docker Hub拉取鏡像
                self.logger.info(f"Image {self.config.image} pulled successfully")  # 拉取成功
            except Exception as e:  # 拉取失敗
                self.logger.error(f"Failed to pull image: {e}")  # 記錄錯誤
                raise  # 拋出異常，終止執行

    def _start_container(self):
        """
        啟動 Docker 訓練容器
        構建容器配置並啟動
        """
        self.logger.info("Starting training container")  # 記錄啟動日志
        
        # 構建命令
        command = [
            "python", "train.py",
            "--epochs", str(self.config.epochs),
            "--batch-size", str(self.config.batch_size),
            "--learning-rate", str(self.config.learning_rate),
            "--log-dir", "/logs"
        ]
        
        # 構建容器配置
        container_config = {  # Docker容器配置字典
            "image": self.config.image,  # 使用的鏡像名稱
            "command": command,  # 容器啟動命令
            "detach": True,  # 後台運行，不阻塞
            "remove": False,  # 不自動刪除，手動控制清理
            "volumes": self.config.docker_volumes,  # 卷掛載配置（日志目錄等）
            "environment": self.config.env_vars,  # 環境變量
            "mem_limit": self.config.memory_limit,  # 內存限制
            "cpu_count": self.config.cpu_count,  # CPU核心數
            "network_mode": self.config.docker_network or "bridge",  # 網絡模式，默認bridge
            "name": f"training_{int(time.time())}"  # 容器名稱，使用時間戳確保唯一
        }
        
        # GPU支持
        if self.config.gpu:  # 如果啟用GPU
            container_config["runtime"] = "nvidia"  # 設置NVIDIA運行時
            if self.config.gpu_ids:  # 如果指定了GPU ID
                container_config["environment"]["CUDA_VISIBLE_DEVICES"] = self.config.gpu_ids  # 設置可見GPU設備
        
        try:
            self.container = self.client.containers.run(**container_config)  # 運行容器，**解包配置字典
            self.container_id = self.container.id  # 保存容器ID
            self.logger.info(f"Container started: {self.container_id[:12]}")  # 記錄容器ID（前12位）
        except Exception as e:  # 啟動失敗
            self.logger.error(f"Failed to start container: {e}")  # 記錄錯誤
            raise  # 拋出異常

    def _stream_logs(self):
        """
        實時採集容器日志並寫入文件
        使用流式讀取，實時處理日志輸出
        """
        if not self.container:  # 如果容器未啟動
            raise RuntimeError("Container not started")  # 拋出異常

        self.logger.info("Starting log streaming")  # 記錄開始日志流
        
        # 打開日志文件
        with open(self.log_file_path, 'w', encoding='utf-8') as log_file:  # 以寫入模式打開日志文件，UTF-8編碼
            start_time = time.time()  # 記錄開始時間，用於超時檢測
            last_log_time = start_time  # 最後日志時間（當前未使用，預留）
            
            try:
                for log_line in self.container.logs(stream=True, follow=True):  # 流式讀取日志，follow=True持續跟隨
                    current_time = time.time()  # 當前時間戳
                    
                    # 解碼日志
                    try:
                        log_text = log_line.decode("utf-8", errors="ignore").strip()  # 解碼為UTF-8字符串，忽略錯誤
                    except:  # 解碼失敗
                        log_text = str(log_line).strip()  # 轉為字符串
                    
                    if log_text:  # 如果日志不為空
                        # 寫入文件
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 格式化時間戳
                        log_entry = f"[{timestamp}] {log_text}\n"  # 構建日志條目
                        log_file.write(log_entry)  # 寫入文件
                        log_file.flush()  # 立即刷新緩衝區，確保實時寫入
                        
                        # 輸出到logger
                        self.logger.info(f"[TRAIN] {log_text}")  # 同時輸出到系統日志
                        
                        last_log_time = current_time  # 更新最後日志時間
                    
                    # 超時檢測
                    if current_time - start_time > self.config.timeout:  # 如果超過超時時間
                        self.logger.error(f"Training timeout after {self.config.timeout}s")  # 記錄超時錯誤
                        raise TimeoutError(f"Training task timeout after {self.config.timeout}s")  # 拋出超時異常
                    
                    # 檢查容器狀態
                    self.container.reload()  # 重新加載容器狀態
                    if self.container.status != 'running' and not self.is_running:  # 如果容器不在運行且標誌為False
                        break  # 退出循環
                        
            except docker.errors.NotFound:  # 容器不存在
                self.logger.warning("Container not found during log streaming")  # 記錄警告
            except Exception as e:  # 其他異常
                self.logger.error(f"Error during log streaming: {e}")  # 記錄錯誤
                raise  # 重新拋出異常

    def _wait_for_completion(self) -> bool:
        """
        等待容器結束並檢查退出狀態
        
        Returns:
            是否成功，True表示退出碼為0
        """
        if not self.container:  # 如果容器未啟動
            raise RuntimeError("Container not started")  # 拋出異常

        self.logger.info("Waiting for container to finish")  # 記錄等待日志
        
        try:
            result = self.container.wait(timeout=self.config.timeout)  # 等待容器結束，設置超時
            status_code = result.get("StatusCode", 1)  # 獲取退出碼，默認1（失敗）
            
            # 獲取最終日志
            final_logs = self.container.logs(tail=100).decode("utf-8", errors="ignore")  # 獲取最後100行日志
            if final_logs:  # 如果有日志
                self.logger.info(f"Final container logs:\n{final_logs}")  # 記錄最終日志
            
            if status_code == 0:  # 退出碼0表示成功
                self.logger.info("Training completed successfully")  # 記錄成功
                return True  # 返回成功
            else:  # 非0退出碼表示失敗
                self.logger.error(f"Training failed with exit code {status_code}")  # 記錄失敗
                return False  # 返回失敗
                
        except Exception as e:  # 等待過程中的異常
            self.logger.error(f"Error waiting for container: {e}")  # 記錄錯誤
            return False  # 返回失敗

    def _kill_container(self):
        """
        強制終止容器（異常場景）
        用於超時或錯誤時強制停止容器
        """
        if self.container:  # 如果容器存在
            self.logger.warning("Killing training container")  # 記錄警告
            try:
                self.container.reload()  # 重新加載容器狀態
                if self.container.status == 'running':  # 如果容器正在運行
                    self.container.kill()  # 強制終止容器
                    self.logger.info("Container killed")  # 記錄終止成功
            except docker.errors.NotFound:  # 容器不存在
                self.logger.warning("Container not found for killing")  # 記錄警告
            except Exception as e:  # 其他異常
                self.logger.error(f"Error killing container: {e}")  # 記錄錯誤

    def _cleanup_container(self):
        """
        清理容器資源
        刪除已停止的容器，釋放資源
        """
        if self.container:  # 如果容器存在
            self.logger.info("Removing training container")  # 記錄清理日志
            try:
                self.container.reload()  # 重新加載容器狀態
                if self.container.status in ['exited', 'dead', 'created']:  # 如果容器已停止或創建但未運行
                    self.container.remove()  # 刪除容器
                    self.logger.info("Container removed")  # 記錄刪除成功
            except docker.errors.NotFound:  # 容器已不存在
                self.logger.warning("Container already removed")  # 記錄警告
            except Exception as e:  # 其他異常
                self.logger.error(f"Error removing container: {e}")  # 記錄錯誤
        
        self.container = None  # 清空容器對象引用
        self.container_id = None  # 清空容器ID

    def get_status(self) -> dict:
        """
        獲取當前狀態
        用於查詢Agent運行狀態
        
        Returns:
            狀態字典，包含運行狀態、容器信息等
        """
        status = {  # 構建狀態字典
            "is_running": self.is_running,  # 是否正在運行
            "container_id": self.container_id,  # 容器ID
            "start_time": self.start_time,  # 開始時間
            "elapsed_time": time.time() - self.start_time if self.start_time else 0,  # 已運行時間
            "log_file": self.log_file_path  # 日志文件路徑
        }
        
        if self.container:  # 如果容器存在
            try:
                self.container.reload()  # 重新加載容器狀態
                status["container_status"] = self.container.status  # 添加容器狀態
            except:  # 加載失敗
                status["container_status"] = "unknown"  # 設置為未知
        
        return status  # 返回狀態字典
