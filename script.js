// Pokemon 屬性配置
const TYPE_CONFIG = {
    normal: { name: '一般', color: '#A8A878', icon: '🐾' },
    fire: { name: '火', color: '#F08030', icon: '🔥' },
    water: { name: '水', color: '#6890F0', icon: '💧' },
    electric: { name: '電', color: '#F8D030', icon: '⚡' },
    grass: { name: '草', color: '#78C850', icon: '🌿' },
    ice: { name: '冰', color: '#98D8D8', icon: '❄️' },
    fighting: { name: '格鬥', color: '#C03028', icon: '👊' },
    poison: { name: '毒', color: '#A040A0', icon: '☠️' },
    ground: { name: '地面', color: '#E0C068', icon: '🌍' },
    flying: { name: '飛行', color: '#A890F0', icon: '🕊️' },
    psychic: { name: '超能力', color: '#F85888', icon: '🔮' },
    bug: { name: '蟲', color: '#A8B820', icon: '🐛' },
    rock: { name: '岩石', color: '#B8A038', icon: '🗿' },
    ghost: { name: '幽靈', color: '#705898', icon: '👻' },
    dragon: { name: '龍', color: '#7038F8', icon: '🐉' },
    dark: { name: '惡', color: '#705848', icon: '🌑' },
    steel: { name: '鋼', color: '#B8B8D0', icon: '⚔️' },
    fairy: { name: '妖精', color: '#EE99AC', icon: '🧚' }
};

// 分頁切換功能
function showTab(tabName) {
    // 隱藏所有分頁內容
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // 移除所有按鈕的 active 狀態
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // 顯示選中的分頁
    document.getElementById(tabName).classList.add('active');
    
    // 設置對應按鈕為 active
    event.target.classList.add('active');
    
    // 如果是 PVE 分頁，初始化控制項
    if (tabName === 'pve') {
        initializePveControls();
    }
}

// 初始化 PVE 控制項
function initializePveControls() {
    const container = document.querySelector('.type-controls');
    if (container.children.length > 0) return; // 已經初始化過
    
    Object.entries(TYPE_CONFIG).forEach(([type, config]) => {
        const controlItem = document.createElement('div');
        controlItem.className = 'type-control-item';
        controlItem.innerHTML = `
            <div class="type-label">
                <div class="type-icon" style="background-color: ${config.color}">
                    ${config.icon}
                </div>
                <span>${config.name}系 (${type})</span>
            </div>
            <div class="type-input-group">
                <span>前</span>
                <input type="number" class="type-input" id="type_${type}" value="10" min="1" max="50">
                <span>名</span>
            </div>
        `;
        container.appendChild(controlItem);
    });
}

// PVE 數據載入功能
async function fetchPveData() {
    const pveLoading = document.getElementById('pve_loading');
    const pveOutput = document.getElementById('pve_output');
    const loadBtn = document.getElementById('loadPveBtn');
    
    // 顯示載入狀態
    pveLoading.style.display = 'block';
    pveOutput.innerHTML = '';
    loadBtn.disabled = true;
    loadBtn.innerHTML = '<span>⏳ 載入中...</span>';
    
    try {
        // 載入 PVE CSV 資料
        const response = await fetch('https://raw.githubusercontent.com/mikaiyen/PVpokeCrawler/main/data/pve.csv');
        const csvText = await response.text();
        const rows = csvText.trim().split('\n').slice(1); // 移除標題行
        
        // 解析 CSV 資料
        const pveData = {};
        rows.forEach(row => {
            const [type, rank, name] = row.split(',');
            if (!pveData[type]) {
                pveData[type] = [];
            }
            pveData[type].push({ rank: parseInt(rank), name: name.trim() });
        });
        
        // 根據用戶設定生成結果
        const results = [];
        Object.entries(TYPE_CONFIG).forEach(([type, config]) => {
            const inputValue = document.getElementById(`type_${type}`).value;
            const count = parseInt(inputValue) || 10;
            
            if (pveData[type]) {
                const topPokemon = pveData[type]
                    .sort((a, b) => a.rank - b.rank)
                    .slice(0, count)
                    .map(p => p.name);
                
                if (topPokemon.length > 0) {
                    results.push({
                        type: type,
                        config: config,
                        pokemon: topPokemon,
                        count: count
                    });
                }
            }
        });
        
        // 顯示結果
        setTimeout(() => {
            displayPveResults(results);
            pveLoading.style.display = 'none';
            loadBtn.disabled = false;
            loadBtn.innerHTML = '<span>🔍 載入 PVE 資料</span>';
        }, 500);
        
    } catch (error) {
        console.error('載入 PVE 資料失敗:', error);
        alert('PVE 資料載入失敗，請確認網路連接。');
        pveLoading.style.display = 'none';
        loadBtn.disabled = false;
        loadBtn.innerHTML = '<span>🔍 載入 PVE 資料</span>';
    }
}

// 顯示 PVE 結果
function displayPveResults(results) {
    const container = document.getElementById('pve_output');
    container.innerHTML = '';
    
    results.forEach(result => {
        const resultDiv = document.createElement('div');
        resultDiv.className = 'type-result';
        resultDiv.innerHTML = `
            <h4>
                <span class="type-icon" style="background-color: ${result.config.color}">
                    ${result.config.icon}
                </span>
                ${result.config.name}系 - 前 ${result.count} 名
            </h4>
            <div class="type-pokemon-list">${result.pokemon.join(', ')}</div>
        `;
        container.appendChild(resultDiv);
    });
    
    console.log(`PVE 資料載入完成: ${results.length} 個屬性系別`);
}// 創建背景粒子效果
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
    
    // 綁定 PVP 載入按鈕點擊事件
    document.getElementById("loadDataBtn").addEventListener("click", fetchPokemonData);
    
    // 綁定 PVE 載入按鈕點擊事件
    document.getElementById("loadPveBtn").addEventListener("click", fetchPveData);
    
    // 綁定 PVP 輸入框的 Enter 鍵事件
    const pvpInputs = ['num1500', 'num2500', 'num10000'];
    pvpInputs.forEach(inputId => {
        document.getElementById(inputId).addEventListener("keypress", function(e) {
            if (e.key === 'Enter') {
                fetchPokemonData();
            }
        });
    });
    
    // 當 PVE 分頁被激活時，綁定所有屬性輸入框的 Enter 鍵事件
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('tab-btn') && e.target.textContent === 'PVE') {
            setTimeout(() => {
                // 等待 DOM 更新後再綁定事件
                Object.keys(TYPE_CONFIG).forEach(type => {
                    const input = document.getElementById(`type_${type}`);
                    if (input) {
                        input.addEventListener("keypress", function(e) {
                            if (e.key === 'Enter') {
                                fetchPveData();
                            }
                        });
                    }
                });
            }, 100);
        }
    });
});