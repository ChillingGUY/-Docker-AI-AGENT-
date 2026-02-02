"""
Docker測試腳本
驗證Docker鏡像構建和容器運行
"""
import docker
import time
import os
import sys
from agent.logger import setup_logger

logger = setup_logger("DockerTest")


def test_docker_connection():
    """測試Docker連接"""
    logger.info("Testing Docker connection...")
    try:
        client = docker.from_env()  # 從環境變量創建Docker客戶端
        client.ping()  # 測試連接，ping成功表示Docker服務運行正常
        logger.info("[OK] Docker connection successful")
        return True
    except docker.errors.DockerException as e:
        # Docker服務未運行或無法連接
        error_msg = str(e)
        if "CreateFile" in error_msg or "系统找不到指定的文件" in error_msg:
            logger.error("[FAIL] Docker connection failed: Docker Desktop is not running")
            logger.info("  → Solution: Please start Docker Desktop and wait for it to fully start")
            logger.info("  → Windows: Open Docker Desktop application")
            logger.info("  → Check: docker ps (should work in terminal)")
        else:
            logger.error("[FAIL] Docker connection failed: %s", e)
        return False
    except Exception as e:
        logger.error("[FAIL] Docker connection failed: %s", e)
        logger.info("  → Please ensure Docker Desktop is installed and running")
        return False


def build_image():
    """構建訓練鏡像"""
    logger.info("Building training image...")
    try:
        client = docker.from_env()  # 獲取Docker客戶端
        
        # 先檢查Docker連接
        try:
            client.ping()  # 確保Docker服務可用
        except Exception:
            logger.error("[FAIL] Cannot build image: Docker service is not available")
            logger.info("  → Please start Docker Desktop first")
            return False
        
        # 構建鏡像（串流輸出構建日志，實時顯示進度）
        logger.info("  -> Building image (first time may take 5-10 min)...")
        build_logs = client.api.build(  # 使用 api.build 獲取生成器，串流輸出
            path=os.path.abspath("."),
            dockerfile="Dockerfile",
            tag="ai-training:latest",
            rm=True,
            decode=True,
        )
        image_id = None
        for chunk in build_logs:
            err = chunk.get("error")
            if err:
                raise RuntimeError(f"Build failed: {err}")
            if chunk.get("stream"):  # 構建步驟輸出 (e.g. Step 1/6)
                raw = chunk["stream"].rstrip()
                if raw:
                    line = raw.encode("utf-8", errors="replace").decode("utf-8")
                    try:
                        logger.info("    %s", line)
                    except Exception:
                        logger.info("    [build output line]")
            if chunk.get("status"):  # 拉取基礎鏡像等狀態
                status = chunk["status"]
                progress = chunk.get("progress", "") or ""
                msg = f"    {status} {progress}".rstrip()
                try:
                    logger.info("%s", msg)
                except Exception:
                    logger.info("    [build status]")
            if chunk.get("aux", {}).get("ID"):
                image_id = chunk["aux"]["ID"]
        if not image_id:
            image = client.images.get("ai-training:latest")
            image_id = image.id
        logger.info("  -> Image built successfully: %s", image_id[:12])
        return True
    except docker.errors.DockerException as e:
        error_msg = str(e)
        if "CreateFile" in error_msg or "系统找不到指定的文件" in error_msg:
            logger.error("[FAIL] Image build failed: Docker Desktop is not running")
            logger.info("  → Solution: Start Docker Desktop and try again")
        else:
            logger.error("[FAIL] Image build failed: %s", e)
        return False
    except Exception as e:
        logger.error("[FAIL] Image build failed: %s", e)
        return False


