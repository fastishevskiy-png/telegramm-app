@echo off
title Pushing to GitHub
echo Attempting to push to GitHub...
echo.

cd /d "%~dp0"

echo Adding remote repository...
git remote add origin https://github.com/fastishevskiy-png/telegramm-app.git 2>nul
if %errorlevel% == 0 (
    echo Remote added successfully
) else (
    echo Remote already exists or error occurred
)

echo.
echo Renaming branch to main...
git branch -M main
if %errorlevel% == 0 (
    echo Branch renamed successfully
) else (
    echo Error renaming branch
)

echo.
echo Pushing to GitHub...
git push -u origin main
if %errorlevel% == 0 (
    echo SUCCESS: Code pushed to GitHub!
    echo Check your repository at: https://github.com/fastishevskiy-png/telegramm-app
) else (
    echo ERROR: Failed to push to GitHub
    echo You may need to authenticate with GitHub first
)

echo.
echo Press any key to exit...
pause >nul
