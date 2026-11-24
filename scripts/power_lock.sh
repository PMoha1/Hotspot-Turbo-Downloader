#!/usr/bin/env bash
# ==============================================================================
# 🔒 مانع السكون وإغلاق غطاء اللابتوب (Lid-Close Sleep Lock)
# ==============================================================================
echo "[🔒] تفعيل حظر السكون وإغلاق الغطاء للعمل المستمر طوال الليل..."
exec systemd-inhibit \
    --what=sleep:shutdown:idle:handle-lid-switch \
    --who="SecurityCore" \
    --why="High-Throughput Overnight Model Download" \
    sleep infinity
