---
name: hotspot-turbo-downloader
description: >
  Autonomous ultra-fast multi-stream downloader, Mikrotik Hotspot captive portal manager, and high-throughput quota sentinel. Trigger whenever the user asks for fast downloading, "مهارت التنزيل السريع", /fast, "التنزيل السريع", "تنزيل توربو", multi-stream range fetching, or downloading large AI models/weights across captive portals without data waste or sleep interruption.
---

# 🚀 مهام وأدوات التنزيل السريع وإدارة بوابات الدخول (Hotspot Turbo Downloader)

## 📌 الكلمات المفتاحية ومحفزات التفعيل (Triggers)
يتم استدعاء هذه المهارة تلقائياً بمجرد طلب:
- `مهارت التنزيل السريع` أو `التنزيل السريع` أو `تنزيل توربو`
- الأمر المباشر: `/fast <URL> [DEST]`
- تنزيل نماذج ذكاء اصطناعي ضخمة (LLM GGUF / SafeTensors) عبر شبكات الميكروتك وبوابات الدخول (Hotspot / Captive Portal).

---

## 🛠️ البنية التشغيلية والسكربتات الجاهزة (Production Scripts)

تضم المهارة حزمة متكاملة من السكربتات الميدانية الجاهزة للتنفيذ الفوري داخل مجلد `scripts/`:

| السكربت | الوظيفة | أمر التشغيل السريع |
|---|---|---|
| **`scripts/turbo_download.py`** | محرك التنزيل المتوازي السريع (32 مسار) مع الاستئناف الذكي ومنع التكرار والدمج الآلي وفحص GGUF | `python3 scripts/turbo_download.py --url "<URL>" --dest "<DIR>"` |
| **`scripts/hotspot_sentinel.py`** | حارس رصيد الميكروتك (يراقب بالبايت وينفذ `/logout` ثم `/login` عند 35 MB) | `python3 scripts/hotspot_sentinel.py --cards "CARD1,CARD2,..."` |
| **`scripts/setup_network.sh`** | عزل المسارات (QoS) وإنشاء مصفوفة الـ 32 IP الفرعية على الإيثرنت | `sudo ./scripts/setup_network.sh` |
| **`scripts/power_lock.sh`** | حظر السكون عند إغلاق غطاء اللابتوب للعمل المتواصل طوال الليل | `./scripts/power_lock.sh &` |
| **`scripts/windows_turbo_setup.ps1`** | إعداد بيئة ويندوز ومنع السكون وتشغيل المحرك عبر بايثون | `powershell -File scripts\windows_turbo_setup.ps1` |

---

## 💡 القواعد الهندسية الذهبية (Core Architecture & Rules)

### 1. عزل المسارات وتفادي الاختناق (Policy Routing & QoS Isolation):
- **الواي فاي (`wlp4s0`):** مخصص بنسبة 100% للأنظمة التفاعلية (Antigravity وتصفح الويب) بأولوية قصوى (`metric 50`).
- **الإيثرنت (`enp3s0`):** مخصص حصراً لحركة التنزيل الثقيلة بجدول توجيه منفصل (`table 102`).
```bash
sudo ip rule add from 10.2.81.0/24 table 102
sudo ip route replace default via 10.2.81.1 dev enp3s0 table 102
sudo ip route replace default via 10.4.88.1 dev wlp4s0 metric 50
```

### 2. مصفوفة الآيبيات الفرعية (Secondary IP Aliasing):
توليد 32 عنوان IP فرعي على نفس كرت الإيثرنت لتجاوز قيود سرعة المسار الواحد في الميكروتك:
```bash
for i in $(seq 100 131); do
    sudo ip addr add 10.2.81.$i/24 dev enp3s0 2>/dev/null || true
done
```

### 3. قاعدة التبديل الذهبية لبوابات Mikrotik Hotspot:
> [!IMPORTANT]
> **يجب دوماً إرسال طلب تسجيل خروج صريح (`/logout`) قبل طلب تسجيل الدخول للبطاقة الجديدة:**
> سيرفرات الميكروتك ترفض الجلسات المتزامنة لنفس عنوان الماك (`MAC`). إذا لم يتم تسجيل الخروج أولاً، يفشل تسجيل الدخول وتُهدر البطاقات الصالحة بالخطأ.

