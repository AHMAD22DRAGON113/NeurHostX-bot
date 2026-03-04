# ============================================================================
# إعدادات البوت - NeuroHost V9.2
# ============================================================================

import os
import json
from enum import Enum
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
# 🔑 بيانات الاعتماد الأساسية (ملء هذه الحقول)
# ═══════════════════════════════════════════════════════════════════════════

# توكن البوت من البوت فاذر (@BotFather)
# مثال: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz..."
TELEGRAM_BOT_TOKEN = ""

# معرف الأدمن (رقمك الشخصي في تيليجرام)
# يمكنك الحصول عليه من @userinfobot
ADMIN_ID = 0

# اسم المطور (اليوزرنيم الخاص بك)
# مثال: "@yourusername"
DEVELOPER_USERNAME = ""

# ═══════════════════════════════════════════════════════════════════════════
# معلومات الإصدار
# ═══════════════════════════════════════════════════════════════════════════

VERSION = "9.2.0"
VERSION_NAME = "Final Release"
RELEASE_DATE = "مارس 2026"

def _load_credentials_from_file():
    """تحميل بيانات الاعتماد من credentials.json أو متغيرات البيئة"""
    global TELEGRAM_BOT_TOKEN, ADMIN_ID, DEVELOPER_USERNAME
    
    # محاولة قراءة من credentials.json
    creds_file = Path(__file__).parent / "credentials.json"
    if creds_file.exists():
        try:
            with open(creds_file, 'r', encoding='utf-8') as f:
                creds = json.load(f)
                TELEGRAM_BOT_TOKEN = creds.get("TELEGRAM_BOT_TOKEN") or TELEGRAM_BOT_TOKEN
                ADMIN_ID = creds.get("ADMIN_ID") or ADMIN_ID
                DEVELOPER_USERNAME = creds.get("DEVELOPER_USERNAME") or DEVELOPER_USERNAME
        except Exception as e:
            print(f"⚠️ خطأ في قراءة credentials.json: {e}")
    
    # استخدام متغيرات البيئة كخيار بديل
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN)
    if os.getenv("ADMIN_ID"):
        try:
            ADMIN_ID = int(os.getenv("ADMIN_ID"))
        except ValueError:
            pass
    DEVELOPER_USERNAME = os.getenv("DEVELOPER_USERNAME", DEVELOPER_USERNAME)

# تحميل بيانات الاعتماد من الملفات عند استيراد الملف
_load_credentials_from_file()

# التحقق من بيانات اعتماد مهمة عند البدء
def validate_credentials():
    """التحقق من بيانات الاعتماد عند بدء التطبيق"""
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "":
        raise ValueError("❌ TELEGRAM_BOT_TOKEN غير محدد في config.py أو credentials.json")
    if ADMIN_ID == 0:
        raise ValueError("❌ ADMIN_ID غير محدد في config.py أو credentials.json")


# ═══════════════════════════════════════════════════════════════════════════
# 📁 إعدادات الملفات والمجلدات
# ═══════════════════════════════════════════════════════════════════════════

# اسم قاعدة البيانات
DATABASE_FILE = "neurohost_v9.db"

# مجلدات المشروع
BOTS_DIRECTORY = "bots"                    # مجلد البوتات
LOGS_DIRECTORY = "logs"                    # مجلد السجلات
BACKUPS_DIRECTORY = "backups"              # مجلد النسخ الاحتياطية
TEMP_DIRECTORY = "temp"                    # مجلد الملفات المؤقتة

# ملفات السجل
ERROR_LOG_FILE = "errors.log"
ACTIVITY_LOG_FILE = "activity.log"

# حدود حجم الملفات (بالميجابايت)
MAX_FILE_UPLOAD_SIZE_MB = 50               # أقصى حجم للملف المرفوع
MAX_EDIT_FILE_SIZE_MB = 5                  # أقصى حجم للملف القابل للتعديل
MAX_ZIP_SIZE_MB = 100                      # أقصى حجم لملف ZIP


