from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import os
from datetime import datetime
from git import Repo

# 爬取的網址
URLS = {
    "pvpoke_1500.csv": "https://pvpoketw.com/rankings/all/1500/overall/",
    "pvpoke_2500.csv": "https://pvpoketw.com/rankings/all/2500/overall/",
    "pvpoke_10000.csv": "https://pvpoketw.com/rankings/all/10000/overall/"
}

def setup_driver():
    """設定 Selenium WebDriver"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def get_pvpoke_rankings(url, filename):
    """爬取 PvP 排名資料"""
    driver = setup_driver()
    driver.get(url)
    
    time.sleep(5)  # 等待網頁完全載入
    
    names = driver.find_elements(By.CLASS_NAME, "name")
    
    # 處理資料
    names_list = [n.text.replace("XL", "").split(" ")[0] for n in names if n.text.strip()]
    xl_list = [1 if "XL" in n.text else 0 for n in names if n.text.strip()]
    
    driver.quit()
    
    # 儲存成 CSV 檔案
    data = pd.DataFrame({"Pokemon": names_list, "XL": xl_list})
    data.to_csv("data/"+filename, index=False, encoding="utf-8-sig")
    print(f"{filename} 資料已成功抓取並儲存。")

def main():
    """主程式"""
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = [executor.submit(get_pvpoke_rankings, url, filename) for filename, url in URLS.items()]
        
        for future in results:
            future.result()  # 確保所有爬蟲工作完成
    
    # 推送到 GitHub
    push_to_github()

def push_to_github():
    """將更新的檔案推送到 GitHub"""
    repo = Repo(os.getcwd())
    repo.git.add(['pvpoke_1500.csv', 'pvpoke_2500.csv', 'pvpoke_10000.csv'])
    repo.index.commit(f"自動更新 PvP 資料 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    origin = repo.remote(name='origin')
    origin.push()
    print("已推送更新到 GitHub")

if __name__ == "__main__":
    main()
