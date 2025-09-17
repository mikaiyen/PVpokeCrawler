from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from datetime import datetime
from git import Repo
import shutil
import threading
import tempfile
from pathlib import Path
import uuid
import psutil
import signal
import sys

# 自動清除壞掉的 .wdm cache
cache_dir = os.path.join(os.path.expanduser("~"), ".wdm")
if os.path.exists(cache_dir):
    shutil.rmtree(cache_dir)
    print("已清除 .wdm cache，等待重新下載乾淨的 driver")

# 定義3個爬蟲任務
CRAWLER_TASKS = [
    {
        "crawler_id": "Crawler-1500",
        "filename": "pvpoke_1500.csv",
        "url": "https://pvpoketw.com/rankings/all/1500/overall/",
        "debug_port": 9222
    },
    {
        "crawler_id": "Crawler-2500", 
        "filename": "pvpoke_2500.csv",
        "url": "https://pvpoketw.com/rankings/all/2500/overall/",
        "debug_port": 9223
    },
    {
        "crawler_id": "Crawler-10000",
        "filename": "pvpoke_10000.csv", 
        "url": "https://pvpoketw.com/rankings/all/10000/overall/",
        "debug_port": 9224
    }
]

# 全域變數和鎖
driver_lock = threading.Lock()
driver_path = None

def signal_handler(sig, frame):
    """處理中斷信號，確保清理資源"""
    print("\n收到中斷信號，正在清理資源...")
    kill_chrome_processes()
    sys.exit(0)

def get_driver_path():
    """線程安全地獲取 ChromeDriver 路徑"""
    global driver_path
    with driver_lock:
        if driver_path is None:
            print("正在下載和安裝 ChromeDriver...")
            driver_path = ChromeDriverManager().install()
            print(f"ChromeDriver 安裝完成: {driver_path}")
            
            # 確保檔案權限正確
            try:
                os.chmod(driver_path, 0o755)
            except Exception as e:
                print(f"設定 ChromeDriver 權限時發生警告: {e}")
        
        return driver_path

def create_unique_user_data_dir(crawler_id):
    """為每個爬蟲創建獨立的用戶資料目錄"""
    temp_dir = tempfile.gettempdir()
    unique_dir = os.path.join(temp_dir, f"chrome_profile_{crawler_id}_{uuid.uuid4().hex[:8]}")
    os.makedirs(unique_dir, exist_ok=True)
    return unique_dir

def setup_driver(crawler_id, debug_port):
    """為指定的爬蟲設定 Selenium WebDriver - 結合舊版本的簡潔性和新版本的穩定性"""
    print(f"[{crawler_id}] 正在初始化 WebDriver...")
    
    # 創建獨立的用戶資料目錄
    user_data_dir = create_unique_user_data_dir(crawler_id)
    
    options = webdriver.ChromeOptions()
    
    # 基本選項 - 保持舊版本的設定
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # 為每個爬蟲指定獨立資源
    options.add_argument(f"--user-data-dir={user_data_dir}")
    options.add_argument(f"--remote-debugging-port={debug_port}")
    
    # 性能優化選項 - 保留JavaScript但優化其他
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    # 移除 --disable-javascript，因為網站需要JS
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--disable-ipc-flooding-protection")
    
    # 記憶體優化 - 使用更保守的設定
    options.add_argument("--memory-pressure-off")
    options.add_argument("--max_old_space_size=2048")
    
    # 新增穩定性選項
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-features=TranslateUI")
    options.add_argument("--disable-default-apps")
    options.add_argument("--no-first-run")
    options.add_argument("--disable-sync")
    
    # 獲取 ChromeDriver 路徑
    chrome_driver_path = get_driver_path()
    
    driver = None
    try:
        service = Service(chrome_driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        
        # 使用舊版本的超時設定
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)
        
        print(f"[{crawler_id}] WebDriver 初始化成功，使用端口: {debug_port}")
        return driver, user_data_dir
        
    except Exception as e:
        print(f"[{crawler_id}] WebDriver 初始化失敗: {e}")
        if driver:
            try:
                driver.quit()
            except:
                pass
        # 清理資源
        try:
            shutil.rmtree(user_data_dir, ignore_errors=True)
        except:
            pass
        raise