# ═══════════════════════════════════════════════════════════════════════════
# 👥 الأدوار والصلاحيات
# ═══════════════════════════════════════════════════════════════════════════

class UserRole(Enum):
    """أدوار المستخدمين المختلفة"""
    USER = "user"              # مستخدم عادي
    MODERATOR = "moderator"    # مشرف
    PREMIUM = "premium"        # مستخدم متقدم
    ADMIN = "admin"            # مسؤول

class UserStatus(Enum):
    """حالات المستخدم"""
    PENDING = "pending"        # في الانتظار
    APPROVED = "approved"      # موافق عليه
    BLOCKED = "blocked"        # محظور


# ═══════════════════════════════════════════════════════════════════════════
# 📊 نظام الخطط والإشتراكات
# ═══════════════════════════════════════════════════════════════════════════

PLANS = {
    'free': {
        'name': 'مجاني',
        'emoji': '🔵',
        'price': 'مجاني',
        'priority': 1,
        
        # حدود الموارد
        'max_bots': 2,
        'max_power': 30.0,
        'cpu_limit': 50,
        'memory_limit_mb': 256,
        'max_file_size_mb': 10,
        
        # الوقت والمدة
        'validity_days': 1,           # صالح لـ 24 ساعة
        'validity_seconds': 86400,
        'daily_restart_limit': 5,
        
        # الميزات
        'backup_enabled': False,
        'support_level': 'none',
        'analytics_basic': True,
        
        'features': [
            'بوتان كحد أقصى',
            'وقت استضافة 24 ساعة',
            'استرجاع يومي مجاني',
            'مدير ملفات أساسي'
        ]
    },
    
    'pro': {
        'name': 'احترافي',
        'emoji': '🟢',
        'price': '$10/شهر',
        'priority': 2,
        
        # حدود الموارد
        'max_bots': 5,
        'max_power': 60.0,
        'cpu_limit': 80,
        'memory_limit_mb': 512,
        'max_file_size_mb': 30,
        
        # الوقت والمدة
        'validity_days': 7,            # صالح لـ 7 أيام
        'validity_seconds': 604800,
        'daily_restart_limit': 15,
        
        # الميزات
        'backup_enabled': True,
        'support_level': 'basic',
        'analytics_basic': True,
        'analytics_advanced': False,
        
        'features': [
            '5 بوتات كحد أقصى',
            'وقت استضافة أسبوع',
            'استرجاع يومي مجاني',
            'مدير ملفات متقدم',
            'دعم فني أساسي',
            'نسخ احتياطي يومي'
        ]
    },
    
    'ultra': {
        'name': 'فائق',
        'emoji': '🟣',
        'price': '$25/شهر',
        'priority': 3,
        
        # حدود الموارد
        'max_bots': 10,
        'max_power': 100.0,
        'cpu_limit': 100,
        'memory_limit_mb': 1024,
        'max_file_size_mb': 50,
        
        # الوقت والمدة
        'validity_days': 30,           # صالح لـ 30 يوم
        'validity_seconds': 2592000,
        'daily_restart_limit': 50,
        
        # الميزات
        'backup_enabled': True,
        'support_level': 'advanced',
        'analytics_basic': True,
        'analytics_advanced': True,
        
        'features': [
            '10 بوتات كحد أقصى',
            'وقت استضافة شهر كامل',
            'استرجاع يومي مجاني × 2',
            'مدير ملفات كامل',
            'دعم فني متقدم',
            'نسخ احتياطي تلقائي',
            'أولوية عالية',
            'إحصائيات متقدمة'
        ]
    },
    
    'supreme': {
        'name': 'أسطوري',
        'emoji': '👑',
        'price': 'حصري',
        'priority': 4,
        
        # حدود الموارد
        'max_bots': 100,
        'max_power': 150.0,
        'cpu_limit': 100,
        'memory_limit_mb': 2048,
        'max_file_size_mb': 100,
        
        # الوقت والمدة
        'validity_days': 365,          # صالح لـ سنة
        'validity_seconds': 999999999,
        'daily_restart_limit': -1,     # غير محدود
        
        # الميزات
        'backup_enabled': True,
        'support_level': 'vip',
        'analytics_basic': True,
        'analytics_advanced': True,
        
        'features': [
            'بوتات غير محدودة',
            'وقت تشغيل لا نهائي',
            'موارد حصرية',
            'دعم VIP 24/7',
            'أولوية قصوى',
            'نسخ احتياطي فوري',
            'إحصائيات حية',
            'تحكم كامل في الموارد',
            'API خاص'
        ]
    }
}


