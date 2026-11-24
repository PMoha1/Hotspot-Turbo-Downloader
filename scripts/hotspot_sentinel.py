#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
         🛡️ UNIVERSAL MIKROTIK HOTSPOT QUOTA SENTINEL 🛡️
=============================================================================
حارس الرصيد التلقائي المتقدم لبوابات شبكات الميكروتك:
- مراقبة دقيقة للرصيد المتبقي بالبايت.
- قاعدة التبديل الذهبية: تسجيل خروج مسبق (/logout) لتفادي رفض الجلسة لنفس الماك.
- التبديل السلس للبطاقات عند 35 MB لمنع الهدر نهائياً.
=============================================================================
"""

import time
import subprocess
import re
import argparse

def get_remaining(ip, gateway, host):
    try:
        cmd = ["curl", "-s", "--connect-timeout", "4", "--interface", ip, "-H", f"Host: {host}", f"http://{gateway}/status"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=6)
        m = re.search(r'data-remaining=[\"\'](\d+)[\"\']', r.stdout)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return None

def login_card(ip, card, gateway, host):
    print(f"[🔄] إنهاء وتسجيل خروج الجلسة السابقة على الواجهة ({ip})...")
    logout_cmd = ["curl", "-s", "--connect-timeout", "4", "--interface", ip, "-H", f"Host: {host}", f"http://{gateway}/logout"]
    subprocess.run(logout_cmd, capture_output=True, text=True, timeout=6)
    time.sleep(2)

    print(f"[🔄] تفعيل البطاقة الجديدة ({ip}): {card}...")
    url = f"http://{gateway}/login?username={card}&password=&domain=speed_very&var=callBack"
    cmd = [
        "curl", "-s", "--interface", ip, "-H", f"Host: {host}",
        "-b", f"hot_speed=speed_very; hot_last_username={card}; hot_auto_relogin=1",
        url
    ]
    subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    time.sleep(4)

def main():
    parser = argparse.ArgumentParser(description="حارس رصيد بوابات الميكروتك التلقائي")
    parser.add_argument("--interface", default="10.2.81.28", help="واجهة الآيبي المرتبطة")
    parser.add_argument("--gateway", default="10.0.0.1", help="عنوان بوابة الميكروتك")
    parser.add_argument("--host", default="a.com", help="نطاق الـ Host للبوابة")
    parser.add_argument("--cards", required=True, help="قائمة البطاقات الاحتياطية مفصولة بفواصل")
    parser.add_argument("--threshold-mb", type=float, default=35.0, help="سقف الرصيد الحرج للتبديل (افتراضي: 35 MB)")
    parser.add_argument("--poll-interval", type=int, default=15, help="فترة الفحص بالثواني (افتراضي: 15s)")
    args = parser.parse_args()

    cards = [c.strip() for c in args.cards.split(",") if c.strip()]
    card_idx = 0

    print(f"[🛡️] حارس الرصيد التلقائي نشط على ({args.interface})...")
    print(f"    - البطاقات المسجلة ({len(cards)}): {cards}")
    print(f"    - سقف التبديل: {args.threshold_mb} MB")

    while True:
        rem_bytes = get_remaining(args.interface, args.gateway, args.host)
        if rem_bytes is not None:
            rem_mb = rem_bytes / (1024 * 1024)
            if rem_mb < args.threshold_mb:
                print(f"[⚠️] رصيد البطاقة الحالية منخفض ({rem_mb:.1f} MB < {args.threshold_mb} MB) -> جاري التبديل...")
                while card_idx + 1 < len(cards):
                    card_idx += 1
                    next_card = cards[card_idx]
                    login_card(args.interface, next_card, args.gateway, args.host)
                    new_rem = get_remaining(args.interface, args.gateway, args.host)
                    if new_rem is not None and (new_rem / (1024 * 1024)) > 100:
                        print(f"[✅] نجح تفعيل البطاقة الجديدة ({next_card}) برصيد: {new_rem / (1024**3):.2f} GiB")
                        break
                    else:
                        print(f"[❌] فشل أو نفد رصيد البطاقة ({next_card})، تجربة التالية...")
        time.sleep(args.poll_interval)

if __name__ == "__main__":
    main()
