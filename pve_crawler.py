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

# 自動清除壞掉的 .wdm cache
cache_dir = os.path.join(os.path.expanduser("~"), ".wdm")
if os.path.exists(cache_dir):
    shutil.rmtree(cache_dir)
    print("已清除 .wdm cache，等待重新下載乾淨的 driver")

# 定義所有屬性爬蟲任務
POKEMON_TYPES = ["normal", "fire", "water", "electric", "grass", "ice", "fighting", 
                "poison", "ground", "flying", "psychic", "bug", "rock", "ghost", 
                "dragon", "dark", "steel", "fairy"]

# 生成爬蟲任務列表
CRAWLER_TASKS = []
for i, ptype in enumerate(POKEMON_TYPES):
    CRAWLER_TASKS.append({
        "crawler_id": f"Crawler-{ptype}",
        "filename": f"{ptype}.csv",
        "url": f"https://db.pokemongohub.net/pokemon-list/best-per-type/{ptype}",
        "debug_port": 9222 + i,  # 每個爬蟲使用不同端口
        "type": ptype
    })

# 全域變數和鎖
driver_lock = threading.Lock()
driver_path = None

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
    """為指定的爬蟲設定 Selenium WebDriver"""
    print(f"[{crawler_id}] 正在初始化 WebDriver...")
    
    # 創建獨立的用戶資料目錄
    user_data_dir = create_unique_user_data_dir(crawler_id)
    
    options = webdriver.ChromeOptions()
    
    # 基本選項
    options.add_argument("--headless=new")  # 使用新的 headless 模式
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    
    # 為每個爬蟲指定獨立資源
    options.add_argument(f"--user-data-dir={user_data_dir}")
    options.add_argument(f"--remote-debugging-port={debug_port}")
    
    # 性能優化選項
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-ipc-flooding-protection")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # 記憶體優化
    options.add_argument("--memory-pressure-off")
    options.add_argument("--max_old_space_size=4096")
    
    # 獲取 ChromeDriver 路徑
    chrome_driver_path = get_driver_path()
    
    driver = None
    try:
        service = Service(chrome_driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(60)
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
    """清理殘留的 Chrome 進程"""
    try:
        killed_count = 0
        for proc in psutil.process_iter(['pid', 'name']):
            if 'chrome' in proc.info['name'].lower():
                try:
                    proc.kill()
                    killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        if killed_count > 0:
            print(f"已終止 {killed_count} 個 Chrome 進程")
    except Exception as e:
        print(f"清理 Chrome 進程時發生錯誤: {e}")

def run_crawler(task):
    """運行單個爬蟲任務"""
    crawler_id = task["crawler_id"]
    filename = task["filename"]
    url = task["url"] 
    debug_port = task["debug_port"]
    ptype = task["type"]
    
    max_retries = 3
    
    for attempt in range(max_retries):
        driver = None
        user_data_dir = None
        
        try:
            print(f"[{crawler_id}] 開始爬取 {ptype} 屬性資料 (嘗試 {attempt + 1}/{max_retries})")
            
            # 初始化 WebDriver
            driver, user_data_dir = setup_driver(crawler_id, debug_port)
            
            # 載入頁面
            print(f"[{crawler_id}] 正在載入頁面: {url}")
            driver.get(url)
            time.sleep(5)  # 額外等待時間
            
            # 1️⃣ 嘗試多種 selector，找到頁面主要內容
            print(f"[{crawler_id}] 等待頁面內容載入...")
            try:
                # 先嘗試原本的選擇器
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//div[contains(@class,"layout_layout__")]')
                    )
                )
                print(f"[{crawler_id}] 找到 layout 元素")
            except:
                print(f"[{crawler_id}] 找不到 layout，嘗試其他選擇器...")
                # 嘗試其他可能的選擇器
                try:
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located(
                            (By.TAG_NAME, "main")
                        )
                    )
                    print(f"[{crawler_id}] 找到 main 元素")
                except:
                    print(f"[{crawler_id}] 嘗試等待 body 載入完成...")
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located(
                            (By.TAG_NAME, "body")
                        )
                    )
                    time.sleep(3)  # 額外等待時間

            # 2️⃣ 如果有 cookie 彈窗，先關掉
            try:
                cookie_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[contains(text(),"Accept")]'))
                )
                cookie_btn.click()
                print(f"[{crawler_id}] 已點擊 Accept cookies")
                time.sleep(1)
            except:
                print(f"[{crawler_id}] 沒有找到 cookie 彈窗")

            # 3️⃣ 等結果區塊載入，嘗試多種選擇器
            print(f"[{crawler_id}] 尋找結果區塊...")
            results = None
            
            # 嘗試不同的選擇器
            selectors = [
                '//div[contains(@class,"PokemonCounters_results__")]',
                '//div[contains(@class,"results")]',
                '//div[contains(@class, "pokemon")]',
                '//main//div',
                '//div[@class]'
            ]
            
            for selector in selectors:
                try:
                    results = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    print(f"[{crawler_id}] 找到結果區塊: {selector}")
                    break
                except:
                    continue
            
            if results is None:
                print(f"[{crawler_id}] 所有選擇器都失敗，嘗試直接從整個頁面抓取...")
                results = driver.find_element(By.TAG_NAME, "body")

            # 4️⃣ 抓取寶可夢名稱，嘗試多種方式
            print(f"[{crawler_id}] 抓取寶可夢名稱...")
            names = []
            
            # 方法1: 原本的方式
            try:
                name_elems = results.find_elements(By.XPATH, './/a[contains(@href,"/pokemon/")]')
                names = [e.text.strip() for e in name_elems if e.text.strip()]
                print(f"[{crawler_id}] 方法1找到 {len(names)} 個名稱")
            except:
                print(f"[{crawler_id}] 方法1失敗")
            
            # 方法2: 如果方法1沒找到，嘗試其他選擇器
            if len(names) == 0:
                try:
                    name_elems = driver.find_elements(By.XPATH, '//a[contains(@href,"pokemon")]')
                    names = [e.text.strip() for e in name_elems if e.text.strip()]
                    print(f"[{crawler_id}] 方法2找到 {len(names)} 個名稱")
                except:
                    print(f"[{crawler_id}] 方法2失敗")
            
            # 方法3: 更廣泛的搜尋
            if len(names) == 0:
                try:
                    # 嘗試找任何包含pokemon的連結
                    name_elems = driver.find_elements(By.PARTIAL_LINK_TEXT, "")
                    all_links = [e.get_attribute('href') for e in name_elems if e.get_attribute('href')]
                    pokemon_links = [link for link in all_links if 'pokemon' in link.lower()]
                    print(f"[{crawler_id}] 找到 {len(pokemon_links)} 個包含pokemon的連結")
                    
                    if len(pokemon_links) > 0:
                        # 從連結中提取寶可夢名稱
                        for link in pokemon_links[:50]:  # 限制50個
                            try:
                                # 從URL中提取寶可夢名稱
                                name = link.split('/')[-1].replace('-', ' ').title()
                                if name:
                                    names.append(name)
                            except:
                                continue
                        print(f"[{crawler_id}] 從連結提取到 {len(names)} 個名稱")
                        
                except Exception as e:
                    print(f"[{crawler_id}] 方法3失敗: {e}")

            # 取前50個結果
            names = names[:50] if names else []
            
            if not names:
                print(f"[{crawler_id}] 警告: {ptype} 屬性沒有找到任何資料")
                if attempt < max_retries - 1:
                    continue
                else:
                    print(f"[{crawler_id}] {ptype} 屬性爬取失敗：找不到資料")
                    return False
            
            # 確保資料夾存在
            if not os.path.exists("pve"):
                os.makedirs("pve")
            
            # 儲存成 CSV 檔案
            data = pd.DataFrame({"rank": range(1, len(names) + 1), "name": names})
            data.to_csv(f"pve/{filename}", index=False, encoding="utf-8-sig")
            print(f"[{crawler_id}] ✅ {ptype} 屬性資料已成功抓取並儲存 (共 {len(names)} 筆資料)")
            return True
            
        except Exception as e:
            print(f"[{crawler_id}] ❌ 爬取 {ptype} 屬性時發生錯誤 (嘗試 {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                print(f"[{crawler_id}] {ptype} 屬性爬取失敗，已達最大重試次數")
            else:
                time.sleep(3)  # 等待後重試
        finally:
            # 清理資源
            if driver or user_data_dir:
                cleanup_crawler_resources(driver, user_data_dir, crawler_id)
    
    return False

def main():
    """主程式 - 多個爬蟲並行執行"""
    print("=" * 80)
    print(f"啟動 {len(POKEMON_TYPES)} 個並行爬蟲，爬取所有寶可夢屬性的PVE資料")
    print("=" * 80)
    
    # 預先清理可能殘留的 Chrome 進程
    print("清理殘留的 Chrome 進程...")
    kill_chrome_processes()
    
    # 預先安裝 ChromeDriver（避免競爭）
    print("預先準備 ChromeDriver...")
    get_driver_path()
    
    # 顯示任務分配
    print("\n任務分配:")
    for i, task in enumerate(CRAWLER_TASKS):
        print(f"  {task['crawler_id']} -> {task['type']} 屬性 (端口: {task['debug_port']})")
        if (i + 1) % 3 == 0:  # 每3個換行
            print()
    
    print(f"\n開始並行執行 {len(CRAWLER_TASKS)} 個爬蟲任務...")
    
    # 使用線程池執行，每個線程處理一個任務
    # 限制同時執行的線程數量，避免資源不足
    max_workers = min(6, len(CRAWLER_TASKS))  # 最多6個同時執行
    
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="PVE-Crawler") as executor:
        # 提交所有任務
        futures = {
            executor.submit(run_crawler, task): task["crawler_id"] 
            for task in CRAWLER_TASKS
        }
        
        # 等待完成並處理結果
        results = {}
        completed_count = 0
        
        for future in as_completed(futures):
            crawler_id = futures[future]
            try:
                success = future.result()
                results[crawler_id] = success
                completed_count += 1
                
                if success:
                    print(f"🎉 {crawler_id} 任務完成 ({completed_count}/{len(CRAWLER_TASKS)})")
                else:
                    print(f"⚠️  {crawler_id} 任務失敗 ({completed_count}/{len(CRAWLER_TASKS)})")
            except Exception as e:
                print(f"❌ {crawler_id} 執行時發生錯誤: {e}")
                results[crawler_id] = False
                completed_count += 1
    
    # 統計結果
    success_count = sum(results.values())
    total_count = len(CRAWLER_TASKS)
    
    print("\n" + "=" * 80)
    print("爬取結果總覽:")
    
    # 按屬性分組顯示結果
    for i, (crawler_id, success) in enumerate(results.items()):
        ptype = crawler_id.replace("Crawler-", "")
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"  {ptype.ljust(10)}: {status}")
        if (i + 1) % 6 == 0:  # 每6個換行
            print()
    
    print(f"\n總計: {success_count}/{total_count} 個屬性成功完成")
    print(f"成功率: {success_count/total_count*100:.1f}%")
    print("=" * 80)
    
    # 最終清理
    print("執行最終清理...")
    time.sleep(2)
    kill_chrome_processes()
    
    # 可選：推送到 GitHub
    # push_to_github()

def push_to_github():
    """將更新的檔案推送到 GitHub"""
    try:
        repo = Repo(os.getcwd())
        
        # 檢查是否有變更
        if repo.is_dirty() or repo.untracked_files:
            # 添加所有 pve 資料夾下的 CSV 檔案
            pve_files = [f"pve/{ptype}.csv" for ptype in POKEMON_TYPES]
            repo.git.add(pve_files)
            repo.index.commit(f"自動更新 PVE 屬性資料 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            origin = repo.remote(name='origin')
            origin.push()
            print("已推送更新到 GitHub")
        else:
            print("沒有檔案變更，跳過 Git 推送")
            
    except Exception as e:
        print(f"Git 推送時發生錯誤: {e}")

if __name__ == "__main__":
    main()