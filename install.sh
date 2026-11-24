#!/usr/bin/env bash
# ==============================================================================
# 🚀 Hotspot-Turbo-Downloader Universal Agent & System Installer
# Developed by PMoha1 (Mohammed Yaqeen)
# ==============================================================================
set -e

REPO_URL="https://github.com/PMoha1/Hotspot-Turbo-Downloader.git"
INSTALL_DIR="$HOME/.gemini/config/skills/hotspot-turbo-downloader"
BIN_DIR="$HOME/.local/bin"

echo "=================================================================="
echo "⚡ تثبيت أداة ومهارة Hotspot-Turbo-Downloader لوكلاء الذكاء الاصطناعي"
echo "👨‍💻 Developed by PMoha1 | Offensive AI & Network Automation"
echo "=================================================================="

mkdir -p "$BIN_DIR"
mkdir -p "$HOME/.gemini/config/skills"

if [ -d "$INSTALL_DIR/.git" ]; then
    echo "[🔄] تحديث النسخة الحالية للمهارة..."
    cd "$INSTALL_DIR" && git pull --quiet origin main
else
    echo "[📥] استنساخ المستودع إلى مجلد مهارات الوكلاء..."
    rm -rf "$INSTALL_DIR"
    git clone --quiet "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"
chmod +x scripts/* bin/* 2>/dev/null || true

# ربط الأوامر المباشرة في مسار النظام التنفيذي
echo "[🔗] إنشاء الروابط التنفيذية السريعة في $BIN_DIR..."
ln -sf "$INSTALL_DIR/bin/fast-download" "$BIN_DIR/fast-download"
ln -sf "$INSTALL_DIR/bin/hotspot-sentinel" "$BIN_DIR/hotspot-sentinel"
ln -sf "$INSTALL_DIR/bin/fast-download" "$BIN_DIR/turbo-download"

# فحص بيئة الوكلاء الإضافية وتثبيت المهارة فيها تلقائياً (Claude / Hermes)
if [ -d "$HOME/.hermes" ]; then
    mkdir -p "$HOME/.hermes/skills"
    ln -sfn "$INSTALL_DIR" "$HOME/.hermes/skills/hotspot-turbo-downloader"
    echo "[✓] تم ربط المهارة بنجاح مع منظومة Hermes Agent!"
fi

if [ -d "$HOME/.claude" ]; then
    mkdir -p "$HOME/.claude/skills"
    ln -sfn "$INSTALL_DIR" "$HOME/.claude/skills/hotspot-turbo-downloader"
    echo "[✓] تم ربط المهارة بنجاح مع منظومة Claude Agent!"
fi

echo "=================================================================="
echo "✅ اكتمل التثبيت بنجاح!"
echo "📌 الاستخدام المباشر في الطرفية أو عبر أي وكيل ذكاء اصطناعي:"
echo "   fast-download <URL>"
echo "   أو أمر الوكيل المباشر: /fast <URL>"
echo "=================================================================="