def test_container_run():
    """測試容器運行"""
    logger.info("Testing container run...")
    
    # 確保日志目錄存在
    log_dir = "./logs"
    os.makedirs(log_dir, exist_ok=True)
    
    try:
        client = docker.from_env()  # 獲取Docker客戶端
        
        # 先檢查鏡像是否存在
        try:
            client.images.get("ai-training:latest")  # 檢查鏡像是否存在
        except docker.errors.ImageNotFound:
            logger.error("[FAIL] Container run failed: Image 'ai-training:latest' not found")
            logger.info("  → Solution: Run 'docker build -f Dockerfile -t ai-training:latest .' first")
            return False
        
        # 檢查Docker連接
        try:
            client.ping()
        except Exception:
            logger.error("[FAIL] Container run failed: Docker service is not available")
            return False
        
        # 運行容器（command 覆蓋鏡像 CMD，需傳完整命令：python train.py ...）
        container = client.containers.run(  # 運行Docker容器
            image="ai-training:latest",  # 使用的鏡像
            command=["python", "train.py", "--epochs", "2", "--batch-size", "16", "--log-dir", "/logs"],
            detach=True,  # 後台運行
            volumes={  # 卷掛載配置
                os.path.abspath(log_dir): {  # 主機日志目錄
                    "bind": "/logs",  # 容器內掛載點
                    "mode": "rw"  # 讀寫模式
                }
            },
            remove=False  # 不自動刪除，手動清理
        )
        
        logger.info("[OK] Container started: %s", container.id[:12])
        
        # 實時輸出日志
        logger.info("Container logs:")
        for log in container.logs(stream=True, follow=True):  # 流式讀取日志
            log_line = log.decode("utf-8", errors="ignore").strip()  # 解碼日志
            if log_line:
                try:
                    logger.info("  %s", log_line)
                except Exception:
                    logger.info("  [container log line]")
        
        # 等待容器完成
        result = container.wait()  # 等待容器結束
        status_code = result.get("StatusCode", 1)  # 獲取退出碼
        
        if status_code == 0:  # 退出碼0表示成功
            logger.info("[OK] Container completed successfully")
        else:
            logger.error("[FAIL] Container failed with exit code %s", status_code)
        
        # 清理
        container.remove()  # 刪除容器
        
        return status_code == 0
        
    except docker.errors.DockerException as e:
        error_msg = str(e)
        if "CreateFile" in error_msg or "系统找不到指定的文件" in error_msg:
            logger.error("[FAIL] Container run failed: Docker Desktop is not running")
            logger.info("  → Solution: Start Docker Desktop and try again")
        else:
            logger.error("[FAIL] Container run failed: %s", e)
        return False
    except Exception as e:
        logger.error("[FAIL] Container run failed: %s", e)
        return False


def test_log_collection():
    """測試日志歸集"""
    logger.info("Testing log collection...")
    
    log_dir = "./logs"
    if not os.path.exists(log_dir):
        logger.error("[FAIL] Log directory not found")
        return False
    
    # 檢查日志文件
    log_files = [f for f in os.listdir(log_dir) if f.endswith('.log') or f.endswith('.txt')]
    
    if log_files:
        logger.info("[OK] Found %d log files:", len(log_files))
        for log_file in log_files[:5]:  # 只顯示前5個
            logger.info("  - %s", log_file)
        return True
    else:
        logger.warning("[WARN] No log files found")
        return False


def main():
    """主測試函數"""
    logger.info("=" * 60)
    logger.info("Docker Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Docker Connection", test_docker_connection),
        ("Build Image", build_image),
        ("Container Run", test_container_run),
        ("Log Collection", test_log_collection),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info("\n[%s]", test_name)
        result = test_func()
        results.append((test_name, result))
        time.sleep(1)
    
    # 總結
    logger.info("\n" + "=" * 60)
    logger.info("Test Results Summary")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        logger.info("%s: %s", status, test_name)
    
    logger.info("\nTotal: %d/%d tests passed", passed, total)
    
    # 若 Docker 連線或鏡像構建失敗，才顯示 Docker 服務排查提示（Container Run 可能因命令/鏡像等失敗）
    docker_failed = any(
        name in ["Docker Connection", "Build Image"] and not result
        for name, result in results
    )
    
    if docker_failed:
        logger.info("\n" + "=" * 60)
        logger.info("Docker Service Issue Detected")
        logger.info("=" * 60)
        logger.info("To fix Docker connection issues:")
        logger.info("1. Make sure Docker Desktop is installed")
        logger.info("2. Start Docker Desktop application")
        logger.info("3. Wait for Docker to fully start (whale icon in system tray)")
        logger.info("4. Verify: Open terminal and run 'docker ps'")
        logger.info("5. If still failing, restart Docker Desktop")
        logger.info("=" * 60)
        logger.info("Note: You can still test other features without Docker:")
        logger.info("  → Run 'python quick_test.py' for basic functionality test")
        logger.info("  → Run 'python -m uvicorn app:app' to start API (without Docker tasks)")
    
    if passed == total:
        logger.info("\n[OK] All tests passed!")
        return 0
    else:
        logger.error("\n[FAIL] Some tests failed")
        if not docker_failed:
            logger.info("  → Check error messages above for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