def cleanup_crawler_resources(driver, user_data_dir, crawler_id):
    """清理爬蟲相關資源"""
    if driver:
        try:
            driver.quit()
            print(f"[{crawler_id}] WebDriver 已關閉")
        except Exception as e:
            print(f"[{crawler_id}] 關閉 WebDriver 時發生錯誤: {e}")
    
    # 清理臨時目錄
    try:
        shutil.rmtree(user_data_dir, ignore_errors=True)
        print(f"[{crawler_id}] 已清理臨時目錄: {user_data_dir}")
    except Exception as e:
        print(f"[{crawler_id}] 清理臨時目錄時發生錯誤: {e}")

def kill_chrome_processes():
    """只清理爬蟲相關的 Chrome 進程，保留正常使用的 Chrome"""
    try:
        killed_count = 0
        crawler_ports = [9222, 9223, 9224]
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'chrome' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    
                    should_kill = False
                    
                    for port in crawler_ports:
                        if f'--remote-debugging-port={port}' in cmdline:
                            should_kill = True
                            break
                    
                    if '--headless' in cmdline:
                        should_kill = True
                    
                    if 'chrome_profile_Crawler' in cmdline:
                        should_kill = True
                    
                    if should_kill:
                        proc.kill()
                        killed_count += 1
                        print(f"已終止爬蟲 Chrome 進程 PID: {proc.info['pid']}")
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        if killed_count > 0:
            print(f"共終止 {killed_count} 個爬蟲相關的 Chrome 進程")
        else:
            print("沒有找到需要清理的爬蟲 Chrome 進程")
            
    except Exception as e:
        print(f"清理爬蟲 Chrome 進程時發生錯誤: {e}")

def simple_wait_for_elements(driver, crawler_id, max_wait=15):
    """簡單的等待策略 - 結合舊版本的簡潔性和適當的等待"""
    print(f"[{crawler_id}] 等待頁面元素載入...")
    
    # 首先等待基本頁面載入
    time.sleep(3)
    
    # 嘗試找到元素，最多等待 max_wait 秒
    for i in range(max_wait):
        try:
            elements = driver.find_elements(By.CLASS_NAME, "name")
            if elements:
                print(f"[{crawler_id}] 找到 {len(elements)} 個 name 元素")
                return True
            time.sleep(1)
        except Exception as e:
            print(f"[{crawler_id}] 等待時發生錯誤: {e}")
            time.sleep(1)
    
    print(f"[{crawler_id}] 等待超時，但繼續嘗試處理")
    return False

def extract_pokemon_data_simple(driver, crawler_id):
    try:
        name_elements = driver.find_elements(By.CLASS_NAME, "name")
        print(f"[{crawler_id}] 找到 {len(name_elements)} 個 name 元素")

        if not name_elements:
            return [], []

        clean_names = []
        xl_list = []

        for e in name_elements:
            text = e.text.strip()
            html = e.get_attribute("innerHTML")

            if not text:
                continue  # 空的直接跳過

            # 清理名字
            clean_name = text.replace("XL", "").strip().split(" ")[0]
            clean_names.append(clean_name)

            # XL 判斷
            xl_list.append(1 if "xl-info-icon" in html else 0)

        print(f"[{crawler_id}] 成功提取 {len(clean_names)} 個寶可夢資料")
        return clean_names, xl_list

    except Exception as e:
        print(f"[{crawler_id}] 提取資料時發生錯誤: {e}")
        return [], []



