# ============================================================================
# إعدادات البوت - NeuroHost V8 Enhanced
# ============================================================================

import os
from enum import Enum

# ═══════════════════════════════════════════════════════════════════════════
# الإعدادات الأساسية
# ═══════════════════════════════════════════════════════════════════════════

# التوكن والمعرفات
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0")) if os.getenv("ADMIN_ID") else 0
DEVELOPER_USERNAME = os.getenv("DEVELOPER_USERNAME", "support")

# معلومات الإصدار
VERSION = "8.5.0"
VERSION_NAME = "Ultimate Edition"
RELEASE_DATE = "فبراير 2026"

# التحقق من بيانات اعتماد مهمة عند البدء
def validate_credentials():
    """التحقق من بيانات الاعتماد عند بدء التطبيق"""
    if not TOKEN or TOKEN == "":
        raise ValueError("❌ TELEGRAM_BOT_TOKEN غير محدد في متغيرات البيئة")
    if ADMIN_ID == 0:
        raise ValueError("❌ ADMIN_ID غير محدد في متغيرات البيئة")

# ═══════════════════════════════════════════════════════════════════════════
# إعدادات الملفات والمجلدات
# ═══════════════════════════════════════════════════════════════════════════

DB_FILE = "neurohost_v8.db"
BOTS_DIR = "bots"
ERROR_LOG_FILE = "neurohost_errors.log"
LOG_DIR = "logs"
BACKUP_DIR = "backups"

# حدود الملفات (MB)
MAX_FILE_SIZE_MB = 50
MAX_EDIT_FILE_SIZE_MB = 5
MAX_ZIP_SIZE_MB = 100

# ═══════════════════════════════════════════════════════════════════════════
# الأدوار والصلاحيات
# ═══════════════════════════════════════════════════════════════════════════

class UserRole(Enum):
    USER = "user"
    MODERATOR = "moderator"
    PREMIUM = "premium"
    ADMIN = "admin"

class UserStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    BLOCKED = "blocked"

# ═══════════════════════════════════════════════════════════════════════════
# نظام الخطط المتقدم
# ═══════════════════════════════════════════════════════════════════════════

