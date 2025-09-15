# 🏆 Pokemon PvP Ranking Crawler & Viewer

一個全自動的 Pokemon PvP 排名數據爬取系統，支持並行爬取多個 CP 級別的排名資料，並提供現代化的網頁介面查看結果。

## 📋 專案概述

本專案包含兩個主要部分：
- **後端爬蟲系統** ：自動化爬取 PvPoke 排名數據
- **前端展示介面** ：美觀的網頁工具用於查看和分析數據

## 🚀 功能特色

### 🔧 後端爬蟲系統
- **並行處理**：同時爬取 3 個 CP 級別 (1500/2500/10000)
- **多線程架構**：每個爬蟲使用獨立的 Chrome 實例
- **智能重試機制**：自動重試失敗的請求，提高穩定性
- **資源管理**：自動清理 Chrome 進程和臨時檔案
- **錯誤處理**：完整的異常處理和日誌系統
- **自動化部署**：支持 GitHub Actions 定期更新

### 🎨 前端展示介面
- **現代化設計**：漸層背景、毛玻璃效果、動畫粒子
- **響應式佈局**：支持桌面和行動裝置
- **即時數據載入**：從 GitHub 獲取最新排名數據
- **智能分類**：自動區分需要/不需要 XL 糖果的 Pokemon
- **一鍵複製**：方便的剪貼板功能
- **更新時間顯示**：透過 GitHub API 顯示資料更新時間

## 🏗️ 系統架構

```
Pokemon-PvP-Crawler/
├── crawler.py              # 主要爬蟲程式
├── data/                   # 爬取的資料目錄
│   ├── pvpoke_1500.csv    # Ultra League 排名
│   ├── pvpoke_2500.csv    # Ultra League 排名  
│   └── pvpoke_10000.csv   # Master League 排名
│                 # 前端網頁介面
├── index.html         # 主頁面
├── style.css          # 樣式檔案
└── script.js          # 功能腳本
```

## 🛠️ 技術棧

### 後端技術
- **Python 3.8+**
- **Selenium WebDriver** - 網頁自動化
- **Pandas** - 數據處理
- **ThreadPoolExecutor** - 並行處理
- **psutil** - 進程管理
- **GitPython** - Git 操作

### 前端技術
- **HTML5 + CSS3 + JavaScript**
- **現代 CSS 特性**：Grid、Flexbox、動畫、漸層
- **Web APIs**：Clipboard API、Fetch API
- **響應式設計**

## 📦 安裝與設置

### 環境需求
```bash
python >= 3.8
pip >= 21.0
Chrome/Chromium 瀏覽器
```

### 安裝步驟

1. **克隆倉庫**
```bash
git clone https://github.com/mikaiyen/PVpokeCrawler.git
cd PVpokeCrawler
```

2. **安裝 Python 依賴**
```bash
selenium>=4.15.0
pandas>=1.5.0
webdriver-manager>=4.0.0
psutil>=5.9.0
GitPython>=3.1.0
```

## 🚀 使用方法

### 運行爬蟲

```bash
python crawler.py
```

爬蟲會自動：
- 初始化 3 個並行爬蟲實例
- 分別爬取 1500、2500、10000 CP 級別排名
- 將數據保存為 CSV 格式到 `data/` 目錄
- 清理所有臨時資源

### 查看前端介面

1. 將 `web/` 目錄下的檔案部署到網頁伺服器
2. 或直接打開 `web/index.html` 在瀏覽器中查看


## 📊 數據格式

### CSV 檔案結構
```csv
Pokemon,XL
Registeel,0
Altaria,1
Azumarill,1
...
```

- **Pokemon**: Pokemon 名稱
- **XL**: 是否需要 XL 糖果 (1=需要, 0=不需要)

### API 端點
- 數據來源：`https://pvpoketw.com/rankings/`
- GitHub Raw 檔案：`https://raw.githubusercontent.com/username/repo/main/data/`

## 🎯 爬蟲架構詳解

### 並行處理設計
```python
# 3個獨立的爬蟲任務
CRAWLER_TASKS = [
    {
        "crawler_id": "Crawler-1500",
        "filename": "pvpoke_1500.csv", 
        "url": "https://pvpoketw.com/rankings/all/1500/overall/",
        "debug_port": 9222
    },
    # ... 更多任務
]
```

### 資源隔離機制
- **獨立 Chrome 實例**：每個爬蟲使用不同的調試端口
- **臨時目錄隔離**：避免用戶資料衝突
- **進程管理**：自動清理殘留的 Chrome 進程

### 錯誤處理策略
- **重試機制**：失敗任務自動重試最多 3 次
- **超時處理**：頁面載入和元素查找設置合理超時
- **資源清理**：異常發生時確保清理所有資源

## 🎨 前端設計亮點

### 視覺效果
- **漸層背景**：現代化的藍紫色漸層
- **毛玻璃效果**：使用 `backdrop-filter` 實現
- **浮動粒子**：JavaScript 生成的背景動畫
- **微互動**：按鈕懸停、載入動畫、複製反饋

### 用戶體驗
- **即時反饋**：載入狀態、複製成功提示
- **鍵盤支持**：Enter 鍵快速搜索
- **響應式設計**：適配各種螢幕尺寸
- **無障礙設計**：適當的對比度和語義標記

## 🔧 配置選項

### 爬蟲設定
```python
# Chrome 選項優化
options.add_argument("--headless=new")      # 無界面模式
options.add_argument("--disable-images")    # 禁用圖片載入
options.add_argument("--disable-javascript") # 禁用 JS（提升速度）
options.add_argument("--memory-pressure-off") # 記憶體優化
```

### 效能調整
- **並行數量**：預設 3 個工作線程
- **重試次數**：預設 3 次重試
- **超時設定**：頁面載入 30 秒，元素查找 10 秒

## 📈 監控與日誌

### 執行日誌範例
```
[Crawler-1500] 正在初始化 WebDriver...
[Crawler-2500] WebDriver 初始化成功，使用端口: 9223  
[Crawler-10000] ✅ pvpoke_10000.csv 資料已成功抓取 (共 245 筆資料)
總計: 3/3 個任務成功完成
```

### 錯誤追蹤
- 詳細的異常日誌記錄
- 每個爬蟲的獨立狀態追蹤
- 資源使用情況監控

## 🙋‍♂️ 常見問題

### Q: 爬蟲執行失敗怎麼辦？
A: 檢查網路連接和目標網站是否可訪問，爬蟲會自動重試 3 次。

### Q: 如何修改爬取頻率？
A: 編輯 `.github/workflows/crawler.yml` 中的 cron 表達式。

### Q: 前端無法載入數據？
A: 確認 GitHub Pages 已啟用，且 CSV 檔案已正確生成。

## 🌐 網頁展示

https://mikaiyen.github.io/PVpokeCrawler/

---

⭐ 如果這個專案對您有幫助，請給個 Star 支持一下！
