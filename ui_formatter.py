# ============================================================================
# نظام التنسيق والواجهة المحسن - NeuroHost V8.5 Enhanced
# ============================================================================
"""
نظام تنسيق متقدم يوفر:
- رسائل بصيغة Markdown V2/HTML احترافية
- إيموجيات متناسقة وجذابة
- واجهة مستخدم سلسة وسهلة
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


class UIFormatter:
    """نظام التنسيق المحسن للواجهة"""

    # ═══════════════════════════════════════════════════════════════════════
    # الفواصل والعناصر البصرية
    # ═══════════════════════════════════════════════════════════════════════

    SEPARATOR_MAIN = "════════════════════════════════════════════"
    SEPARATOR_TITLE = "────────────────────────────────────────"
    SEPARATOR_LIGHT = "─" * 40
    SEPARATOR_DOT = "•" * 40
    SEPARATOR_STAR = "★" * 40

    # أيقونات الحالة
    ICONS = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️',
        'loading': '⏳',
        'clock': '⏰',
        'calendar': '📅',
        'user': '👤',
        'bot': '🤖',
        'star': '⭐',
        'fire': '🔥',
        'heart': '❤️',
        'arrow': '→',
        'checkmark': '✔️',
        'cross': '✘',
    }

    @staticmethod
    def format_title(text: str, emoji: str = "📋") -> str:
        """
        تنسيق عنوان الرسالة الرئيسي

        Args:
            text: نص العنوان
            emoji: الأيقونة

        Returns:
            العنوان المنسق
        """
        return (
            f"{emoji} <b>{text}</b>\n"
            f"{UIFormatter.SEPARATOR_MAIN}"
        )

    @staticmethod
    def format_section(title: str, content: str, emoji: str = "📌") -> str:
        """
        تنسيق قسم في الرسالة

        Args:
            title: عنوان القسم
            content: محتوى القسم
            emoji: الأيقونة

        Returns:
            القسم المنسق
        """
        return (
            f"\n{emoji} <b>{title}</b>\n"
            f"{UIFormatter.SEPARATOR_LIGHT}\n"
            f"{content}"
        )

    @staticmethod
    def format_list_item(icon: str, label: str, value: str = "", indent: int = 0) -> str:
        """
        تنسيق عنصر في قائمة

        Args:
            icon: الأيقونة
            label: اسم العنصر
            value: القيمة (اختياري)
            indent: المسافة البادئة

        Returns:
            العنصر المنسق
        """
        indent_str = "  " * indent
        if value:
            return f"{indent_str}{icon} <b>{label}:</b> <code>{value}</code>"
        return f"{indent_str}{icon} {label}"

    @staticmethod
    def format_status_bar(current: int, maximum: int, length: int = 10) -> str:
        """
        رسم شريط حالة نسبي

        Args:
            current: القيمة الحالية
            maximum: القيمة القصوى
            length: طول الشريط

        Returns:
            شريط الحالة
        """
        if maximum <= 0:
            percentage = 0
        else:
            percentage = (current / maximum) * 100

        filled = int((percentage / 100) * length)
        empty = length - filled

        bar = "█" * filled + "░" * empty
        return f"[{bar}] {percentage:.0f}%"

    @staticmethod
    def format_time_remaining(seconds: int) -> str:
        """
        تنسيق الوقت المتبقي بصيغة سهلة القراءة

        Args:
            seconds: الوقت بالثواني

        Returns:
            الوقت المنسق
        """
        if seconds <= 0:
            return "⏱️ انتهى الوقت"

        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        parts = []
        if days > 0:
            parts.append(f"{days} يوم" if days > 1 else "يوم واحد")
        if hours > 0:
            parts.append(f"{hours} ساعة" if hours > 1 else "ساعة واحدة")
        if minutes > 0 and days == 0:
            parts.append(f"{minutes} دقيقة" if minutes > 1 else "دقيقة واحدة")
        if secs > 0 and days == 0 and hours == 0:
            parts.append(f"{secs} ثانية")

        return " و".join(parts) if parts else "0 ثانية"

    @staticmethod
    def format_file_size(bytes_size: int) -> str:
        """
        تنسيق حجم الملف

        Args:
            bytes_size: الحجم بالبايت

        Returns:
            الحجم المنسق
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} TB"

    # ═══════════════════════════════════════════════════════════════════════
    # رسائل موحدة
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def format_success_message(action: str, details: str = "") -> str:
        """رسالة النجاح الموحدة"""
        msg = f"✅ <b>{action}</b>\n" + UIFormatter.SEPARATOR_LIGHT
        if details:
            msg += f"\n\n{details}"
        return msg

    @staticmethod
    def format_error_message(error: str, suggestion: str = "") -> str:
        """رسالة الخطأ الموحدة"""
        msg = f"❌ <b>خطأ</b>\n" + UIFormatter.SEPARATOR_LIGHT
        msg += f"\n\n{error}"
        if suggestion:
            msg += f"\n\n💡 <i>{suggestion}</i>"
        return msg

    @staticmethod
    def format_warning_message(warning: str, action: str = "") -> str:
        """رسالة التحذير الموحدة"""
        msg = f"⚠️ <b>تحذير</b>\n" + UIFormatter.SEPARATOR_LIGHT
        msg += f"\n\n{warning}"
        if action:
            msg += f"\n\n<i>الإجراء المقترح: {action}</i>"
        return msg

    @staticmethod
    def format_info_message(title: str, content: str) -> str:
        """رسالة المعلومات الموحدة"""
        return (
            f"ℹ️ <b>{title}</b>\n"
            f"{UIFormatter.SEPARATOR_LIGHT}\n\n"
            f"{content}"
        )

    # ═══════════════════════════════════════════════════════════════════════
    # بطاقات المستخدمين والبوتات
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def format_user_card(user_data: Dict) -> str:
        """
        تنسيق بطاقة بيانات المستخدم

        Args:
            user_data: بيانات المستخدم

        Returns:
            بطاقة المستخدم
        """
        msg = UIFormatter.format_title(f"👤 {user_data.get('username', 'مستخدم')}", "👤")

        msg += f"\n\n"
        msg += UIFormatter.format_list_item("🆔", "المعرف", str(user_data.get('user_id')))
        msg += "\n"
        msg += UIFormatter.format_list_item("📛", "الاسم", user_data.get('first_name', 'غير محدد'))
        msg += "\n"
        msg += UIFormatter.format_list_item("🎖️", "الدور", user_data.get('role', 'مستخدم'))
        msg += "\n"
        msg += UIFormatter.format_list_item("📊", "الحالة", user_data.get('status', 'معلق'))
        msg += "\n"
        msg += UIFormatter.format_list_item("📦", "الخطة", user_data.get('plan', 'مجاني'))

        return msg

    @staticmethod
    def format_bot_card(bot_data: Dict) -> str:
        """
        تنسيق بطاقة بيانات البوت

        Args:
            bot_data: بيانات البوت

        Returns:
            بطاقة البوت
        """
        msg = UIFormatter.format_title(f"🤖 {bot_data.get('name', 'بوت')}", "🤖")

        msg += f"\n\n"
        msg += UIFormatter.format_list_item("🆔", "المعرف", str(bot_data.get('id')))
        msg += "\n"
        msg += UIFormatter.format_list_item("⚙️", "الحالة", bot_data.get('status', 'متوقف'))
        msg += "\n"

        # شريط الوقت المتبقي
        remaining = bot_data.get('remaining_seconds', 0)
        total = bot_data.get('total_seconds', 1)
        status_bar = UIFormatter.format_status_bar(remaining, total)
        msg += f"\n⏱️ <b>الوقت المتبقي:</b> {status_bar}\n"
        msg += f"   {UIFormatter.format_time_remaining(remaining)}"

        # شريط الطاقة
        power = bot_data.get('power_remaining', 0)
        max_power = bot_data.get('power_max', 100)
        power_bar = UIFormatter.format_status_bar(power, max_power)
        msg += f"\n\n⚡ <b>الطاقة:</b> {power_bar}"

        return msg

    # ═══════════════════════════════════════════════════════════════════════
    # عرض الإحصائيات
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def format_statistics(stats: Dict) -> str:
        """
        تنسيق الإحصائيات

        Args:
            stats: قاموس الإحصائيات

        Returns:
            الإحصائيات المنسقة
        """
        msg = UIFormatter.format_title("📊 الإحصائيات", "📊")

        msg += f"\n\n"
        msg += UIFormatter.format_list_item("🤖", "إجمالي البوتات", str(stats.get('total_bots', 0)))
        msg += "\n"
        msg += UIFormatter.format_list_item("✅", "البوتات النشطة", str(stats.get('running_bots', 0)))
        msg += "\n"
        msg += UIFormatter.format_list_item("⏱️", "الوقت المستخدم", stats.get('used_time', 'غير محدد'))
        msg += "\n"
        msg += UIFormatter.format_list_item("🔄", "إعادة التشغيل", str(stats.get('restarts', 0)))

        return msg

    # ═══════════════════════════════════════════════════════════════════════
    # تنسيق الجداول والقوائم
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def format_table(headers: List[str], rows: List[List[str]], max_width: int = 50) -> str:
        """
        تنسيق جدول بصيغة نصية

        Args:
            headers: رؤوس الأعمدة
            rows: صفوف الجدول
            max_width: أقصى عرض للخانة

        Returns:
            الجدول المنسق
        """
        # حساب عرض كل عمود
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)[:max_width]))

        # بناء الجدول
        table = ""
        # الصف الأول (رأس الجدول)
        table += " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        table += "\n"
        table += "-+-".join("-" * w for w in col_widths)
        table += "\n"

        # باقي الصفوف
        for row in rows:
            formatted_row = []
            for i, cell in enumerate(row):
                cell_str = str(cell)[:max_width]
                formatted_row.append(cell_str.ljust(col_widths[i]))
            table += " | ".join(formatted_row)
            table += "\n"

        return f"<code>{table}</code>"

    # ═══════════════════════════════════════════════════════════════════════
    # معالجة الأخطاء الآمنة
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def escape_html(text: str) -> str:
        """تجنب الأحرف الخاصة في HTML"""
        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    @staticmethod
    def safe_format(text: str, **kwargs) -> str:
        """
        تنسيق آمن للنصوص

        Args:
            text: النص المراد تنسيقه
            **kwargs: المتغيرات

        Returns:
            النص المنسق بأمان
        """
        try:
            for key, value in kwargs.items():
                safe_value = UIFormatter.escape_html(str(value))
                text = text.replace(f"{{{key}}}", safe_value)
            return text
        except Exception as e:
            logger.error(f"خطأ في التنسيق الآمن: {e}")
            return text

    # ═══════════════════════════════════════════════════════════════════════
    # رسائل الترحيب والودّاع
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def welcome_message(first_name: str) -> str:
        """رسالة الترحيب"""
        return (
            f"👋 <b>مرحباً بك {first_name}!</b>\n\n"
            f"أهلاً بك في <b>NeurHostX V8.5</b> ⭐\n"
            f"منصة الاستضافة الذكية للبوتات!\n\n"
            f"{'═' * 40}\n\n"
            f"<i>ابدأ رحلتك بإضافة بوتك الأول 🚀</i>"
        )

    @staticmethod
    def goodbye_message() -> str:
        """رسالة الوداع"""
        return (
            "👋 <b>وداعاً!</b>\n\n"
            "شكراً لاستخدامك NeurHostX 💖\n\n"
            "نتمنى أن نراك قريباً! 🚀"
        )
