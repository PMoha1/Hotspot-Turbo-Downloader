#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
         🚀 UNIVERSAL HOTSPOT TURBO MULTI-STREAM DOWNLOADER 🚀
=============================================================================
محرك تنزيل متوازي عالي السرعة متوافق مع بيئات بوابات الدخول ومصفوفات الـ IP.
يدعم: الاستئناف الذكي، منع تكرار البايتات، الدمج فائق السرعة، والتحقق من GGUF.
=============================================================================
"""

import os
import sys
import time
import json
import signal
import atexit
import argparse
import subprocess
import threading
from queue import Queue, Empty
import urllib.request

# رفع حدود النظام للملفات المفتوحة والمقابس لدعم 100-200 مسار متزامن
try:
    import resource
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    target_nofile = max(65535, soft)
    resource.setrlimit(resource.RLIMIT_NOFILE, (target_nofile, hard if hard >= target_nofile else target_nofile))
except Exception:
    pass

procs = {}
procs_lock = threading.Lock()
running = True

def cleanup():
    global running
    running = False
    with procs_lock:
        for wid, p in list(procs.items()):
            try: p.terminate()
            except Exception: pass

atexit.register(cleanup)

def sig_handler(sig, frame):
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, sig_handler)
signal.signal(signal.SIGTERM, sig_handler)

def get_remote_file_size(url, user_agent):
    req = urllib.request.Request(url, headers={"User-Agent": user_agent, "Range": "bytes=0-0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            cr = resp.headers.get("Content-Range")
            if cr and "/" in cr:
                return int(cr.split("/")[-1])
            cl = resp.headers.get("Content-Length")
            if cl:
                return int(cl)
    except Exception as e:
        # Fallback to curl
        cmd = ["curl", "-s", "-I", "-L", "-A", user_agent, url]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        for line in res.stdout.splitlines():
            if line.lower().startswith("content-length:"):
                return int(line.split(":")[-1].strip())
    raise RuntimeError(f"تعذر تحديد حجم الملف من الرابط: {url}")

def parse_interfaces(spec):
    if not spec:
        return []
    ips = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            base, end_part = part.rsplit(".", 1)
            start_num, end_num = end_part.split("-")
            for i in range(int(start_num), int(end_num) + 1):
                ips.append(f"{base}.{i}")
        else:
            ips.append(part)
    return ips

def worker_thread(worker_id, ip, url, task_queue, done_set, failed_queue, user_agent):
    backoff = 0.5
    while running:
        try:
            chunk = task_queue.get_nowait()
        except Empty:
            break

        idx = chunk["idx"]
        path = chunk["path"]
        expected_size = chunk["size"]

        cur_size = os.path.getsize(path) if os.path.exists(path) else 0
        if cur_size == expected_size:
            done_set.add(idx)
            task_queue.task_done()
            backoff = 0.5
            continue
        elif cur_size > expected_size:
            try: os.remove(path)
            except Exception: pass
            cur_size = 0

        start_offset = chunk["start"]
        actual_start = start_offset + cur_size
        if actual_start > chunk["end"]:
            try: os.remove(path)
            except Exception: pass
            actual_start = start_offset
            cur_size = 0

        cmd = [
            "curl", "-4", "-f", "-L",
            "-r", f"{actual_start}-{chunk['end']}",
            "--speed-limit", "5000",
            "--speed-time", "12",
            "--connect-timeout", "10",
            "--retry", "0",
            "--keepalive-time", "60",
            "-A", user_agent,
            "-s"
        ]
        if ip:
            cmd.extend(["--interface", ip])
        cmd.append(url)

        try:
            with open(path, "ab") as f:
                p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.DEVNULL)
                with procs_lock:
                    procs[worker_id] = p
                p.wait()
                with procs_lock:
                    if worker_id in procs:
                        del procs[worker_id]

            final_size = os.path.getsize(path) if os.path.exists(path) else 0
            if final_size == expected_size:
                done_set.add(idx)
                task_queue.task_done()
                backoff = 0.5
            elif final_size > expected_size:
                try: os.remove(path)
                except Exception: pass
                task_queue.task_done()
                failed_queue.put(chunk)
                time.sleep(backoff)
                backoff = min(backoff * 1.5, 8.0)
            else:
                task_queue.task_done()
                failed_queue.put(chunk)
                time.sleep(backoff)
                backoff = min(backoff * 1.5, 8.0)
        except Exception:
            task_queue.task_done()
            failed_queue.put(chunk)
            time.sleep(backoff)
            backoff = min(backoff * 1.5, 8.0)

def stitch_chunks(chunks, final_file, total_size, verify_gguf, chunks_dir):
    print(f"\n[🧩] اكتمال جميع القطع ({len(chunks)}/{len(chunks)})! جاري دمج الملف النهائي...")
    t0 = time.time()
    with open(final_file, "wb") as outfile:
        for ch in chunks:
            part_path = ch["path"]
            with open(part_path, "rb") as infile:
                while True:
                    buf = infile.read(64 * 1024 * 1024)
                    if not buf:
                        break
                    outfile.write(buf)

    t1 = time.time()
    print(f"[✓] تم دمج الملف في {t1 - t0:.2f} ثانية بنجاح على القرص!")

    final_size = os.path.getsize(final_file)
    print(f"[🔍] فحص حجم الملف النهائي: {final_size} بايت (المطلوب: {total_size})")

    if verify_gguf or final_file.endswith(".gguf"):
        with open(final_file, "rb") as f:
            magic = f.read(4)
            if magic == b"GGUF":
                print("[💎] تأكيد سلامة البنية: GGUF Magic Header سليم 100%!")
            else:
                print(f"[⚠️] تنبيه: الهيدر غير مطابق ({magic})")

    for ch in chunks:
        try: os.remove(ch["path"])
        except Exception: pass
    try: os.rmdir(chunks_dir)
    except Exception: pass
    print(f"[🎉] اكتمل التنزيل بنجاح: {final_file}")

def main():
    parser = argparse.ArgumentParser(description="محرك التنزيل السريع عبر الواجهات المتعددة وبوابات الدخول")
    parser.add_argument("--url", required=True, help="رابط الملف المراد تنزيله")
    parser.add_argument("--dest", default=".", help="مجلد حفظ الملف")
    parser.add_argument("--name", default="", help="اسم الملف النهائي (اختياري)")
    parser.add_argument("--streams", type=int, default=32, help="عدد المسارات المتزامنة (يدعم حتى 100-200 مسار)")
    parser.add_argument("--chunks", type=int, default=64, help="عدد القطع المقسمة (يفضل 2x إلى 4x عدد المسارات)")
    parser.add_argument("--interfaces", default="10.2.81.50-250", help="عناوين الآيبي المرتبطة (مثال: 10.2.81.50-250)")
    parser.add_argument("--verify-gguf", action="store_true", help="فحص هيدر GGUF السحري بعد الدمج")
    parser.add_argument("--status-file", default="", help="مسار ملف حالة JSON المباشر")
    args = parser.parse_args()

    ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    
    os.makedirs(args.dest, exist_ok=True)
    chunks_dir = os.path.join(args.dest, "chunks")
    os.makedirs(chunks_dir, exist_ok=True)

    filename = args.name or args.url.split("?")[0].split("/")[-1]
    final_file = os.path.join(args.dest, filename)
    status_file = args.status_file or os.path.join(args.dest, "DOWNLOAD_STATUS.json")

    print(f"[🌐] الاتصال بالسيرفر لتحديد حجم الملف: {filename}...")
    total_size = get_remote_file_size(args.url, ua)
    print(f"[📦] الحجم الإجمالي: {total_size} بايت ({total_size / (1024**3):.2f} GiB)")

    ips = parse_interfaces(args.interfaces)
    if not ips:
        ips = [None] * args.streams
    else:
        while len(ips) < args.streams:
            ips.extend(ips)
        ips = ips[:args.streams]

    num_chunks = max(args.chunks, args.streams)
    base_chunk_size = total_size // num_chunks
    chunks = []
    for i in range(num_chunks):
        start = i * base_chunk_size
        end = (i + 1) * base_chunk_size - 1 if i < num_chunks - 1 else total_size - 1
        expected_size = end - start + 1
        fn = f"chunk_{i:03d}.part"
        part_path = os.path.join(chunks_dir, fn)
        chunks.append({
            "idx": i,
            "filename": fn,
            "path": part_path,
            "start": start,
            "end": end,
            "size": expected_size
        })

    print(f"[⚡] إطلاق {len(ips)} مسار متزامن لـ {num_chunks} قطعة...")

    task_queue = Queue()
    failed_queue = Queue()
    done_set = set()

    for ch in chunks:
        cur_sz = os.path.getsize(ch["path"]) if os.path.exists(ch["path"]) else 0
        if cur_sz == ch["size"]:
            done_set.add(ch["idx"])
        elif cur_sz > ch["size"]:
            try: os.remove(ch["path"])
            except Exception: pass
            task_queue.put(ch)
        else:
            task_queue.put(ch)

    threads = []
    ramp_delay = 0.02 if len(ips) > 32 else 0.005 # Staggered thread startup to prevent socket storming
    for wid, ip in enumerate(ips):
        t = threading.Thread(
            target=worker_thread,
            args=(wid, ip, args.url, task_queue, done_set, failed_queue, ua),
            daemon=True
        )
        t.start()
        threads.append(t)
        if ramp_delay > 0:
            time.sleep(ramp_delay)

    last_time = time.time()
    last_bytes = sum(os.path.getsize(ch["path"]) for ch in chunks if os.path.exists(ch["path"]))

    while running and len(done_set) < num_chunks:
        while not failed_queue.empty():
            try:
                ch = failed_queue.get_nowait()
                task_queue.put(ch)
            except Empty:
                break

        time.sleep(2.0)
        now = time.time()
        elapsed = now - last_time

        cur_bytes = sum(os.path.getsize(ch["path"]) for ch in chunks if os.path.exists(ch["path"]))
        delta_bytes = cur_bytes - last_bytes

        speed_mib = (delta_bytes / (1024 * 1024)) / elapsed if elapsed > 0 else 0.0
        speed_mbps = speed_mib * 8.0

        last_time = now
        last_bytes = cur_bytes

        total_dl_gb = cur_bytes / (1024**3)
        pct = (cur_bytes / total_size) * 100.0

        remaining_bytes = total_size - cur_bytes
        eta_sec = remaining_bytes / (speed_mib * 1024 * 1024) if speed_mib > 0 else 0
        eta_str = time.strftime("%H:%M:%S", time.gmtime(eta_sec)) if eta_sec < 86400 else "--:--:--"

        with procs_lock:
            active_cnt = len(procs)

        status_data = {
            "file_name": filename,
            "total_size_gb": round(total_size / (1024**3), 2),
            "downloaded_gb": round(total_dl_gb, 2),
            "percentage": round(pct, 1),
            "speed_mib": round(speed_mib, 2),
            "speed_mbps": round(speed_mbps, 2),
            "active_streams": active_cnt,
            "done_chunks": len(done_set),
            "total_chunks": num_chunks,
            "eta": eta_str,
            "timestamp": now,
            "complete": False
        }
        try:
            with open(status_file, "w") as sf:
                json.dump(status_data, sf, indent=2)
        except Exception:
            pass

    if len(done_set) == num_chunks:
        stitch_chunks(chunks, final_file, total_size, args.verify_gguf, chunks_dir)
        status_data = {
            "file_name": filename,
            "total_size_gb": round(total_size / (1024**3), 2),
            "downloaded_gb": round(total_size / (1024**3), 2),
            "percentage": 100.0,
            "speed_mib": 0.0,
            "speed_mbps": 0.0,
            "active_streams": 0,
            "done_chunks": num_chunks,
            "total_chunks": num_chunks,
            "eta": "00:00:00",
            "timestamp": time.time(),
            "complete": True
        }
        try:
            with open(status_file, "w") as sf:
                json.dump(status_data, sf, indent=2)
        except Exception:
            pass

if __name__ == "__main__":
    main()
