from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd

def get_pvpoke_rankings(url, filename, num_rankings):
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
    rankings = driver.find_elements(By.CLASS_NAME, "number")
    names = driver.find_elements(By.CLASS_NAME, "name")
    
    # 轉換數據
    rankings_list = [r.text for r in rankings if r.text.strip()][:num_rankings]  # 只取前x名
    names_list = [n.text.replace("XL", "").split(" ")[0] for n in names if n.text.strip()][:num_rankings]  # 只取前x名
    xl_list = [1 if "XL" in n.text else 0 for n in names if n.text.strip()][:num_rankings]  # 檢查是否含有XL
    
    driver.quit()
    
    # 整理成 DataFrame
    data = pd.DataFrame({"Rank": rankings_list, "Pokemon": names_list, "XL": xl_list})
    
    # 存成 CSV
    data.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"PvPoke 排名數據已更新並存為 {filename}")

def process_pokemon_categories():
    xl_pokemon = set()
    non_xl_pokemon = set()
    
    # 讀取三個 CSV
    for filename in ["pvpoke_1500.csv", "pvpoke_2500.csv", "pvpoke_10000.csv"]:
        df = pd.read_csv(filename)
        xl_pokemon.update(df[df["XL"] == 1]["Pokemon"])
        non_xl_pokemon.update(df[df["XL"] == 0]["Pokemon"])
    
    # 存成 txt
    with open("xl_pokemon.txt", "w", encoding="utf-8-sig") as f:
        f.write(",".join(sorted(xl_pokemon)))
    
    with open("non_xl_pokemon.txt", "w", encoding="utf-8-sig") as f:
        f.write(",".join(sorted(non_xl_pokemon)))
    
    print("XL 與非 XL 寶可夢分類完成，結果存為 xl_pokemon.txt 和 non_xl_pokemon.txt")
    
if __name__ == "__main__":
    # 讓使用者輸入要抓取的前幾名
    num_rankings = int(input("請輸入要抓取的前幾名寶可夢: "))
    urls = {
        "pvpoke_1500.csv": "https://pvpoketw.com/rankings/all/1500/overall/",
        "pvpoke_2500.csv": "https://pvpoketw.com/rankings/all/2500/overall/",
        "pvpoke_10000.csv": "https://pvpoketw.com/rankings/all/10000/overall/"
    }
    
    for filename, url in urls.items():
        get_pvpoke_rankings(url, filename, num_rankings)
    
    process_pokemon_categories()