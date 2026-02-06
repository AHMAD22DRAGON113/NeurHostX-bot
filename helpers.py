# ============================================================================
# وظائف مساعدة - NeuroHost V8 Enhanced
# ============================================================================

import html
import re
from datetime import datetime, timezone
from pathlib import Path
from config import UI_CONFIG

# ═══════════════════════════════════════════════════════════════════════════
# تحويل الوقت
# ═══════════════════════════════════════════════════════════════════════════

def seconds_to_human(s, detailed=False):
    """تحويل الثواني إلى صيغة يمكن قراءتها"""
    if s is None or s <= 0:
        return "انتهى ❌"
    
    s = int(s)
    days, remainder = divmod(s, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    
    if days > 0:
        parts.append(f"{days}ي")
    if hours > 0:
        parts.append(f"{hours}س")
    if minutes > 0:
        parts.append(f"{minutes}د")
    if seconds > 0 and not parts:
        parts.append(f"{seconds}ث")
    
    if detailed and len(parts) < 2:
        if hours > 0 and minutes > 0:
            parts.append(f"{minutes}د")
    
    return " ".join(parts) if parts else "< 1 ثانية"

def seconds_to_full(s):
    """تحويل الثواني إلى صيغة كاملة"""
    if s is None or s <= 0:
        return "0 ثانية"
    
    s = int(s)
    days, remainder = divmod(s, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    
    if days > 0:
        parts.append(f"{days} يوم")
    if hours > 0:
        parts.append(f"{hours} ساعة")
    if minutes > 0:
        parts.append(f"{minutes} دقيقة")
    if seconds > 0:
        parts.append(f"{seconds} ثانية")
    
    return " و ".join(parts) if parts else "0 ثانية"

# ═══════════════════════════════════════════════════════════════════════════
# شريط التقدم
# ═══════════════════════════════════════════════════════════════════════════

def render_bar(percent, length=None):
    """رسم شريط التقدم"""
    if length is None:
        length = UI_CONFIG.get('bar_length', 10)
    
    try:
        p = max(0, min(100, float(percent)))
    except (ValueError, TypeError):
        p = 0
    
    filled = int((p / 100) * length)
    empty = length - filled
    
    bar = '█' * filled + '░' * empty
    
    return f"[{bar}] {p:.0f}%"

def render_progress(current, total, length=10):
    """رسم شريط تقدم بناءً على القيم"""
    if total <= 0:
        return render_bar(0, length)
    percent = (current / total) * 100
    return render_bar(percent, length)

# ═══════════════════════════════════════════════════════════════════════════
# معالجة النصوص
# ═══════════════════════════════════════════════════════════════════════════

def safe_html_escape(text):
    """تحويل النص الآمن لـ HTML"""
    if text is None:
        return ""
    return html.escape(str(text))

def truncate_text(text, max_length=100, suffix="..."):
    """قص النص الطويل"""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def clean_filename(filename):
    """تنظيف اسم الملف"""
    if not filename:
        return "unnamed"
    # إزالة الأحرف غير المسموحة
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # إزالة المسافات المتعددة
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned[:255] if len(cleaned) > 255 else cleaned

# ═══════════════════════════════════════════════════════════════════════════
# معالجة الملفات
# ═══════════════════════════════════════════════════════════════════════════

def get_file_size(path):
    """الحصول على حجم الملف بصيغة قابلة للقراءة"""
    try:
        if isinstance(path, str):
            path = Path(path)
        size = path.stat().st_size
        return format_size(size)
    except (OSError, ValueError, AttributeError):
        return "غير معروف"

def format_size(size_bytes):
    """تنسيق الحجم بالبايت"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def get_file_icon(filename: str) -> str:
    """الحصول على أيقونة الملف"""
    if not filename:
        return '📄'
    
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    icons = {
        'py': '🐍',
        'js': '📜',
        'json': '📋',
        'txt': '📄',
        'md': '📝',
        'html': '🌐',
        'css': '🎨',
        'yml': '⚙️',
        'yaml': '⚙️',
        'env': '🔐',
        'log': '📜',
        'db': '🗄️',
        'sql': '🗄️',
        'zip': '📦',
        'tar': '📦',
        'gz': '📦',
        'png': '🖼️',
        'jpg': '🖼️',
        'jpeg': '🖼️',
        'gif': '🖼️',
        'mp3': '🎵',
        'mp4': '🎬',
        'pdf': '📕',
        'doc': '📘',
        'docx': '📘',
    }
    
    return icons.get(ext, '📄')

def is_text_file(filename: str) -> bool:
    """التحقق مما إذا كان الملف نصي"""
    text_extensions = {
        'py', 'js', 'json', 'txt', 'md', 'html', 'css', 'yml', 'yaml',
        'env', 'log', 'sql', 'cfg', 'ini', 'sh', 'bat', 'xml', 'csv'
    }
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    return ext in text_extensions

# ═══════════════════════════════════════════════════════════════════════════
# الوقت والتاريخ
# ═══════════════════════════════════════════════════════════════════════════

def get_current_time():
    """الحصول على الوقت الحالي بتوقيت UTC"""
    return datetime.now(timezone.utc).isoformat()

def format_datetime(dt_string):
    """تنسيق التاريخ والوقت"""
    if not dt_string:
        return "غير معروف"
    try:
        if isinstance(dt_string, str):
            dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        else:
            dt = dt_string
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return str(dt_string)[:16] if dt_string else "غير معروف"

def time_ago(dt_string):
    """حساب الوقت المنقضي"""
    if not dt_string:
        return "غير معروف"
    try:
        if isinstance(dt_string, str):
            dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        else:
            dt = dt_string
        
        now = datetime.now(timezone.utc)
        diff = now - dt
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "الآن"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"منذ {minutes} دقيقة"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"منذ {hours} ساعة"
        else:
            days = int(seconds / 86400)
            return f"منذ {days} يوم"
    except:
        return "غير معروف"

# ═══════════════════════════════════════════════════════════════════════════
# التحقق من الصحة
# ═══════════════════════════════════════════════════════════════════════════

def validate_token(token: str) -> bool:
    """التحقق من صحة توكن تيليجرام"""
    if not token:
        return False
    pattern = r'^[0-9]{8,10}:[a-zA-Z0-9_-]{35,}$'
    return bool(re.match(pattern, token))

def extract_token_from_code(content: str) -> str:
    """استخراج التوكن من كود Python"""
    if not content:
        return None
    
    patterns = [
        r'["\']([0-9]{8,10}:[a-zA-Z0-9_-]{35,})["\']',
        r'TOKEN\s*=\s*["\']([0-9]{8,10}:[a-zA-Z0-9_-]{35,})["\']',
        r'BOT_TOKEN\s*=\s*["\']([0-9]{8,10}:[a-zA-Z0-9_-]{35,})["\']',
        r'TELEGRAM_BOT_TOKEN\s*=\s*["\']([0-9]{8,10}:[a-zA-Z0-9_-]{35,})["\']',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(1)
    
    # بحث عام عن نمط التوكن
    general_pattern = r'[0-9]{8,10}:[a-zA-Z0-9_-]{35,}'
    match = re.search(general_pattern, content)
    if match:
        return match.group(0)
    
    return None

def is_safe_path(base_path: Path, check_path: Path) -> bool:
    """التحقق من أمان المسار (منع التجاوز)"""
    try:
        base = base_path.resolve()
        check = check_path.resolve()
        return str(check).startswith(str(base))
    except (OSError, ValueError, AttributeError):
        return False

# ═══════════════════════════════════════════════════════════════════════════
# تنسيق الرسائل
# ═══════════════════════════════════════════════════════════════════════════

def format_bot_status(status: str, sleep_mode: bool = False) -> tuple:
    """تنسيق حالة البوت"""
    if sleep_mode:
        return "😴", "وضع السكون"
    elif status == "running":
        return "🟢", "يعمل"
    elif status == "stopped":
        return "🔴", "متوقف"
    elif status == "error":
        return "❌", "خطأ"
    else:
        return "⚪", "غير معروف"

def format_user_status(status: str) -> tuple:
    """تنسيق حالة المستخدم"""
    statuses = {
        'approved': ('✅', 'معتمد'),
        'pending': ('⏳', 'معلق'),
        'blocked': ('🚫', 'محظور'),
    }
    return statuses.get(status, ('❓', 'غير معروف'))

def format_log_type(log_type: str) -> str:
    """تنسيق نوع السجل"""
    icons = {
        'INFO': 'ℹ️',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🔴',
        'DEBUG': '🔍',
        'SUCCESS': '✅',
    }
    return icons.get(log_type, '📝')

# ═══════════════════════════════════════════════════════════════════════════
# أدوات متنوعة
# ═══════════════════════════════════════════════════════════════════════════

def parse_callback_data(data: str, expected_parts: int = 2) -> list:
    """تحليل بيانات callback بشكل آمن"""
    if not data:
        return [None] * expected_parts
    
    parts = data.split("_")
    
    # إضافة قيم None للأجزاء الناقصة
    while len(parts) < expected_parts:
        parts.append(None)
    
    return parts

def get_bot_id_from_callback(data: str) -> int:
    """استخراج bot_id من callback data"""
    try:
        parts = data.split("_")
        # البحث عن أول رقم في الأجزاء
        for part in parts[1:]:
            if part and part.isdigit():
                return int(part)
        return None
    except (ValueError, TypeError, AttributeError, IndexError):
        return None

def generate_unique_folder(prefix: str, user_id: int) -> str:
    """إنشاء اسم مجلد فريد"""
    import time
    timestamp = int(time.time())
    return f"{prefix}_{user_id}_{timestamp}"
