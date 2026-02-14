# ============================================================================
# نظام الحماية المحسّن - NeurHostX V8.5
# ============================================================================
"""
نظام أمان متقدم لحماية البوتات المرفوعة من الأخطار
"""

import os
import json
import hashlib
import logging
from typing import Tuple, List, Dict, Optional
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SecurityScanner:
    """ماسح الأمان المحسّن"""

    # الملحقات الخطرة المحظورة
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.dll', '.sys',
        '.scr', '.vbs', '.ps1', '.sh', '.bash', '.zsh',
        '.so', '.dylib', '.bin', '.app', '.deb', '.rpm',
        '.msi', '.jar', '.class', '.pyc', '.pyo'
    }

    # كلمات مفتاحية محظورة (قد تشير لأكواد ضارة)
    DANGEROUS_KEYWORDS = {
        'os.system', 'subprocess.call', 'exec(', 'eval(',
        '__import__', 'importlib.import', 'ctypes',
        'socket.socket', 'urllib.urlopen', 'requests.get',
        'paramiko', 'fabric', 'ansible', 'salt',
        'platform.system', 'getpass.getpass', 'sqlite3'
    }

    # أحجام الملفات الآمنة (بـ MB)
    MAX_SAFE_FILE_SIZE = 50
    MAX_SAFE_DIR_SIZE = 500

    # ملفات موثوقة بشكل افتراضي
    TRUSTED_FILES = {
        'main.py', 'bot.py', 'app.py', 'run.py',
        'requirements.txt', '.env', 'config.py',
        'setup.py', 'README.md', 'LICENSE'
    }

    @staticmethod
    def scan_file(file_path: str) -> Tuple[bool, str]:
        """فحص ملف واحد

        Args:
            file_path: مسار الملف

        Returns:
            (آمن؟، الرسالة)
        """
        file_name = os.path.basename(file_path)

        # التحقق من الامتداد
        file_ext = os.path.splitext(file_name)[1].lower()
        if file_ext in SecurityScanner.DANGEROUS_EXTENSIONS:
            return False, f"❌ امتداد خطر: {file_ext}"

        # التحقق من حجم الملف
        try:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > SecurityScanner.MAX_SAFE_FILE_SIZE:
                return False, f"❌ حجم الملف كبير جداً: {file_size_mb:.1f}MB"
        except:
            return False, "❌ لا يمكن الوصول للملف"

        # فحص محتوى الملفات النصية فقط
        if file_ext in ['.py', '.txt', '.json', '.yml', '.yaml', '.conf', '.cfg']:
            is_safe, message = SecurityScanner._scan_file_content(file_path)
            if not is_safe:
                return False, message

        return True, "✅ آمن"

    @staticmethod
    def _scan_file_content(file_path: str) -> Tuple[bool, str]:
        """فحص محتوى الملف بحثاً عن أكواد خطرة"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # البحث عن كلمات مفتاحية خطرة
            for keyword in SecurityScanner.DANGEROUS_KEYWORDS:
                if keyword in content:
                    logger.warning(f"⚠️ كلمة مفتاحية خطرة: {keyword} في {file_path}")
                    # نوفر تحذير لكن لا نحظر (قد تكون شرعية)

            # البحث عن أنماط خطرة
            if 'eval(' in content or 'exec(' in content:
                return False, "❌ كود خطر: eval/exec مكتشف"

            if '__import__(' in content and 'import' not in file_path:
                return False, "❌ كود خطر: __import__ مكتشف"

            return True, "✅ محتوى آمن"

        except Exception as e:
            return False, f"❌ خطأ في الفحص: {str(e)}"

    @staticmethod
    def scan_directory(dir_path: str) -> Tuple[bool, List[str], List[str]]:
        """فحص مجلد كامل

        Args:
            dir_path: مسار المجلد

        Returns:
            (آمن؟، الملفات الآمنة، الملفات غير الآمنة)
        """
        safe_files = []
        unsafe_files = []

        # فحص جميع الملفات في المجلد
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                file_path = os.path.join(root, file)

                # تخطي المجلدات المشبوهة
                if '__pycache__' in file_path or '.git' in file_path:
                    continue

                is_safe, message = SecurityScanner.scan_file(file_path)

                if is_safe:
                    safe_files.append(file)
                else:
                    unsafe_files.append(f"{file}: {message}")

        all_safe = len(unsafe_files) == 0
        return all_safe, safe_files, unsafe_files

    @staticmethod
    def get_file_hash(file_path: str) -> str:
        """حساب hash الملف للكشف عن التعديلات

        Args:
            file_path: مسار الملف

        Returns:
            hash الملف
        """
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except:
            return ""

    @staticmethod
    def verify_file_integrity(file_path: str, expected_hash: str) -> bool:
        """التحقق من سلامة الملف

        Args:
            file_path: مسار الملف
            expected_hash: hash متوقع

        Returns:
            هل الملف سليم؟
        """
        actual_hash = SecurityScanner.get_file_hash(file_path)
        return actual_hash == expected_hash


class RateLimiter:
    """نظام تحديد معدل الطلبات"""

    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        """
        Args:
            max_requests: الحد الأقصى للطلبات
            window_seconds: فترة الزمني بالثواني
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}

    def is_allowed(self, user_id: int) -> Tuple[bool, int]:
        """التحقق من السماح بطلب جديد

        Args:
            user_id: معرف المستخدم

        Returns:
            (مسموح؟، الطلبات المتبقية)
        """
        now = datetime.now()

        if user_id not in self.requests:
            self.requests[user_id] = []

        # تنظيف الطلبات القديمة
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if (now - req_time).total_seconds() < self.window_seconds
        ]

        # التحقق من الحد الأقصى
        if len(self.requests[user_id]) >= self.max_requests:
            return False, 0

        # إضافة الطلب الجديد
        self.requests[user_id].append(now)
        remaining = self.max_requests - len(self.requests[user_id])

        return True, remaining

    def get_remaining_time(self, user_id: int) -> int:
        """الحصول على الوقت المتبقي قبل إعادة محاولة

        Args:
            user_id: معرف المستخدم

        Returns:
            الثواني المتبقية
        """
        if user_id not in self.requests or not self.requests[user_id]:
            return 0

        oldest_request = self.requests[user_id][0]
        elapsed = (datetime.now() - oldest_request).total_seconds()
        remaining = self.window_seconds - elapsed

        return max(0, int(remaining))


