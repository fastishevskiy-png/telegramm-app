# PowerShell script to push to GitHub
Write-Host "Starting GitHub push process..." -ForegroundColor Green

# Check if we're in a git repository
if (!(Test-Path ".git")) {
    Write-Host "Error: Not in a git repository" -ForegroundColor Red
    exit 1
}

# Add remote if not exists
try {
    $remotes = git remote
    if ($remotes -notcontains "origin") {
        Write-Host "Adding GitHub remote..." -ForegroundColor Yellow
        git remote add origin https://github.com/fastishevskiy-png/telegramm-app.git
    } else {
        Write-Host "Remote origin already exists" -ForegroundColor Green
    }
} catch {
    Write-Host "Error adding remote: $_" -ForegroundColor Red
}

# Rename branch to main
try {
    Write-Host "Renaming branch to main..." -ForegroundColor Yellow
    git branch -M main
} catch {
    Write-Host "Error renaming branch: $_" -ForegroundColor Red
}

# Push to GitHub
try {
    Write-Host "Pushing to GitHub..." -ForegroundColor Yellow
    git push -u origin main
    Write-Host "Successfully pushed to GitHub!" -ForegroundColor Green
} catch {
    Write-Host "Error pushing to GitHub: $_" -ForegroundColor Red
    Write-Host "You might need to authenticate with GitHub first" -ForegroundColor Yellow
}

Write-Host "Check your repository at: https://github.com/fastishevskiy-png/telegramm-app" -ForegroundColor Cyan
