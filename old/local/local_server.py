from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
CORS(app)  # 允許跨域請求

# 目標網址
URLS = {
    "Super": "https://pvpoketw.com/rankings/all/1500/overall/",
    "Ultra": "https://pvpoketw.com/rankings/all/2500/overall/",
    "Master": "https://pvpoketw.com/rankings/all/10000/overall/"
}

def setup_driver():
    """設置 Selenium WebDriver"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 無頭模式
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def get_pvpoke_rankings(url, num_rankings):
    """爬取單一網址的 PvP 排名數據"""
    driver = setup_driver()
    driver.get(url)
    
    time.sleep(3)  # 減少等待時間，提高讀取速度
    
    # 抓取寶可夢名稱
    names = driver.find_elements(By.CLASS_NAME, "name")
    
    # 處理數據
    names_list = [n.text.replace("XL", "").split(" ")[0] for n in names if n.text.strip()][:num_rankings]
    xl_list = [1 if "XL" in n.text else 0 for n in names if n.text.strip()][:num_rankings]
    
    driver.quit()
    
    return pd.DataFrame({"Pokemon": names_list, "XL": xl_list})

@app.route('/run_scraper', methods=['GET'])
def run_scraper():
    """並行爬取 3 個網址，加速處理"""
    num_rankings = int(request.args.get('numRankings', 50))
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(lambda url: get_pvpoke_rankings(url, num_rankings), URLS.values()))
    
    # 合併所有 DataFrame
    df = pd.concat(results, ignore_index=True)

    # 分類 XL 和非 XL
    xl_pokemon = sorted(set(df[df["XL"] == 1]["Pokemon"]))
    non_xl_pokemon = sorted(set(df[df["XL"] == 0]["Pokemon"]))

    return jsonify({
        "xl_pokemon": ",".join(xl_pokemon),
        "non_xl_pokemon": ",".join(non_xl_pokemon)
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
