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
    const numRankings = document.getElementById("numRankings").value;
    const fileNames = ["pvpoke_1500.csv", "pvpoke_2500.csv", "pvpoke_10000.csv"];
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
        for (const fileName of fileNames) {
            const response = await fetch("https://raw.githubusercontent.com/mikaiyen/PVpokeCrawler/main/data/"+fileName);
            const csvText = await response.text();
            const rows = csvText.trim().split('\n').slice(1);

            rows.slice(0, numRankings).forEach(row => {
                const [name, xl] = row.split(',');
                if (xl === '1') xlPokemon.add(name);
                else nonXlPokemon.add(name);
            });
        }

        // 動畫顯示結果
        setTimeout(() => {
            document.getElementById('xl_pokemon').innerText = Array.from(xlPokemon).sort().join(', ');
            document.getElementById('non_xl_pokemon').innerText = Array.from(nonXlPokemon).sort().join(', ');
            
            loading.style.display = "none";
            results.classList.remove("hidden");
            results.classList.add("visible");
            
            loadBtn.disabled = false;
            loadBtn.innerHTML = '<span>🚀 載入資料</span>';
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
    
    // 綁定輸入框 Enter 鍵事件
    document.getElementById("numRankings").addEventListener("keypress", function(e) {
        if (e.key === 'Enter') {
            fetchPokemonData();
        }
    });
});