async function fetchPokemonData() {
    fetchLastUpdatedTime();
    const numRankings = document.getElementById("numRankings").value;
    const fileNames = ["pvpoke_1500.csv", "pvpoke_2500.csv", "pvpoke_10000.csv"];
    const xlPokemon = new Set();
    const nonXlPokemon = new Set();
    const loading = document.getElementById("loading");

    document.getElementById('xl_pokemon').innerText = "";
    document.getElementById('non_xl_pokemon').innerText = "";

    loading.style.display = "block";

    for (const fileName of fileNames) {
        try {
            const response = await fetch("https://raw.githubusercontent.com/mikaiyen/PVpokeCrawler/main/data/"+fileName);
            const csvText = await response.text();
            const rows = csvText.trim().split('\n').slice(1);

            rows.slice(0, numRankings).forEach(row => {
                const [name, xl] = row.split(',');
                if (xl === '1') xlPokemon.add(name);
                else nonXlPokemon.add(name);
            });

        } catch (error) {
            console.error("無法獲取資料：", error);
            alert("資料載入失敗，請確認檔案是否存在。");
            loading.style.display = "none";
            return;
        }
    }

    document.getElementById('xl_pokemon').innerText = Array.from(xlPokemon).sort().join(',');
    document.getElementById('non_xl_pokemon').innerText = Array.from(nonXlPokemon).sort().join(',');
    loading.style.display = "none";
}

function copyToClipboard(elementId) {
    const text = document.getElementById(elementId).innerText;
    navigator.clipboard.writeText(text).catch(err => {
        console.error("無法複製文字：", err);
    });
}

async function fetchLastUpdatedTime() {
    try {
        const response = await fetch("https://api.github.com/repos/mikaiyen/PVpokeCrawler/commits?path=data/pvpoke_1500.csv&page=1&per_page=1");
        const commits = await response.json();
        if (commits && commits[0]) {
            const date = new Date(commits[0].commit.committer.date);
            document.getElementById("last_updated").innerText = "最近更新時間：" + date.toLocaleString();
        }
    } catch (err) {
        console.warn("❗無法取得更新時間", err);
        document.getElementById("last_updated").innerText = "最近更新時間：取得失敗";
    }
}


document.getElementById("loadDataBtn").addEventListener("click", fetchPokemonData);