# ═══════════════════════════════════════════════════════════════════════════
# 💬 حالات المحادثة والتفاعلات
# ═══════════════════════════════════════════════════════════════════════════

CONVERSATION_STATES = {
    'WAIT_FILE': 0,                # انتظار ملف
    'WAIT_TOKEN': 1,               # انتظار توكن
    'WAIT_FEEDBACK': 2,            # انتظار تغذية راجعة
    'WAIT_GITHUB': 3,              # انتظار رابط GitHub
    'WAIT_FILE_ACTION': 4,         # انتظار إجراء على الملف
    'WAIT_FILE_EDIT': 5,           # انتظار تعديل الملف
    'WAIT_BROADCAST': 6,           # انتظار رسالة البث
    'WAIT_USER_ID': 7,             # انتظار معرف المستخدم
    'WAIT_PLAN_SELECTION': 8,      # انتظار اختيار الخطة
    'WAIT_RENAME': 9,              # انتظار إعادة تسمية
    'WAIT_MAIN_FILE': 10,          # انتظار الملف الرئيسي
    'WAIT_DESCRIPTION': 11,        # انتظار الوصف
    'WAIT_MUTE_REASON': 12,        # انتظار سبب الكتم
}

# ═══════════════════════════════════════════════════════════════════════════
# ⚙️ إعدادات العمليات والمراقبة
# ═══════════════════════════════════════════════════════════════════════════

# تأخير وحدود إعادة التشغيل
PROCESS_RESTART_COOLDOWN_SECONDS = 30      # الانتظار بين إعادة التشغيل
RESTART_TIME_COST_SECONDS = 300            # تكلفة إعادة التشغيل بالثواني
MAX_DAILY_RESTARTS = 5                     # الحد الأقصى لإعادة التشغيل يومياً

# فترات المراقبة والتحقق
MONITOR_CHECK_INTERVAL_SECONDS = 10        # فترة فحص المراقبة
WARNING_COOLDOWN_SECONDS = 300             # الانتظار بين التحذيرات
DAILY_RECOVERY_TIME_SECONDS = 7200         # وقت الاسترجاع اليومي (ساعتين)

# حدود الأداء والعمليات
MAX_CONCURRENT_BOTS = 50                   # الحد الأقصى للبوتات المتزامنة
PROCESS_TIMEOUT_SECONDS = 300              # مهلة انتظار العملية
STARTUP_TIMEOUT_SECONDS = 120              # مهلة بدء التشغيل


# ═══════════════════════════════════════════════════════════════════════════
# 💬 الرسائل والنصوص (يمكن تعديلها حسب الحاجة)
# ═══════════════════════════════════════════════════════════════════════════

MESSAGES = {
    # ❌ الأخطاء
    'error_admin_only': 
        '⛔ هذه الميزة متاحة للأدمن فقط',
    'error_bot_not_found': 
        '❌ البوت غير موجود أو تم حذفه',
    'error_file_not_found': 
        '❌ الملف غير موجود',
    'error_unexpected': 
        '❌ حدث خطأ غير متوقع. حاول مرة أخرى',
    'error_permission': 
        '⛔ ليس لديك صلاحية لهذا الإجراء',
    'error_limit_reached': 
        '⚠️ وصلت للحد الأقصى المسموح',
    'error_invalid_token': 
        '❌ التوكن غير صالح',
    'error_token_exists': 
        '⚠️ التوكن مستخدم بالفعل',

    # ✅ النجاح
    'success_bot_started': 
        '✅ تم بدء البوت بنجاح',
    'success_bot_stopped': 
        '✅ تم إيقاف البوت',
    'success_bot_added': 
        '✅ تم إضافة البوت بنجاح',
    'success_bot_deleted': 
        '✅ تم حذف البوت',
    'success_file_uploaded': 
        '✅ تم رفع الملف بنجاح',
    'success_file_updated': 
        '✅ تم تحديث الملف',
    'success_time_added': 
        '✅ تم إضافة الوقت',
    'success_recovery': 
        '✅ تم الاسترجاع بنجاح',

    # ⚠️ التحذيرات
    'warning_low_time': 
        '⚠️ الوقت المتبقي منخفض',
    'warning_sleep_mode': 
        '😴 البوت في وضع السكون',
    'warning_restart_limit': 
        '⚠️ تم الوصول لحد إعادة التشغيل'
}