### 4. محرك الاستئناف النظيف ومنع تكرار البايتات (No Duplicate Appends):
- يمنع استخدام `--retry 999` داخل أمر `curl`؛ لأن انقطاع الاتصال المؤقت يجعل `curl` يعيد طلب النطاق من الصفر داخل نفس الملف المفتوح بنمط `"ab"`، مما يضخم حجم القطع عن حجمها الحقيقي.
- المعالجة الصحيحة: ضبط مهلة منخفضة (`--speed-limit 5000 --speed-time 12`)، وتفعيل الاستئناف بالبايت الدقيق وحساب النطاق المتبقي فورياً.

### 5. التوسع عالي الكثافة (100 - 200 مسار متزامن) والمعمارية التكيفية:
> [!TIP]
> **تحليل قيود السرعة بين السيرفر والميكروتك:**
> 1. **قيود الميكروتك (Local Router Queue):** في بوابات الهوتسبوت، كل جلسة كرت/MAC مقيدة بسقف محدد (مثلاً 10-12 Mbps لكل بطاقة). استخدام 32 مساراً كافٍ لاستخراج 100% من عرض نطاق البطاقة الواحدة.
> 2. **قيود خوادم الـ CDN والمواقع (Hugging Face / Cloudflare Rate Limits):** فتح 100-200 اتصال TCP متزامن دفعة واحدة من عنوان IP واحد يتسبب في تشغيل حماية Cloudflare Anti-DDoS، مما يؤدي إلى حظر جزئي أو أخطاء `HTTP 429 Too Many Requests` أو إسقاط الاتصالات `TCP RST`.
> 3. **المعمارية التكيفية للسرعة القصوى:**
>    - **للمواقع غير المقيدة (Unconstrained Mirrors):** يدعم المحرك تشغيل حتى 200 مسار (`--streams 200 --chunks 400`) مع مصفوفة 200 IP فرعي (`10.2.81.50-250`) لملء سعة الخط السلكي بالكامل.
>    - **للمواقع المقيدة بحماية (Cloudflare/Hugging Face):** يطبق المحرك تقنية التدرج الزمني (`Staggered Ramp-Up` بفاصل 15-20ms بين المسارات) مع التراجع الأسي الذكي (`Adaptive Backoff`) عند رصد أي تباطؤ لتجنب كشف الأداة كـ DDoS.

---

## ⚡ كيف يستجيب الوكيل عند طلب المستخدم `/fast` أو "التنزيل السريع":

1. **التحقق من الرابط وتحديد حجم الملف:**
   - استخراج الرابط وحجم الملف بدقة عبر HTTP HEAD (`Content-Length` أو `Content-Range`).
   - تحديد مجلد الوجهة المناسب (افتراضياً في مجلدات LM Studio: `~/.lmstudio/models/...`).
2. **احتساب الرصيد وطلب الكروت الاحتياطية تفاعلياً (Interactive Card Provisioning):**
   - فحص الرصيد المتبقي على الكرت النشط عبر `http://10.0.0.1/status`.
   - إذا كان حجم الملف يتجاوز الرصيد المتبقي:
     - حساب عدد الكروت اللازمة: `(حجم الملف - الرصيد الحالي) / سعة الكرت`.
     - توجيه تنبيه مباشر للمستخدم:
       > *"حجم الملف المطلوب هو [X] GiB ويتجاوز سعة الكرت الحالي ([Y] GiB متبقية). يُرجى تزويدي بأرقام الكروت الاحتياطية المتوفرة لديك لتسليح حارس الرصيد التلقائي لضمان عدم انقطاع التنزيل أثناء نومك."*
     - بمجرد استلام الأرقام من المستخدم، يتم إطلاق الحارس في الخلفية:
       `hotspot-sentinel --cards "CARD1,CARD2,..." &`
3. **فحص جاهزية الشبكة والمسارات (QoS Routing):**
   - التأكد من سريان جدول التوجيه 102 للإيثرنت ومصفوفة الآيبيات الفرعية:
     `sudo setup_network.sh 32` (أو 200 للمسارات الكثيفة).
4. **إطلاق محرك التوربو كعملية خلفية (Daemon):**
   ```bash
   fast-download \
       --url "<TARGET_URL>" \
       --dest "<DEST_DIR>" \
       --streams 32 \
       --chunks 64 \
       --verify-gguf &
   ```
5. **تفعيل مانع السكون:** تشغيل `power_lock.sh &` لحظر سكون اللابتوب عند إغلاق الغطاء.
6. **المراقبة الدورية وإبلاغ المستخدم:** قراءة ملف `DOWNLOAD_STATUS.json` وتقديم تقارير دقيقة بالنسبة المئوية والسرعة والوقت المتبقي.
