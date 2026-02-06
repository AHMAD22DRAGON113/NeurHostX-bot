# 💳 دليل نظام الدفع والأمان - NeurHostX V8.5

## 🎯 نظرة عامة

تم إضافة نظام دفع متكامل لنجوم تيليجرام مع نظام أمان محسّن للبوتات المرفوعة.

---

## 💰 نظام الدفع بنجوم تيليجرام

### الملفات الجديدة:
1. **payment_system.py** - نظام الدفع الأساسي
2. **payment_handlers.py** - معالجات الشراء والدفع
3. **database_migrations.py** - تحديثات قاعدة البيانات

### أسعار الخطط:

| الخطة | السعر | الميزات |
|------|-------|---------|
| 🔵 **احترافي (Pro)** | **5 نجوم** | 5 بوتات، أسبوع وقت |
| 🟣 **فائق (Ultra)** | **10 نجوم** | 10 بوتات، شهر وقت، إحصائيات |
| 👑 **أسطوري (Supreme)** | **25 نجم** | بوتات غير محدودة، وقت غير محدود |

---

## 🔄 تدفق الشراء

```
المستخدم يضغط "اشتر خطة"
    ↓
عرض قائمة الخطط
    ↓
اختيار الخطة المطلوبة
    ↓
عرض تفاصيل الخطة + السعر
    ↓
اضغط "ادفع بـ X نجوم"
    ↓
إرسال فاتورة تيليجرام
    ↓
نافذة الدفع الآمنة (مدمجة)
    ↓
المستخدم يدفع
    ↓
التحقق من الدفع
    ↓
تحديث الخطة في قاعدة البيانات
    ↓
رسالة تأكيد النجاح ✅
```

---

## 📱 واجهة المستخدم

### قائمة الخطط:
```
💎 خطط الاشتراك

🟢 احترافي (Pro) - 5 نجوم
📝 5 بوتات، أسبوع وقت

🟣 فائق (Ultra) - 10 نجوم
📝 10 بوتات، شهر وقت

👑 أسطوري (Supreme) - 25 نجم
📝 بوتات غير محدودة، وقت غير محدود

[ادفع] [ادفع] [ادفع]
[رجوع]
```

### صفحة التأكيد:
```
✅ تأكيد الشراء

🟢 خطة احترافية
✓ 5 بوتات كحد أقصى
✓ وقت استضافة أسبوع
✓ استرجاع يومي
...

💳 السعر النهائي: 5 نجوم

[ادفع بـ 5 نجوم] [إلغاء]
```

---

## 🔐 نظام الحماية المحسّن

### الملف الجديد:
**security_system.py**

### المميزات:

#### 1. ماسح الأمان (SecurityScanner)
```python
from security_system import SecurityScanner

# فحص ملف واحد
is_safe, message = SecurityScanner.scan_file("bot.py")

# فحص مجلد كامل
is_safe, safe_files, unsafe_files = SecurityScanner.scan_directory("bots/bot_123")

# حساب hash الملف
file_hash = SecurityScanner.get_file_hash("main.py")

# التحقق من السلامة
SecurityScanner.verify_file_integrity("main.py", expected_hash)
```

#### 2. تحديد معدل الطلبات (RateLimiter)
```python
from security_system import RateLimiter

limiter = RateLimiter(max_requests=5, window_seconds=60)

# التحقق من السماح
is_allowed, remaining = limiter.is_allowed(user_id)

if not is_allowed:
    waiting_time = limiter.get_remaining_time(user_id)
```

#### 3. مُدقق الملفات (FileValidator)
```python
from security_system import FileValidator

# التحقق من نوع الملف
is_allowed, message = FileValidator.is_file_allowed("script.py")

# التحقق من اسم الملف
is_valid, message = FileValidator.validate_filename("my_bot.py")

# تنظيف المسار (منع path traversal)
clean_path = FileValidator.clean_path("../../../etc/passwd", "bots/")
```

#### 4. مدير أمان البوتات (BotSecurityManager)
```python
from security_system import BotSecurityManager

manager = BotSecurityManager()

# فحص البوت عند الرفع
is_safe, warnings = await manager.validate_bot_upload(user_id, bot_folder)

# الحصول على تقرير الأمان
report = manager.format_security_report(warnings)
```

---

## 🛡️ آليات الحماية

### 1. فحص الملحقات الخطرة ❌
```
محظور: .exe, .bat, .dll, .sh, .vbs, .ps1, .jar, إلخ
مسموح: .py, .js, .txt, .json, .yml, إلخ
```

### 2. البحث عن أكواد خطرة 🔍
```python
كلمات مفتاحية خطرة:
- os.system()
- subprocess.call()
- eval()
- exec()
- __import__()
- socket.socket()
```

### 3. حدود حجم الملفات 📊
```
ملف واحد:    50 MB
مجلد كامل:  500 MB
```

### 4. تحديد معدل الطلبات ⏱️
```
الحد الأقصى: 5 طلبات
الفترة:     60 ثانية
التنبيه:    "يرجى الانتظار X ثانية"
```

### 5. فحص سلامة الملفات 🔐
```
- حساب SHA-256 hash
- التحقق من التعديلات
- كشف التلف أو الفساد
```

