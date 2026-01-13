"""
生成更新日誌檔案
記錄更新時間和已更新的檔案列表
"""
import os
import json
from datetime import datetime

def generate_update_log():
    """生成更新日誌到 data/update_log.json"""
    
    # 定義要檢查的檔案
    pvp_files = [
        "data/pvpoke_1500.csv",
        "data/pvpoke_2500.csv", 
        "data/pvpoke_10000.csv"
    ]
    
    pve_files = [
        "data/pve.csv"
    ]
    
    all_files = pvp_files + pve_files
    
    # 檢查哪些檔案存在並記錄
    updated_files = []
    for filepath in all_files:
        if os.path.exists(filepath):
            # 取得檔案修改時間
            mtime = os.path.getmtime(filepath)
            file_time = datetime.fromtimestamp(mtime).isoformat()
            updated_files.append({
                "file": filepath,
                "modified": file_time
            })
    
    # 生成日誌內容
    log_data = {
        "update_time": datetime.now().isoformat(),
        "update_time_readable": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": "local",
        "files": updated_files,
        "summary": {
            "pvp_count": len([f for f in updated_files if "pvpoke" in f["file"]]),
            "pve_count": len([f for f in updated_files if "pve.csv" in f["file"]]),
            "total_count": len(updated_files)
        }
    }
    
    # 確保 data 資料夾存在
    if not os.path.exists("data"):
        os.makedirs("data")
    
    # 寫入 JSON 日誌
    log_path = "data/update_log.json"
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 更新日誌已生成: {log_path}")
    print(f"   更新時間: {log_data['update_time_readable']}")
    print(f"   更新檔案數: {log_data['summary']['total_count']}")
    
    for file_info in updated_files:
        print(f"   - {file_info['file']}")
    
    return log_path

if __name__ == "__main__":
    generate_update_log()