# ═══════════════════════════════════════════════════════════════════════════
# 🎨 إعدادات التصميم والواجهة
# ═══════════════════════════════════════════════════════════════════════════

UI_CONFIG = {
    'main_separator': '═' * 50,          # الفاصل الرئيسي
    'light_separator': '─' * 40,         # فاصل خفيف
    'max_items_per_page': 10,            # أقصى عدد عناصر في الصفحة
    'max_filename_display': 15,          # أقصى طول لاسم الملف المعروض
    'max_log_entries': 25,               # أقصى عدد سجلات
    'progress_bar_length': 10,           # طول شريط التقدم
    'emoji_success': '✅',
    'emoji_error': '❌',
    'emoji_warning': '⚠️',
    'emoji_info': 'ℹ️'
}

# ═══════════════════════════════════════════════════════════════════════════
# 🔒 إعدادات الأمان
# ═══════════════════════════════════════════════════════════════════════════

SECURITY_CONFIG = {
    # حدود تسجيل الدخول
    'max_login_attempts': 5,             # أقصى محاولات دخول
    'session_timeout_seconds': 3600,     # انتهاء الجلسة بعد ساعة
    
    # حدود المعدل
    'rate_limit_per_minute': 30,         # عدد الطلبات المسموح بها في الدقيقة
    
    # الملفات المحظورة
    'blocked_extensions': [
        '.exe',      # ملفات تنفيذية Windows
        '.bat',      # ملفات دفعية
        '.sh',       # ملفات bash
        '.dll',      # مكتبات ديناميكية
        '.scr',      # حماقات الشاشة
        '.vbs',      # VB Script
    ],
    
    # الملفات المسموح بها
    'allowed_extensions': [
        '.py',       # Python
        '.txt',      # نصوص عادية
        '.json',     # JSON
        '.yml',      # YAML
        '.yaml',     # YAML
        '.md',       # Markdown
        '.env',      # متغيرات البيئة
        '.cfg',      # ملفات التكوين
        '.conf',     # ملفات التكوين
        '.ini',      # INI files
    ]
}

# ═══════════════════════════════════════════════════════════════════════════
# 📝ملاحظة مهمة: إرشادات الملء
# ═══════════════════════════════════════════════════════════════════════════
"""
لملء الحقول المطلوبة أعلاه:

1️⃣ TELEGRAM_BOT_TOKEN:
   - انتقل إلى @BotFather على تيليجرام
   - اكتب /newbot واتبع التعليمات
   - انسخ النص "HTTP API" كاملاً

2️⃣ ADMIN_ID:
   - انتقل إلى @userinfobot على تيليجرام
   - سيظهر رقم معرفك
   - انسخ الرقم (بدون علامات)

3️⃣ DEVELOPER_USERNAME:
   - انتقل إلى إعدادات تيليجرام
   - انسخ اسم المستخدم (بما فيه @)
   - مثال: @yourusername

يمكنك أيضاً إنشاء ملف credentials.json بدلاً من ملء الحقول مباشرة:
{
    "TELEGRAM_BOT_TOKEN": "your_token_here",
    "ADMIN_ID": 123456789,
    "DEVELOPER_USERNAME": "@your_username"
}
"""

