# ============================================================================
# نظام المساعدات والتنسيق المتقدم - NeurHostX V8.5
# ============================================================================
"""
أدوات متقدمة للنصوص والتنسيق مع دعم Markdown2
"""

import re
from typing import Optional, List, Dict
from html import escape

class MarkdownFormatter:
    """محرّك تنسيق Markdown2 مخصص لتيليجرام"""

    # أنماط Markdown2
    PATTERNS = {
        # عناوين
        'h1': (r'^# (.+)$', '**<b>{}</b>**'),
        'h2': (r'^## (.+)$', '<b>{}</b>'),
        'h3': (r'^### (.+)$', '<u>{}</u>'),

        # تنسيق نصوص
        'bold': (r'\*\*(.+?)\*\*', '<b>{}</b>'),
        'italic': (r'__(.+?)__', '<i>{}</i>'),
        'strikethrough': (r'~~(.+?)~~', '<s>{}</s>'),
        'code_inline': (r'`(.+?)`', '<code>{}</code>'),

        # قوائم
        'list_item': (r'^[-*+] (.+)$', '• {}'),

        # الروابط
        'link': (r'\[(.+?)\]\((.+?)\)', '<a href="{}">{}</a>'),

        # اقتباسات
        'quote': (r'^> (.+)$', '<i>"{}"</i>'),

        # جداول بسيطة
        'table': (r'\|(.+)\|', '│ {} │'),
    }

    @staticmethod
    def parse(text: str) -> str:
        """تحويل Markdown2 إلى HTML لتيليجرام"""
        lines = text.split('\n')
        result = []

        for line in lines:
            processed = line

            # معالجة العناوين
            h1_match = re.match(r'^# (.+)$', line)
            if h1_match:
                result.append(f"<b>╔ {h1_match.group(1)} ╗</b>")
                continue

            h2_match = re.match(r'^## (.+)$', line)
            if h2_match:
                result.append(f"<b>▸ {h2_match.group(1)}</b>")
                continue

            h3_match = re.match(r'^### (.+)$', line)
            if h3_match:
                result.append(f"<u>{h3_match.group(1)}</u>")
                continue

            # معالجة النص الغامق
            processed = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', processed)

            # معالجة النص المائل
            processed = re.sub(r'__(.+?)__', r'<i>\1</i>', processed)

            # معالجة الشطب
            processed = re.sub(r'~~(.+?)~~', r'<s>\1</s>', processed)

            # معالجة الكود
            processed = re.sub(r'`(.+?)`', r'<code>\1</code>', processed)

            # معالجة القوائم
            if re.match(r'^[-*+] ', processed):
                processed = re.sub(r'^[-*+] ', '• ', processed)

            # معالجة الاقتباسات
            if processed.startswith('> '):
                processed = '> ' + processed[2:]

            result.append(processed)

        return '\n'.join(result)

    @staticmethod
    def escape_html(text: str) -> str:
        """تجنب أحرف HTML الخاصة"""
        return escape(text)


