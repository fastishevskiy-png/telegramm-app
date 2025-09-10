@echo off
cd /d "C:\Users\fasti\Documents\Cursor\SuperApp"
git remote add origin https://github.com/fastishevskiy-png/telegramm-app.git 2>nul
git branch -M main 2>nul
git push -u origin main
echo Push completed. Check GitHub repository.