---

## 💾 التحديثات في قاعدة البيانات

### جداول جديدة:

#### 1. جدول الفواتير (invoices)
```
id              - معرف الفاتورة
user_id         - معرف المستخدم
plan            - اسم الخطة
amount          - المبلغ بالنجوم
status          - حالة الفاتورة (pending/completed)
payload         - بيانات الفاتورة
created_at      - وقت الإنشاء
completed_at    - وقت الاكتمال
transaction_id  - معرف المعاملة
```

#### 2. جدول المعاملات (transactions)
```
id              - معرف المعاملة
user_id         - معرف المستخدم
invoice_id      - معرف الفاتورة
plan            - اسم الخطة
amount          - المبلغ
status          - الحالة (pending/completed/failed)
payment_method  - طريقة الدفع (telegram_stars)
telegram_charge_id - معرف الرسوم تيليجرام
created_at      - وقت الإنشاء
```

#### 3. جدول القسائم (coupons)
```
id              - معرف القسيمة
code            - كود القسيمة
discount_percent - نسبة الخصم
max_uses        - الحد الأقصى للاستخدام
valid_from      - تاريخ البدء
valid_until     - تاريخ الانتهاء
status          - الحالة
```

### أعمدة جديدة للأمان:
```
bots table:
- security_hash         - hash الملفات
- last_security_check   - آخر فحص أمان
- security_warnings     - التحذيرات
- is_verified           - هل تم التحقق منه
```

---

## 🚀 البدء السريع

### 1. تهيئة الدفع:
```python
from database_migrations import initialize_payment_system

initialize_payment_system("neurohost_v8.db")
```

### 2. تثبيت المعالجات:
```python
from payment_handlers import setup_payment_handlers

setup_payment_handlers(app, db)
```

### 3. معالجة الفاتورة:
```python
# تلقائياً عند إرسال /start
# ستظهر خيارات الشراء في القائمة الرئيسية
```

---

## 📊 مثال عملي: معالج الشراء

```python
async def my_plan(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    # عرض الخطة الحالية
    user_plan = db.get_user_plan(user_id, admin_id)

    keyboard = [
        [InlineKeyboardButton("💎 شراء خطة مدفوعة", callback_data="plans_menu")],
        [InlineKeyboardButton("📜 سجل الشراء", callback_data="purchase_history")],
        [InlineKeyboardButton("💰 طلب استرجاع", callback_data="refund_request")],
    ]

    await query.edit_message_text(..., reply_markup=InlineKeyboardMarkup(keyboard))
```

---

## 🔔 معالجات الدفع التلقائية

### 1. PreCheckoutQuery
```python
async def pre_checkout_callback(update, context, db):
    # التحقق من البيانات
    query = update.pre_checkout_query

    if is_valid:
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="...")
```

### 2. SuccessfulPayment
```python
async def successful_payment_callback(update, context, db):
    # تحديث الخطة
    # إرسال تأكيد
    # حفظ في قاعدة البيانات
```

---

## 📈 الإحصائيات والتقارير

### الحصول على إحصائيات المبيعات:
```python
stats = db.get_revenue_stats(days=30)
# {
#     'total_sales': 15,
#     'total_revenue': 120,  # نجم
#     'avg_transaction': 8
# }
```

---

## ⚙️ الإعدادات في settings.json

```json
{
  "payment": {
    "enabled": true,
    "currency": "XTR",
    "plans": {
      "pro": 5,
      "ultra": 10,
      "supreme": 25
    },
    "refund_days": 14,
    "payment_timeout_minutes": 15
  },

  "security": {
    "enable_scanner": true,
    "scan_on_upload": true,
    "rate_limit": 5,
    "rate_limit_window": 60,
    "max_file_size_mb": 50,
    "check_file_integrity": true
  }
}
```

---

## 🐛 استكشاف الأخطاء

### مشكلة: "خطأ في إرسال الفاتورة"
```
السبب: عدم تفعيل Telegram Payments في البوت
الحل:
1. تأكد من أن البوت يدعم Telegram Stars
2. تواصل مع @BotFather لتفعيل Payments
```

### مشكلة: "فشل الدفع"
```
السبب: عدم تطابق البيانات
الحل:
1. تحقق من السعر الصحيح
2. تحقق من معرف المستخدم
3. قم بإعادة المحاولة
```

---

## 📝 الملفات المرتبطة

- `payment_system.py` - نظام الدفع (200 سطر)
- `payment_handlers.py` - معالجات الشراء (300 سطر)
- `security_system.py` - نظام الحماية (400 سطر)
- `database_migrations.py` - تحديثات قاعدة البيانات (200 سطر)

---

## ✅ قائمة التحقق

- [x] نظام الدفع متكامل
- [x] معالجات الفواتير
- [x] التحقق الآمن
- [x] جداول قاعدة بيانات
- [x] نظام الحماية
- [x] الفحص الأمني
- [x] تحديد معدل الطلبات
- [x] التوثيق الشامل

---

**الإصدار:** 8.5.0 + Payment System
**الحالة:** ✅ جاهز