class TextFormatter:
    """منسّق النصوص المتقدم"""

    @staticmethod
    def create_divider(char: str = '═', length: int = 40) -> str:
        """إنشاء فاصل"""
        return char * length

    @staticmethod
    def create_header(title: str, char: str = '═', length: int = 40) -> str:
        """إنشاء رأس قسم"""
        divider = char * length
        return f"{divider}\n{title}\n{divider}"

    @staticmethod
    def create_box(title: str, content: str) -> str:
        """إنشاء صندوق نص"""
        lines = content.split('\n')
        max_len = max(len(line) for line in lines) if lines else 0
        max_len = max(max_len, len(title))

        result = f"╔{'═' * (max_len + 2)}╗\n"
        result += f"║ {title.ljust(max_len)} ║\n"
        result += f"╠{'═' * (max_len + 2)}╣\n"

        for line in lines:
            result += f"║ {line.ljust(max_len)} ║\n"

        result += f"╚{'═' * (max_len + 2)}╝"
        return result

    @staticmethod
    def create_progress_bar(current: int, total: int, length: int = 10,
                           filled_char: str = '█', empty_char: str = '░') -> str:
        """إنشاء شريط تقدم"""
        if total == 0:
            return empty_char * length

        filled = int((current / total) * length)
        return (filled_char * filled) + (empty_char * (length - filled))

    @staticmethod
    def create_table(headers: List[str], rows: List[List[str]],
                    border: bool = True) -> str:
        """إنشاء جدول نصي"""
        col_widths = [len(h) for h in headers]

        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))

        # الرأس
        header_line = '│ ' + ' │ '.join(
            h.ljust(col_widths[i]) for i, h in enumerate(headers)
        ) + ' │'

        separator = '├' + '┼'.join('─' * (w + 2) for w in col_widths) + '┤'
        top_line = '┌' + '┬'.join('─' * (w + 2) for w in col_widths) + '┐'
        bottom_line = '└' + '┴'.join('─' * (w + 2) for w in col_widths) + '┘'

        result = top_line + '\n' + header_line + '\n' + separator + '\n'

        # الصفوف
        for row in rows:
            row_line = '│ ' + ' │ '.join(
                str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)
            ) + ' │'
            result += row_line + '\n'

        result += bottom_line
        return result

    @staticmethod
    def truncate(text: str, max_length: int, suffix: str = '...') -> str:
        """قطع النص إذا كان طويلاً"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix

    @staticmethod
    def wrap_text(text: str, width: int = 40) -> str:
        """لف النص عند عرض معين"""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            if current_length + len(word) + 1 <= width:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)

        if current_line:
            lines.append(' '.join(current_line))

        return '\n'.join(lines)

    @staticmethod
    def add_prefix_to_lines(text: str, prefix: str) -> str:
        """إضافة بادئة لكل سطر"""
        lines = text.split('\n')
        return '\n'.join(prefix + line for line in lines)

    @staticmethod
    def create_list(items: List[str], ordered: bool = False,
                   prefix: str = '') -> str:
        """إنشاء قائمة"""
        result = []
        for i, item in enumerate(items):
            if ordered:
                result.append(f"{prefix}{i + 1}. {item}")
            else:
                result.append(f"{prefix}• {item}")
        return '\n'.join(result)

    @staticmethod
    def highlight_code(code: str, language: str = '') -> str:
        """تحديد الكود (تنسيق بسيط)"""
        if language:
            return f"```{language}\n{code}\n```"
        return f"```\n{code}\n```"


class MessageBuilder:
    """بناء رسائل معقدة"""

    def __init__(self):
        self.parts = []

    def add_header(self, title: str) -> 'MessageBuilder':
        """إضافة رأس"""
        self.parts.append(f"<b>{'═' * 40}</b>")
        self.parts.append(f"<b>{title}</b>")
        self.parts.append(f"<b>{'═' * 40}</b>")
        return self

    def add_text(self, text: str) -> 'MessageBuilder':
        """إضافة نص"""
        self.parts.append(text)
        return self

    def add_empty_line(self) -> 'MessageBuilder':
        """إضافة سطر فارغ"""
        self.parts.append('')
        return self

    def add_divider(self) -> 'MessageBuilder':
        """إضافة فاصل"""
        self.parts.append('─' * 40)
        return self

    def add_section(self, title: str, content: str) -> 'MessageBuilder':
        """إضافة قسم"""
        self.parts.append(f"\n<b>{title}</b>:")
        self.parts.append(content)
        return self

    def add_list(self, items: List[str], emoji: str = '•') -> 'MessageBuilder':
        """إضافة قائمة"""
        for item in items:
            self.parts.append(f"{emoji} {item}")
        return self

    def build(self) -> str:
        """بناء الرسالة النهائية"""
        return '\n'.join(self.parts)


# دوال مساعدة سريعة
def format_bold(text: str) -> str:
    """تنسيق نص غامق (HTML)"""
    return f"<b>{text}</b>"


def format_italic(text: str) -> str:
    """تنسيق نص مائل (HTML)"""
    return f"<i>{text}</i>"


def format_code(text: str) -> str:
    """تنسيق كود (HTML)"""
    return f"<code>{text}</code>"


def format_link(text: str, url: str) -> str:
    """تنسيق رابط (HTML)"""
    return f'<a href="{url}">{text}</a>'


def format_mention(user_id: int) -> str:
    """تنسيق إشارة مستخدم"""
    return f'<a href="tg://user?id={user_id}">مستخدم</a>'


def create_emoji_list(items: List[str]) -> str:
    """إنشاء قائمة بأيقونات تلقائية"""
    emojis = ['🔵', '🟢', '🟣', '🟡', '🔴', '⭐', '✅', '❌', '⚠️', '💡']
    result = []
    for i, item in enumerate(items):
        emoji = emojis[i % len(emojis)]
        result.append(f"{emoji} {item}")
    return '\n'.join(result)
