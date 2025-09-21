// 創建背景粒子效果
function createParticles() {
    const particlesContainer = document.querySelector('.particles');
    const particleCount = 20;

    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 6 + 's';
        particle.style.animationDuration = (Math.random() * 3 + 3) + 's';
        particlesContainer.appendChild(particle);
    }
}

// 主要數據載入函數
async function fetchPokemonData() {
    fetchLastUpdatedTime();
    
    // 獲取三個不同CP級別的數量設定
    const num1500 = document.getElementById("num1500").value;
    const num2500 = document.getElementById("num2500").value;
    const num10000 = document.getElementById("num10000").value;
    
    const fileConfigs = [
        { fileName: "pvpoke_1500.csv", numRankings: num1500, league: "Great League (1500)" },
        { fileName: "pvpoke_2500.csv", numRankings: num2500, league: "Ultra League (2500)" },
        { fileName: "pvpoke_10000.csv", numRankings: num10000, league: "Master League (10000)" }
    ];
    
    const xlPokemon = new Set();
    const nonXlPokemon = new Set();
    const loading = document.getElementById("loading");
    const results = document.getElementById("results");
    const loadBtn = document.getElementById("loadDataBtn");

    // 清空結果
    document.getElementById('xl_pokemon').innerText = "";
    document.getElementById('non_xl_pokemon').innerText = "";

    // 顯示載入動畫
    loading.style.display = "block";
    results.classList.add("hidden");
    results.classList.remove("visible");
    loadBtn.disabled = true;
    loadBtn.innerHTML = '<span>⏳ 載入中...</span>';

    try {
        // 載入並處理每個CSV文件
        for (const config of fileConfigs) {
            console.log(`正在載入 ${config.league}: 前 ${config.numRankings} 名`);
            
            const response = await fetch(`https://raw.githubusercontent.com/mikaiyen/PVpokeCrawler/main/data/${config.fileName}`);
            const csvText = await response.text();
            const rows = csvText.trim().split('\n').slice(1);

            // 根據設定的數量取得對應筆數的資料
            rows.slice(0, parseInt(config.numRankings)).forEach(row => {
                const [name, xl] = row.split(',');
                if (name && name.trim()) {  // 確保有有效的名稱
                    if (xl === '1') {
                        xlPokemon.add(name.trim());
                    } else {
                        nonXlPokemon.add(name.trim());
                    }
                }
            });
        }

        // 動畫顯示結果
        setTimeout(() => {
            const xlArray = Array.from(xlPokemon).sort();
            const nonXlArray = Array.from(nonXlPokemon).sort();
            
            document.getElementById('xl_pokemon').innerText = xlArray.length > 0 ? xlArray.join(', ') : '無資料';
            document.getElementById('non_xl_pokemon').innerText = nonXlArray.length > 0 ? nonXlArray.join(', ') : '無資料';
            
            loading.style.display = "none";
            results.classList.remove("hidden");
            results.classList.add("visible");
            
            loadBtn.disabled = false;
            loadBtn.innerHTML = '<span>🚀 載入資料</span>';
            
            console.log(`載入完成: XL糖果 ${xlArray.length} 隻, 非XL ${nonXlArray.length} 隻`);
        }, 500);

    } catch (error) {
        console.error("無法獲取資料：", error);
        alert("資料載入失敗，請確認網路連接。");
        loading.style.display = "none";
        loadBtn.disabled = false;
        loadBtn.innerHTML = '<span>🚀 載入資料</span>';
    }
}

// 複製到剪貼板函數
function copyToClipboard(elementId, buttonElement) {
    const text = document.getElementById(elementId).innerText;
    navigator.clipboard.writeText(text).then(() => {
        // 複製成功動畫
        const originalText = buttonElement.innerHTML;
        buttonElement.classList.add('copied');
        buttonElement.innerHTML = '✅ 已複製';
        
        setTimeout(() => {
            buttonElement.classList.remove('copied');
            buttonElement.innerHTML = originalText;
        }, 2000);
    }).catch(err => {
        console.error("無法複製文字：", err);
        alert("複製失敗，請手動選取文字複製。");
    });
}

// 獲取最後更新時間
async function fetchLastUpdatedTime() {
    try {
        const response = await fetch("https://api.github.com/repos/mikaiyen/PVpokeCrawler/commits?path=data/pvpoke_1500.csv&page=1&per_page=1");
        const commits = await response.json();
        if (commits && commits[0]) {
            const date = new Date(commits[0].commit.committer.date);
            document.getElementById("last_updated").innerText = "最近更新時間：" + date.toLocaleString('zh-TW');
        }
    } catch (err) {
        console.warn("❗無法取得更新時間", err);
        document.getElementById("last_updated").innerText = "最近更新時間：取得失敗";
    }
}

// 頁面初始化
document.addEventListener('DOMContentLoaded', function() {
    // 創建背景粒子動畫
    createParticles();
    
    // 獲取最後更新時間
    fetchLastUpdatedTime();
    
    // 綁定載入按鈕點擊事件
    document.getElementById("loadDataBtn").addEventListener("click", fetchPokemonData);
    
    // 綁定所有輸入框的 Enter 鍵事件
    const inputs = ['num1500', 'num2500', 'num10000'];
    inputs.forEach(inputId => {
        document.getElementById(inputId).addEventListener("keypress", function(e) {
            if (e.key === 'Enter') {
                fetchPokemonData();
            }
        });
    });
});