def run_crawler(task):
    """運行單個爬蟲任務 - 結合舊版本的簡潔性和新版本的穩定性"""
    crawler_id = task["crawler_id"]
    filename = task["filename"]
    url = task["url"] 
    debug_port = task["debug_port"]
    
    max_retries = 3
    
    for attempt in range(max_retries):
        driver = None
        user_data_dir = None
        
        try:
            print(f"[{crawler_id}] 開始爬取 {filename} (嘗試 {attempt + 1}/{max_retries})")
            
            # 初始化 WebDriver
            driver, user_data_dir = setup_driver(crawler_id, debug_port)
            
            # 載入頁面
            print(f"[{crawler_id}] 正在載入頁面: {url}")
            driver.get(url)
            
            # 使用簡化的等待策略
            simple_wait_for_elements(driver, crawler_id)
            
            # 提取資料
            names_list, xl_list = extract_pokemon_data_simple(driver, crawler_id)
            
            if not names_list:
                print(f"[{crawler_id}] 警告: {filename} 沒有找到任何資料")
                if attempt < max_retries - 1:
                    print(f"[{crawler_id}] 準備重試...")
                    continue
                else:
                    print(f"[{crawler_id}] {filename} 爬取失敗：找不到資料")
                    return False
            
            # 確保資料夾存在
            if not os.path.exists("data"):
                os.makedirs("data")
            
            # 儲存成 CSV 檔案
            data = pd.DataFrame({"Pokemon": names_list, "XL": xl_list})
            data.to_csv(f"data/{filename}", index=False, encoding="utf-8-sig")
            
            # 統計結果
            xl_count = sum(xl_list)
            total_count = len(names_list)
            print(f"[{crawler_id}] ✅ {filename} 資料已成功抓取並儲存")
            print(f"[{crawler_id}] 總計 {total_count} 隻寶可夢，其中 {xl_count} 隻需要XL糖")
            return True
            
        except Exception as e:
            print(f"[{crawler_id}] ❌ 爬取 {filename} 時發生錯誤 (嘗試 {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                print(f"[{crawler_id}] {filename} 爬取失敗，已達最大重試次數")
            else:
                time.sleep(3)  # 等待後重試
        finally:
            # 清理資源
            if driver or user_data_dir:
                cleanup_crawler_resources(driver, user_data_dir, crawler_id)
    
    return False

def main():
    """主程式 - 3個爬蟲並行執行"""
    # 設定信號處理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 60)
    print("啟動 3 個並行爬蟲，每個處理不同的任務")
    print("=" * 60)
    
    # 預先清理可能殘留的 Chrome 進程
    print("清理殘留的 Chrome 進程...")
    kill_chrome_processes()
    
    # 預先安裝 ChromeDriver（避免競爭）
    print("預先準備 ChromeDriver...")
    get_driver_path()
    
    # 顯示任務分配
    print("\n任務分配:")
    for task in CRAWLER_TASKS:
        print(f"  {task['crawler_id']} -> {task['filename']} (端口: {task['debug_port']})")
    
    print(f"\n開始並行執行 {len(CRAWLER_TASKS)} 個爬蟲任務...")
    
    # 使用線程池執行 - 先嘗試3個並行
    with ThreadPoolExecutor(max_workers=3, thread_name_prefix="Crawler") as executor:
        # 提交所有任務
        futures = {
            executor.submit(run_crawler, task): task["crawler_id"] 
            for task in CRAWLER_TASKS
        }
        
        # 等待完成並處理結果
        results = {}
        for future in as_completed(futures):
            crawler_id = futures[future]
            try:
                success = future.result()
                results[crawler_id] = success
                if success:
                    print(f"🎉 {crawler_id} 任務完成")
                else:
                    print(f"⚠️  {crawler_id} 任務失敗")
            except Exception as e:
                print(f"❌ {crawler_id} 執行時發生錯誤: {e}")
                results[crawler_id] = False
    
    # 統計結果
    success_count = sum(results.values())
    total_count = len(CRAWLER_TASKS)
    
    print("\n" + "=" * 60)
    print("爬取結果總覽:")
    for crawler_id, success in results.items():
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"  {crawler_id}: {status}")
    
    print(f"\n總計: {success_count}/{total_count} 個任務成功完成")
    print("=" * 60)
    
    # 最終清理
    print("執行最終清理...")
    time.sleep(2)
    kill_chrome_processes()
    
    # 如果需要推送到 GitHub，取消註解下面這行
    # push_to_github()

def push_to_github():
    """將更新的檔案推送到 GitHub"""
    try:
        repo = Repo(os.getcwd())
        
        # 檢查是否有變更
        if repo.is_dirty() or repo.untracked_files:
            repo.git.add(['data/pvpoke_1500.csv', 'data/pvpoke_2500.csv', 'data/pvpoke_10000.csv'])
            repo.index.commit(f"自動更新 PvP 資料 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            origin = repo.remote(name='origin')
            origin.push()
            print("已推送更新到 GitHub")
        else:
            print("沒有檔案變更，跳過 Git 推送")
            
    except Exception as e:
        print(f"Git 推送時發生錯誤: {e}")

if __name__ == "__main__":
    main()