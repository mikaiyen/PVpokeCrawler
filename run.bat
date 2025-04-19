@echo off
cd /d E:\Github\PVpokeCrawler

echo [1] do crawler: crawler.py
C:\Users\mikai\anaconda3\envs\py39\python.exe crawler.py

echo [2] Git push update data
git add data\pvpoke_*.csv
git commit -m "auto update PvP data %date% %time%"
git push origin main

echo complete
pause
