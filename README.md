# NeurHostX Bot v8.5.0 - البوت الذكي لإدارة بوتات تيليجرام

## المزايا الرئيسية ✨

- 🤖 إدارة شاملة لبوتات تيليجرام
- 💾 نظام قاعدة بيانات متقدم SQLite
- 📊 إحصائيات وتقارير مفصلة
- 🔐 نظام أمان شامل
- 💳 نظام الدفع والخطط المتقدم
- 📁 مدير ملفات ذكي
- 🔔 نظام إشعارات ذكي
- ⚡ معالجة سريعة وآمنة

## متطلبات التشغيل 📋

- Python 3.8+
- Unix/Linux أو MacOS (أو Windows مع WSL)
- الحد الأدنى من الذاكرة: 256 MB

## التثبيت والإعداد 🚀

### 1. نسخ الملفات
```bash
git clone https://github.com/AHMAD22DRAGON113/NeurHostX-bot.git
cd NeurHostX-bot
```

### 2. تثبيت المتطلبات
```bash
pip install -r requirements.txt
```

### 3. إعداد بيانات الاعتماد

اختر أحد الخيارات التالية:

#### الخيار 1: استخدام credentials.json (موصى به)
```bash
cp credentials.example.json credentials.json
# ثم فتح credentials.json وأدخل بيانات التوكن والايدي
{
  "TELEGRAM_BOT_TOKEN": "your_actual_token_here",
  "ADMIN_ID": your_actual_admin_id_here,
  "DEVELOPER_USERNAME": "support"
}
```

#### الخيار 2: استخدام متغيرات البيئة
```bash
export TELEGRAM_BOT_TOKEN="your_token_here"
export ADMIN_ID=your_admin_id_here
python main.py
```

### 4. تشغيل البوت
```bash
python main.py
```

## هيكل المشروع 📁

```
NeurHostX-bot/
├── main.py                      # البرنامج الرئيسي
├── config.py                   # الإعدادات والثوابت
├── app_setup.py                # إعداد التطبيق
├── database.py                 # إدارة قاعدة البيانات
├── handlers.py                 # معالجات الأوامر الأساسية
├── handlers_files.py           # معالجات إدارة الملفات
├── handlers_advanced.py        # معالجات متقدمة
├── payment_system.py           # نظام الدفع
├── security_system.py          # نظام الأمان
├── process_manager.py          # مدير العمليات
├── settings_manager.py         # مدير الإعدادات
├── helpers.py                  # دوال مساعدة
├── formatters.py               # تنسيق الرسائل
├── help_manager.py             # مدير المساعدة
├── smart_notifications.py      # نظام الإشعارات
├── credentials.example.json    # مثال لملف بيانات الاعتماد
├── .env                        # متغيرات البيئة
├── requirements.txt            # متطلبات Python
└── help_content.json           # محتوى المساعدة
```

## الأوامر المتاحة 🎮

- `/start` - ابدأ مع البوت
- `/help` - احصل على المساعدة
- `/my_bots` - عرض بوتاتك
- `/admin` - لوحة التحكم (للأدمن فقط)

## الميزات الأمنية 🔒

- تشفير بيانات المستخدمين
- التحقق من الصلاحيات والأدوار
- نظام حظر المستخدمين
- تنبيهات أمنية

## استكشاف الأخطاء 🐛

إذا واجهت مشاكل:
1. تأكد من صحة التوكن والايدي في credentials.json
2. تأكد من تثبيت جميع المتطلبات: `pip install -r requirements.txt`
3. تحقق من السجلات في مجلد logs/

## الإعدادات المتقدمة ⚙️

يمكن تخصيص جميع الإعدادات من خلال ملف config.py:
- حدود الملفات والموارد
- إعدادات الخطط والأسعار
- رسائل النظام والإشعارات

## الترخيص 📜

جميع الحقوق محفوظة © 2026

---

**الإصدار:** 8.5.0 - Ultimate Edition  
**آخر تحديث:** فبراير 2026  
**المطور:** AHMAD22DRAGON113