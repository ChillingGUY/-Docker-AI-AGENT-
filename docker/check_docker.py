"""
Docker環境檢查腳本
快速診斷Docker連接問題
"""
import sys
import subprocess
import platform

def check_docker_installed():
    """檢查Docker是否安裝"""
    print("=" * 60)
    print("檢查1: Docker是否安裝")
    print("=" * 60)
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"[OK] Docker已安裝: {result.stdout.strip()}")
            return True
        else:
            print("[FAIL] Docker未安裝或不在PATH中")
            return False
    except FileNotFoundError:
        print("[FAIL] Docker命令未找到")
        print("  → 請安裝Docker Desktop: https://www.docker.com/products/docker-desktop")
        return False
    except Exception as e:
        print(f"✗ 檢查失敗: {e}")
        return False

def check_docker_running():
    """檢查Docker服務是否運行"""
    print("\n" + "=" * 60)
    print("檢查2: Docker服務是否運行")
    print("=" * 60)
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("[OK] Docker服務正在運行")
            print(f"  輸出: {result.stdout.strip()[:100]}...")
            return True
        else:
            print("[FAIL] Docker服務未運行")
            print(f"  錯誤: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"[ERROR] 無法連接到Docker服務: {e}")
        return False

def check_docker_python_sdk():
    """檢查Docker Python SDK"""
    print("\n" + "=" * 60)
    print("檢查3: Docker Python SDK")
    print("=" * 60)
    try:
        import docker
        print(f"[OK] docker模組已安裝: {docker.__version__}")
        return True
    except ImportError:
        print("[FAIL] docker模組未安裝")
        print("  → 安裝命令: pip install docker")
        return False

def check_docker_connection():
    """檢查Docker連接（使用Python SDK）"""
    print("\n" + "=" * 60)
    print("檢查4: Docker Python SDK連接")
    print("=" * 60)
    try:
        import docker
        client = docker.from_env()
        client.ping()
        print("[OK] Docker Python SDK連接成功")
        return True
    except docker.errors.DockerException as e:
        error_msg = str(e)
        if "CreateFile" in error_msg or "系统找不到指定的文件" in error_msg:
            print("[FAIL] Docker Desktop未啟動")
            print("  → 解決方案:")
            print("    1. 打開Docker Desktop應用程序")
            print("    2. 等待Docker完全啟動（系統托盤顯示Docker圖標）")
            print("    3. 在終端運行 'docker ps' 驗證")
        else:
            print(f"[ERROR] Docker連接失敗: {e}")
        return False
    except ImportError:
        print("[FAIL] docker模組未安裝")
        return False
    except Exception as e:
        print(f"[ERROR] 連接失敗: {e}")
        return False

def check_docker_desktop_process():
    """檢查Docker Desktop進程（Windows）"""
    print("\n" + "=" * 60)
    print("檢查5: Docker Desktop進程（Windows）")
    print("=" * 60)
    if platform.system() != "Windows":
        print("⚠ 此檢查僅適用於Windows系統")
        return None
    
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Docker Desktop.exe"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if "Docker Desktop.exe" in result.stdout:
            print("[OK] Docker Desktop進程正在運行")
            return True
        else:
            print("[FAIL] Docker Desktop進程未運行")
            print("  → 請啟動Docker Desktop應用程序")
            return False
    except Exception as e:
        print(f"✗ 檢查失敗: {e}")
        return None

def provide_solutions():
    """提供解決方案"""
    print("\n" + "=" * 60)
    print("解決方案")
    print("=" * 60)
    print("如果Docker未運行，請按以下步驟操作：")
    print()
    print("1. 安裝Docker Desktop（如果未安裝）")
    print("   下載地址: https://www.docker.com/products/docker-desktop")
    print()
    print("2. 啟動Docker Desktop")
    print("   - 在開始菜單搜索 'Docker Desktop'")
    print("   - 點擊啟動，等待完全啟動")
    print("   - 系統托盤會顯示Docker圖標（鯨魚圖標）")
    print()
    print("3. 驗證Docker運行")
    print("   在PowerShell中運行: docker ps")
    print()
    print("4. 如果仍無法連接")
    print("   - 重啟Docker Desktop")
    print("   - 檢查Windows更新")
    print("   - 查看Docker Desktop日志")
    print()
    print("5. 無Docker環境測試")
    print("   可以運行: python quick_test.py")
    print("   這會測試基本功能（不需要Docker）")

def main():
    """主函數"""
    print("\n" + "=" * 60)
    print("Docker環境診斷工具")
    print("=" * 60)
    print()
    
    results = []
    
    # 執行檢查
    results.append(("Docker安裝", check_docker_installed()))
    results.append(("Docker服務", check_docker_running()))
    results.append(("Python SDK", check_docker_python_sdk()))
    results.append(("SDK連接", check_docker_connection()))
    
    # Windows特定檢查
    if platform.system() == "Windows":
        desktop_check = check_docker_desktop_process()
        if desktop_check is not None:
            results.append(("Docker Desktop進程", desktop_check))
    
    # 總結
    print("\n" + "=" * 60)
    print("診斷結果")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {name}")
    
    print(f"\n通過: {passed}/{total}")
    
    if passed < total:
        provide_solutions()
        return 1
    else:
        print("\n[SUCCESS] 所有檢查通過！Docker環境正常。")
        print("可以運行: python test_docker.py")
        return 0

if __name__ == "__main__":
    sys.exit(main())
