"""
API測試腳本
測試FastAPI服務的各個端點
"""
import requests
import time
import sys
from agent.logger import setup_logger

logger = setup_logger("APITest")
BASE_URL = "http://localhost:8000"


def test_health():
    """測試健康檢查"""
    logger.info("Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            logger.info(f"✓ Health check passed: {response.json()}")
            return True
        else:
            logger.error(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ Health check error: {e}")
        return False


def test_submit_task():
    """測試提交訓練任務"""
    logger.info("Testing task submission...")
    try:
        response = requests.post(
            f"{BASE_URL}/train",
            json={
                "epochs": 3,
                "batch_size": 16,
                "learning_rate": 0.001
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✓ Task submitted: {data}")
            return data.get("task_id")
        else:
            logger.error(f"✗ Task submission failed: {response.status_code}")
            logger.error(f"  Response: {response.text}")
            return None
    except Exception as e:
        logger.error(f"✗ Task submission error: {e}")
        return None


def test_get_task_status(task_id: str):
    """測試獲取任務狀態"""
    logger.info(f"Testing task status query for {task_id}...")
    try:
        response = requests.get(f"{BASE_URL}/train/{task_id}", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✓ Task status: {data['status']}")
            return data
        else:
            logger.error(f"✗ Task status query failed: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"✗ Task status query error: {e}")
        return None


def test_list_tasks():
    """測試任務列表"""
    logger.info("Testing task list...")
    try:
        response = requests.get(f"{BASE_URL}/train", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✓ Found {data['total']} tasks")
            return True
        else:
            logger.error(f"✗ Task list failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ Task list error: {e}")
        return False


def test_stats():
    """測試統計信息"""
    logger.info("Testing stats...")
    try:
        response = requests.get(f"{BASE_URL}/stats", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✓ Stats: {data}")
            return True
        else:
            logger.error(f"✗ Stats failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ Stats error: {e}")
        return False


def wait_for_task_completion(task_id: str, max_wait: int = 300):
    """等待任務完成"""
    logger.info(f"Waiting for task {task_id} to complete (max {max_wait}s)...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        status_data = test_get_task_status(task_id)
        if status_data:
            status = status_data.get("status")
            if status in ["success", "failed", "cancelled"]:
                logger.info(f"Task completed with status: {status}")
                return status
            logger.info(f"Task status: {status}, waiting...")
        
        time.sleep(5)
    
    logger.warning("Task did not complete within timeout")
    return None


def main():
    """主測試函數"""
    logger.info("=" * 60)
    logger.info("API Test Suite")
    logger.info("=" * 60)
    
    # 等待服務啟動
    logger.info("Waiting for API service to start...")
    time.sleep(3)
    
    tests = [
        ("Health Check", test_health),
        ("Task List", test_list_tasks),
        ("Stats", test_stats),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n[{test_name}]")
        result = test_func()
        results.append((test_name, result))
        time.sleep(1)
    
    # 測試任務提交和狀態查詢
    logger.info("\n[Task Submission and Status]")
    task_id = test_submit_task()
    if task_id:
        results.append(("Task Submission", True))
        
        # 等待任務完成
        logger.info("\n[Waiting for Task Completion]")
        final_status = wait_for_task_completion(task_id)
        if final_status:
            results.append(("Task Completion", True))
        else:
            results.append(("Task Completion", False))
    else:
        results.append(("Task Submission", False))
    
    # 總結
    logger.info("\n" + "=" * 60)
    logger.info("Test Results Summary")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("✓ All tests passed!")
        return 0
    else:
        logger.error("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
