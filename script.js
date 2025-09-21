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
    const container = document.getElementById('pve_grid');
    if (container.children.length > 0) return; // 已經初始化過
    
    Object.entries(TYPE_CONFIG).forEach(([type, config]) => {
        const rowDiv = document.createElement('div');
        rowDiv.className = 'pve-row';
        rowDiv.innerHTML = `
            <div class="pve-left">
                <div class="pve-info">
                    <div class="pve-type-label">
                        <div class="pve-type-icon" style="background-color: ${config.color}">
                            ${config.icon}
                        </div>
                        <span>${config.name}系 (${type})</span>
                    </div>
                    <div class="pve-input-group">
                        <span>搜尋前</span>
                        <input type="number" class="pve-type-input" id="pve_${type}" value="10" min="1" max="50">
                        <span>名</span>
                    </div>
                </div>
                <div class="pve-buttons">
                    <button class="pve-search-btn" onclick="fetchSingleTypeData('${type}')">
                        🔍 搜尋
                    </button>
                    <button class="pve-copy-btn" id="copy_${type}" onclick="copyPveResult('${type}', this)" disabled>
                        📋 複製
                    </button>
                </div>
            </div>
            <div class="pve-result" id="result_${type}">
                點擊搜尋按鈕載入資料
            </div>
        `;
        container.appendChild(rowDiv);
    });
}

// 複製 PVE 結果的功能
function copyPveResult(type, buttonElement) {
    const resultElement = document.getElementById(`result_${type}`);
    const text = resultElement.textContent.trim();
    
    if (!text || text === '點擊搜尋按鈕載入資料' || text === '載入中...' || text === '無資料' || text === '該屬性暫無資料' || text === '載入失敗，請重試') {
        return; // 不複製無效內容
    }
    
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

// 載入單一屬性資料
async function fetchSingleTypeData(type) {
    const resultDiv = document.getElementById(`result_${type}`);
    const searchBtn = resultDiv.parentElement.querySelector('.pve-search-btn');
    const copyBtn = document.getElementById(`copy_${type}`);
    const inputValue = document.getElementById(`pve_${type}`).value;
    const count = parseInt(inputValue) || 10;
    
    // 顯示載入狀態
    resultDiv.className = 'pve-result loading';
    resultDiv.textContent = '載入中...';
    searchBtn.disabled = true;
    searchBtn.innerHTML = '⏳ 載入中';
    copyBtn.disabled = true;
    
    try {
        // 載入 PVE CSV 資料（如果還沒載入）
        if (!window.pveData) {
            const response = await fetch('https://raw.githubusercontent.com/mikaiyen/PVpokeCrawler/main/data/pve.csv');
            const csvText = await response.text();
            const rows = csvText.trim().split('\n').slice(1); // 移除標題行
            
            // 解析 CSV 資料並存到全域變數
            window.pveData = {};
            rows.forEach(row => {
                const [pokemonType, rank, name] = row.split(',');
                if (!window.pveData[pokemonType]) {
                    window.pveData[pokemonType] = [];
                }
                window.pveData[pokemonType].push({ 
                    rank: parseInt(rank), 
                    name: name.trim() 
                });
            });
        }
        
        // 取得該屬性的前N名Pokemon
        if (window.pveData[type]) {
            const topPokemon = window.pveData[type]
                .sort((a, b) => a.rank - b.rank)
                .slice(0, count)
                .map(p => p.name);
            
            // 去除重複的Pokemon名稱，保持排名順序
            const uniquePokemon = [];
            const seenNames = new Set();
            
            topPokemon.forEach(name => {
                if (!seenNames.has(name)) {
                    seenNames.add(name);
                    uniquePokemon.push(name);
                }
            });
            
            setTimeout(() => {
                resultDiv.className = 'pve-result';
                resultDiv.textContent = uniquePokemon.length > 0 ? uniquePokemon.join(', ') : '無資料';
                searchBtn.disabled = false;
                searchBtn.innerHTML = '🔍 搜尋';
                
                // 啟用複製按鈕（只有在有有效資料時）
                if (uniquePokemon.length > 0) {
                    copyBtn.disabled = false;
                } else {
                    copyBtn.disabled = true;
                }
            }, 300);
        } else {
            setTimeout(() => {
                resultDiv.className = 'pve-result empty';
                resultDiv.textContent = '該屬性暫無資料';
                searchBtn.disabled = false;
                searchBtn.innerHTML = '🔍 搜尋';
                copyBtn.disabled = true;
            }, 300);
        }
        
    } catch (error) {
        console.error(`載入 ${type} 屬性資料失敗:`, error);
        resultDiv.className = 'pve-result empty';
        resultDiv.textContent = '載入失敗，請重試';
        searchBtn.disabled = false;
        searchBtn.innerHTML = '🔍 搜尋';
        copyBtn.disabled = true;
    }
}

// 移除舊的PVE相關函數
// fetchPveData 和 displayPveResults 函數已不需要// 創建背景粒子效果
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
    
    // 綁定 PVP 輸入框的 Enter 鍵事件
    const pvpInputs = ['num1500', 'num2500', 'num10000'];
    pvpInputs.forEach(inputId => {
        document.getElementById(inputId).addEventListener("keypress", function(e) {
            if (e.key === 'Enter') {
                fetchPokemonData();
            }
        });
    });
    
    // 當 PVE 分頁被激活時，綁定輸入框的 Enter 鍵事件
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('tab-btn') && e.target.textContent === 'PVE') {
            setTimeout(() => {
                // 等待 DOM 更新後再綁定事件
                Object.keys(TYPE_CONFIG).forEach(type => {
                    const input = document.getElementById(`pve_${type}`);
                    if (input) {
                        input.addEventListener("keypress", function(e) {
                            if (e.key === 'Enter') {
                                fetchSingleTypeData(type);
                            }
                        });
                    }
                });
            }, 100);
        }
    });
});