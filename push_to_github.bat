@echo off
echo Pushing to GitHub repository...

REM Add remote repository
git remote add origin https://github.com/fastishevskiy-png/telegramm-app.git

REM Rename branch to main
git branch -M main

REM Push to GitHub
git push -u origin main

echo Done! Check your GitHub repository.
pause
