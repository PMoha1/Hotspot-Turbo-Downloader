#!/usr/bin/env bash
# ==============================================================================
# 🌐 تهيئة شبكة التنزيل المتوازي وعزل المسارات (QoS & Policy Routing)
# يدعم إنشاء مصفوفة IPs فرعية حتى 200 عنوان لدعم 100-200 مسار متزامن
# ==============================================================================
set -e

ETH_DEV="enp3s0"
WIFI_DEV="wlp4s0"
ETH_GW="10.2.81.1"
WIFI_GW="10.4.88.1"
POOL_SIZE="${1:-200}"

echo "[🌐] إعداد جدول التوجيه المنفصل (table 102 للإيثرنت)..."
sudo ip rule add from 10.2.81.0/24 table 102 2>/dev/null || true
sudo ip route replace default via "$ETH_GW" dev "$ETH_DEV" table 102 2>/dev/null || true

echo "[🌐] إعداد جدول التوجيه المنفصل (table 104 للواي فاي)..."
sudo ip rule add from 10.4.88.0/24 table 104 2>/dev/null || true
sudo ip route replace default via "$WIFI_GW" dev "$WIFI_DEV" table 104 2>/dev/null || true

echo "[⚡] إعطاء الأولوية للواي فاي للنظام وتصفح Antigravity (metric 50)..."
sudo ip route replace default via "$WIFI_GW" dev "$WIFI_DEV" metric 50 2>/dev/null || true

START_IP=50
END_IP=$((START_IP + POOL_SIZE - 1))
if [ "$END_IP" -gt 254 ]; then
    END_IP=254
fi

echo "[🚀] إنشاء مصفوفة الـ $POOL_SIZE IP الفرعية على الإيثرنت (10.2.81.$START_IP - 10.2.81.$END_IP)..."
for i in $(seq "$START_IP" "$END_IP"); do
    sudo ip addr add "10.2.81.$i/24" dev "$ETH_DEV" 2>/dev/null || true
done

echo "✅ تم تجهيز وعزل الشبكة وتوليد $((END_IP - START_IP + 1)) عنوان IP بنجاح."