PLANS = {
    'free': {
        'time': 86400,                # 24 ساعة
        'power': 30.0,
        'max_bots': 2,
        'name': 'مجاني',
        'cpu_limit': 50,
        'mem_limit': 256,
        'emoji': '🔵',
        'price': 'مجاني',
        'priority': 1,
        'features': [
            'بوتان كحد أقصى',
            'وقت استضافة 24 ساعة',
            'استرجاع يومي مجاني',
            'مدير ملفات أساسي'
        ],
        'limits': {
            'daily_restarts': 5,
            'max_file_size': 10,
            'backup_enabled': False
        }
    },
    'pro': {
        'time': 604800,               # 7 أيام
        'power': 60.0,
        'max_bots': 5,
        'name': 'احترافي',
        'cpu_limit': 80,
        'mem_limit': 512,
        'emoji': '🟢',
        'price': '$10/شهر',
        'priority': 2,
        'features': [
            '5 بوتات كحد أقصى',
            'وقت استضافة أسبوع',
            'استرجاع يومي مجاني',
            'مدير ملفات متقدم',
            'دعم فني أساسي',
            'نسخ احتياطي يومي'
        ],
        'limits': {
            'daily_restarts': 15,
            'max_file_size': 30,
            'backup_enabled': True
        }
    },
    'ultra': {
        'time': 2592000,              # 30 يوم
        'power': 100.0,
        'max_bots': 10,
        'name': 'فائق',
        'cpu_limit': 100,
        'mem_limit': 1024,
        'emoji': '🟣',
        'price': '$25/شهر',
        'priority': 3,
        'features': [
            '10 بوتات كحد أقصى',
            'وقت استضافة شهر كامل',
            'استرجاع يومي مجاني × 2',
            'مدير ملفات كامل',
            'دعم فني متقدم',
            'نسخ احتياطي تلقائي',
            'أولوية عالية في التنفيذ',
            'إحصائيات متقدمة'
        ],
        'limits': {
            'daily_restarts': 50,
            'max_file_size': 50,
            'backup_enabled': True
        }
    },
    'supreme': {
        'time': 999999999,            # غير محدود
        'power': 150.0,
        'max_bots': 100,
        'name': 'أسطوري',
        'cpu_limit': 100,
        'mem_limit': 2048,
        'emoji': '👑',
        'price': 'حصري',
        'priority': 4,
        'features': [
            'بوتات غير محدودة',
            'وقت تشغيل لا نهائي',
            'موارد حصرية للخادم',
            'دعم VIP على مدار الساعة',
            'أولوية قصوى',
            'نسخ احتياطي فوري',
            'إحصائيات حية',
            'تحكم كامل في الموارد',
            'API خاص'
        ],
        'limits': {
            'daily_restarts': -1,     # غير محدود
            'max_file_size': 100,
            'backup_enabled': True
        }
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# حالات المحادثة
# ═══════════════════════════════════════════════════════════════════════════

CONVERSATION_STATES = {
    'WAIT_FILE': 0,
    'WAIT_TOKEN': 1,
    'WAIT_FEEDBACK': 2,
    'WAIT_GITHUB': 3,
    'WAIT_FILE_ACTION': 4,
    'WAIT_FILE_EDIT': 5,
    'WAIT_BROADCAST': 6,
    'WAIT_USER_ID': 7,
    'WAIT_PLAN_SELECTION': 8,
    'WAIT_RENAME': 9
}

# ═══════════════════════════════════════════════════════════════════════════
# إعدادات العمليات والمراقبة
# ═══════════════════════════════════════════════════════════════════════════

RESTART_COOLDOWN = 30               # ثواني بين إعادة التشغيل
RESTART_TIME_COST = 300             # تكلفة إعادة التشغيل (ثواني)
MAX_RESTARTS = 5                    # الحد الأقصى لإعادة التشغيل
MONITOR_CHECK_INTERVAL = 10         # فترة المراقبة (ثواني)
WARNING_COOLDOWN = 300              # فترة بين التحذيرات (ثواني)
RECOVERY_TIME = 7200                # وقت الاسترجاع اليومي (ساعتين)

# إعدادات الأداء
MAX_CONCURRENT_BOTS = 50            # الحد الأقصى للبوتات المتزامنة
PROCESS_TIMEOUT = 300               # مهلة العملية (ثواني)
STARTUP_TIMEOUT = 120               # مهلة بدء التشغيل

# ═══════════════════════════════════════════════════════════════════════════
# الرسائل والنصوص
# ═══════════════════════════════════════════════════════════════════════════

MESSAGES = {
    # أخطاء
    'error_admin_only': '⛔ هذه الميزة متاحة للأدمن فقط',
    'error_bot_not_found': '❌ البوت غير موجود أو تم حذفه',
    'error_file_not_found': '❌ الملف غير موجود',
    'error_unexpected': '❌ حدث خطأ غير متوقع. حاول مرة أخرى',
    'error_permission': '⛔ ليس لديك صلاحية لهذا الإجراء',
    'error_limit_reached': '⚠️ وصلت للحد الأقصى المسموح',
    'error_invalid_token': '❌ التوكن غير صالح',
    'error_token_exists': '⚠️ التوكن مستخدم بالفعل',

    # نجاح
    'success_bot_started': '✅ تم بدء البوت بنجاح',
    'success_bot_stopped': '✅ تم إيقاف البوت',
    'success_bot_added': '✅ تم إضافة البوت بنجاح',
    'success_bot_deleted': '✅ تم حذف البوت',
    'success_file_uploaded': '✅ تم رفع الملف بنجاح',
    'success_file_updated': '✅ تم تحديث الملف',
    'success_time_added': '✅ تم إضافة الوقت',
    'success_recovery': '✅ تم الاسترجاع بنجاح',

    # تحذيرات
    'warning_low_time': '⚠️ الوقت المتبقي منخفض',
    'warning_sleep_mode': '😴 البوت في وضع السكون',
    'warning_restart_limit': '⚠️ تم الوصول لحد إعادة التشغيل'
}

# ═══════════════════════════════════════════════════════════════════════════
# إعدادات التصميم
# ═══════════════════════════════════════════════════════════════════════════

UI_CONFIG = {
    'separator': '═' * 40,
    'separator_light': '─' * 35,
    'max_items_per_page': 10,
    'max_filename_display': 15,
    'max_log_entries': 25,
    'bar_length': 10
}

# ═══════════════════════════════════════════════════════════════════════════
# إعدادات الأمان
# ═══════════════════════════════════════════════════════════════════════════

SECURITY_CONFIG = {
    'max_login_attempts': 5,
    'session_timeout': 3600,
    'rate_limit_per_minute': 30,
    'blocked_extensions': ['.exe', '.bat', '.sh', '.dll'],
    'allowed_extensions': ['.py', '.txt', '.json', '.yml', '.yaml', '.md', '.env', '.cfg']
}
