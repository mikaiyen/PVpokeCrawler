from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允許所有前端存取 API


def get_pvpoke_rankings(url, num_rankings):
    # 設置 Selenium
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 無頭模式
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    # 啟動 WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    
    time.sleep(5)  # 等待 JavaScript 加載完成
    
    # 抓取數據
    names = driver.find_elements(By.CLASS_NAME, "name")
    
    # 轉換數據
    names_list = [n.text.replace("XL", "").split(" ")[0] for n in names if n.text.strip()][:num_rankings]
    xl_list = [1 if "XL" in n.text else 0 for n in names if n.text.strip()][:num_rankings]

    driver.quit()
    
    # 整理成 DataFrame
    data = pd.DataFrame({"Pokemon": names_list, "XL": xl_list})
    
    return data

@app.route('/run_scraper', methods=['GET'])
def run_scraper():
    # 取得使用者輸入的數量（預設 50）
    num_rankings = int(request.args.get('numRankings', 50))
    
    urls = {
        "Super": "https://pvpoketw.com/rankings/all/1500/overall/",
        "Ultra": "https://pvpoketw.com/rankings/all/2500/overall/",
        "Master": "https://pvpoketw.com/rankings/all/10000/overall/"
    }

    df = pd.DataFrame()
    
    for league, url in urls.items():
        dftemp = get_pvpoke_rankings(url, num_rankings)
        df = pd.concat([df, dftemp], ignore_index=True)

    # 分類 XL 和非 XL
    xl_pokemon = sorted(set(df[df["XL"] == 1]["Pokemon"]))
    non_xl_pokemon = sorted(set(df[df["XL"] == 0]["Pokemon"]))

    # 回傳 JSON 給前端
    return jsonify({
        "xl_pokemon": ", ".join(xl_pokemon),
        "non_xl_pokemon": ", ".join(non_xl_pokemon)
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