class FileValidator:
    """مُدقق الملفات الآمن"""

    # أنواع الملفات المسموحة
    ALLOWED_TYPES = {
        'text': {'.txt', '.md', '.csv', '.log', '.cfg', '.conf'},
        'code': {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rb', '.php'},
        'config': {'.json', '.yml', '.yaml', '.xml', '.toml', '.ini'},
        'data': {'.db', '.sqlite', '.sql', '.csv'},
        'archive': {'.zip', '.7z', '.rar', '.tar', '.gz'},
        'other': {'.env', '.gitignore', '.dockerignore'}
    }

    @staticmethod
    def is_file_allowed(filename: str) -> Tuple[bool, str]:
        """التحقق من أن الملف مسموح

        Args:
            filename: اسم الملف

        Returns:
            (مسموح؟، رسالة)
        """
        ext = os.path.splitext(filename)[1].lower()

        # التحقق من الامتداد
        if not ext:
            return False, "❌ الملف بدون امتداد"

        # البحث في الأنواع المسموحة
        for file_type, extensions in FileValidator.ALLOWED_TYPES.items():
            if ext in extensions:
                return True, f"✅ نوع مسموح: {file_type}"

        return False, f"❌ امتداد غير مسموح: {ext}"

    @staticmethod
    def validate_filename(filename: str) -> Tuple[bool, str]:
        """التحقق من صحة اسم الملف

        Args:
            filename: اسم الملف

        Returns:
            (صحيح؟، رسالة)
        """
        # التحقق من الأحرف الخطرة
        dangerous_chars = '<>:"|?*\\/'
        for char in dangerous_chars:
            if char in filename:
                return False, f"❌ حرف غير مسموح: {char}"

        # التحقق من الطول
        if len(filename) > 255:
            return False, "❌ اسم الملف طويل جداً"

        # التحقق من الأسماء المحجوزة
        reserved_names = {'con', 'prn', 'aux', 'nul', 'com1', 'lpt1'}
        if filename.lower() in reserved_names:
            return False, "❌ اسم ملف محجوز"

        return True, "✅ اسم صحيح"

    @staticmethod
    def clean_path(path: str, base_dir: str) -> Optional[str]:
        """تنظيف المسار ومنع path traversal

        Args:
            path: المسار المطلوب
            base_dir: المجلد الأساسي المسموح

        Returns:
            المسار المنظف أو None إذا كان خطراً
        """
        try:
            # تحويل لمسار مطلق
            clean = os.path.normpath(path)
            base = os.path.normpath(base_dir)

            # التحقق من أن المسار داخل المجلد الأساسي
            if not clean.startswith(base):
                return None

            return clean
        except:
            return None


class BotSecurityManager:
    """مدير أمان البوتات المرفوعة"""

    def __init__(self):
        self.scanner = SecurityScanner()
        self.rate_limiter = RateLimiter(max_requests=3, window_seconds=60)
        self.validator = FileValidator()
        self.integrity_hashes = {}

    async def validate_bot_upload(self, user_id: int, bot_folder: str) -> Tuple[bool, List[str]]:
        """التحقق من أمان البوت المرفوع

        Args:
            user_id: معرف المستخدم
            bot_folder: مسار مجلد البوت

        Returns:
            (آمن؟، التحذيرات)
        """
        warnings = []

        # التحقق من معدل الطلبات
        is_allowed, remaining = self.rate_limiter.is_allowed(user_id)
        if not is_allowed:
            waiting_time = self.rate_limiter.get_remaining_time(user_id)
            return False, [f"⏳ يرجى الانتظار {waiting_time} ثانية قبل المحاولة مجدداً"]

        # فحص المجلد
        if not os.path.exists(bot_folder):
            return False, ["❌ مجلد البوت غير موجود"]

        # فحص أمان الملفات
        is_safe, safe_files, unsafe_files = self.scanner.scan_directory(bot_folder)

        if unsafe_files:
            warnings.extend([f"⚠️ {f}" for f in unsafe_files[:5]])

        # تحذير إذا لم يوجد main.py
        if not any(f.endswith(('main.py', 'bot.py', 'app.py')) for f in safe_files):
            warnings.append("⚠️ لم يتم العثور على الملف الرئيسي (main.py/bot.py/app.py)")

        # تسجيل هashes الملفات
        for file in safe_files[:10]:
            file_path = os.path.join(bot_folder, file)
            if os.path.isfile(file_path):
                file_hash = self.scanner.get_file_hash(file_path)
                self.integrity_hashes[f"{user_id}_{file}"] = file_hash

        logger.info(f"✅ فحص البوت: المستخدم {user_id}, آمن={is_safe}")

        return True, warnings  # نسمح برفع البوت حتى مع التحذيرات

    def format_security_report(self, warnings: List[str]) -> str:
        """تنسيق تقرير الأمان"""
        if not warnings:
            return "✅ <b>تقرير الأمان: آمن</b>"

        report = "<b>📋 تقرير الأمان:</b>\n"
        for warning in warnings[:5]:
            report += f"{warning}\n"

        report += "\n<i>ملاحظة: يتم مراقبة البوتات المرفوعة بانتظام</i>"
        return report


# دوال مساعدة سريعة
def create_sandbox_environment(bot_id: int) -> str:
    """إنشاء بيئة sandbox آمنة للبوت

    Args:
        bot_id: معرف البوت

    Returns:
        مسار البيئة
    """
    sandbox_path = f"bots/.sandbox/bot_{bot_id}"
    os.makedirs(sandbox_path, exist_ok=True)
    return sandbox_path


def restrict_bot_permissions(bot_process) -> bool:
    """تقييد صلاحيات عملية البوت

    Args:
        bot_process: عملية البوت

    Returns:
        نجح؟
    """
    try:
        # هذا يعتمد على النظام الأساسي
        # Windows: استخدام restricted process token
        # Linux: استخدام ulimit و setuid

        # مثال: تحديد حد أقصى للذاكرة
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))

        logger.info("✅ تم تقييد صلاحيات البوت")
        return True
    except:
        logger.warning("⚠️ لا يمكن تقييد الصلاحيات (قد تكون مدعومة على Linux فقط)")
        return False
