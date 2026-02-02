"""
快速驗證腳本
檢查基本功能是否正常
"""
import sys
import os

def test_imports():
    """測試模組導入"""
    print("測試模組導入...")
    try:
        from agent.models import TrainingTask, TaskStatus
        from agent.config import TrainingConfig
        from agent.logger import setup_logger
        from agent.task_queue import add_task, get_task
        print("[OK] 所有模組導入成功")
        # 嘗試導入agent（需要docker）
        try:
            from agent.agent import TrainingAgent
            print("[OK] TrainingAgent導入成功")
        except ImportError as ie:
            print(f"[WARN] TrainingAgent需要docker模組: {ie}")
        return True
    except Exception as e:
        print(f"[ERROR] 模組導入失敗: {e}")
        return False

def test_config():
    """測試配置"""
    print("\n測試配置...")
    try:
        from agent.config import TrainingConfig
        config = TrainingConfig()
        print(f"[OK] 配置創建成功: image={config.image}, epochs={config.epochs}")
        return True
    except Exception as e:
        print(f"[ERROR] 配置測試失敗: {e}")
        return False

def test_models():
    """測試數據模型"""
    print("\n測試數據模型...")
    try:
        from agent.models import TrainingTask, TaskStatus
        task = TrainingTask(
            task_id="test-001",
            epochs=5,
            batch_size=32
        )
        print(f"[OK] 任務模型創建成功: {task.task_id}, status={task.status.value}")
        return True
    except Exception as e:
        print(f"[ERROR] 模型測試失敗: {e}")
        return False

def test_logger():
    """測試日志"""
    print("\n測試日志...")
    try:
        from agent.logger import setup_logger
        logger = setup_logger("TestLogger")
        logger.info("測試日志消息")
        print("[OK] 日志功能正常")
        return True
    except Exception as e:
        print(f"[ERROR] 日志測試失敗: {e}")
        return False

def test_docker_available():
    """測試Docker是否可用"""
    print("\n測試Docker可用性...")
    try:
        import docker
        client = docker.from_env()
        client.ping()
        print("[OK] Docker連接成功")
        return True
    except ImportError:
        print("[WARN] Docker模組未安裝（運行時需要）")
        return True  # 不算錯誤
    except Exception as e:
        print(f"[WARN] Docker不可用: {e}（運行時需要）")
        return True  # 不算錯誤

def main():
    """主函數"""
    print("=" * 60)
    print("快速驗證測試")
    print("=" * 60)
    
    tests = [
        ("模組導入", test_imports),
        ("配置", test_config),
        ("數據模型", test_models),
        ("日志", test_logger),
        ("Docker", test_docker_available),
    ]
    
    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
    
    print("\n" + "=" * 60)
    print("測試結果")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status}: {name}")
    
    print(f"\n總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("\n[SUCCESS] 所有基本測試通過！")
        print("可以運行 'python test_docker.py' 進行完整Docker測試")
        return 0
    else:
        print("\n[ERROR] 部分測試失敗，請檢查錯誤信息")
        return 1

if __name__ == "__main__":
    sys.exit(main())
