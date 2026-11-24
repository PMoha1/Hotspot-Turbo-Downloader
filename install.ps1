# ==============================================================================
# 🚀 Hotspot-Turbo-Downloader Windows Agent & System Installer
# Developed by PMoha1 (Mohammed Yaqeen)
# ==============================================================================
$ErrorActionPreference = "Stop"

$RepoUrl = "https://github.com/PMoha1/Hotspot-Turbo-Downloader.git"
$InstallDir = "$HOME\.gemini\config\skills\hotspot-turbo-downloader"
$BinDir = "$HOME\.local\bin"

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "⚡ تثبيت أداة ومهارة Hotspot-Turbo-Downloader لأنظمة Windows والوكلاء" -ForegroundColor Yellow
Write-Host "👨‍💻 Developed by PMoha1 | Offensive AI & Network Automation" -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Cyan

if (-not (Test-Path "$HOME\.gemini\config\skills")) {
    New-Item -ItemType Directory -Force -Path "$HOME\.gemini\config\skills" | Out-Null
}

if (Test-Path "$InstallDir\.git") {
    Write-Host "[🔄] تحديث النسخة الحالية للمهارة..." -ForegroundColor Cyan
    Set-Location $InstallDir
    git pull --quiet origin main
} else {
    Write-Host "[📥] استنساخ المستودع..." -ForegroundColor Cyan
    if (Test-Path $InstallDir) { Remove-Item -Recurse -Force $InstallDir }
    git clone --quiet $RepoUrl $InstallDir
}

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "✅ اكتمل التثبيت بنجاح على Windows!" -ForegroundColor Green
Write-Host "📌 الاستخدام عبر بايثون أو الوكيل:" -ForegroundColor White
Write-Host "   python $InstallDir\scripts\turbo_download.py --url <URL>" -ForegroundColor Yellow
Write-Host "==================================================================" -ForegroundColor Cyan
