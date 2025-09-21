@echo off
cd /d E:\Github\PVpokeCrawler

echo [1] do crawler: crawler.py
C:\Users\mikai\anaconda3\envs\py39\python.exe crawler.py

echo [2] do crawler: pve_crawler.py
C:\Users\mikai\anaconda3\envs\py39\python.exe pve_crawler.py

echo [3] Git push update data
git add data
git commit -m "auto update data %date% %time%"
git push origin main

echo complete
pause
