# ==============================================================================
# 🪟 Windows Turbo Network & Power Setup (PowerShell Administrator)
# ==============================================================================
Write-Host "[🌐] إعداد بيئة التنزيل المتوازي على Windows..." -ForegroundColor Cyan

# 1. منع سكون ويندوز عند إغلاق غطاء اللابتوب أثناء التوصيل بالشاحن:
powercfg -setacvalueindex SCHEME_CURRENT SUB_BUTTONS LIDACTION 0
powercfg -setdcvalueindex SCHEME_CURRENT SUB_BUTTONS LIDACTION 0
powercfg -setactive SCHEME_CURRENT
Write-Host "[✓] تم ضبط تصرف غطاء اللابتوب: عدم السكون عند الإغلاق (Do Nothing)." -ForegroundColor Green

# 2. تشغيل التنزيل المتوازي عبر بايثون مباشرة:
# python scripts/turbo_download.py --url "<URL>" --dest "C:\Users\mhmdm\.lmstudio\models\..." --streams 16 --chunks 32
Write-Host "[✓] يمكنك تشغيل محرك التنزيل على ويندوز عبر الأمر:" -ForegroundColor Yellow
Write-Host "python scripts\turbo_download.py --url <URL> --dest <FOLDER> --streams 16 --chunks 32"
