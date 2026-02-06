# ============================================================================
# نظام إدارة المحتويات المحسّن - NeurHostX V8.5
# ============================================================================
"""
إدارة الأسئلة الشائعة والدليل المفصل مع دعم Markdown2
"""

import json
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class HelpContentManager:
    """مدير محتويات المساعدة والأسئلة الشائعة"""

    def __init__(self, help_file: str = "help_content.json"):
        self.help_file = help_file
        self.content: Dict = {}
        self.load_content()

    def load_content(self) -> bool:
        """تحميل محتويات المساعدة من ملف JSON"""
        try:
            if Path(self.help_file).exists():
                with open(self.help_file, 'r', encoding='utf-8') as f:
                    self.content = json.load(f)
                logger.info(f"✅ تم تحميل محتويات المساعدة من {self.help_file}")
                return True
            else:
                logger.warning(f"⚠️ لم يتم العثور على ملف المحتويات: {self.help_file}")
                return False
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل المحتويات: {e}")
            return False

    def save_content(self) -> bool:
        """حفظ محتويات المساعدة إلى ملف JSON"""
        try:
            with open(self.help_file, 'w', encoding='utf-8') as f:
                json.dump(self.content, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ تم حفظ المحتويات في {self.help_file}")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ المحتويات: {e}")
            return False

    # ===================================================================
    # وظائف الأسئلة الشائعة
    # ===================================================================

    def get_all_faq(self) -> List[Dict]:
        """الحصول على جميع الأسئلة الشائعة"""
        return self.content.get('faq', [])

    def get_faq_by_id(self, faq_id: int) -> Optional[Dict]:
        """الحصول على سؤال شائع برقمه"""
        for item in self.get_all_faq():
            if item['id'] == faq_id:
                return item
        return None

    def get_faq_by_category(self, category: str) -> List[Dict]:
        """الحصول على أسئلة شائعة من فئة معينة"""
        return [
            faq for faq in self.get_all_faq()
            if faq.get('category') == category
        ]

    def search_faq(self, query: str) -> List[Dict]:
        """البحث في الأسئلة الشائعة"""
        query = query.lower()
        results = []

        for faq in self.get_all_faq():
            if (query in faq['question'].lower() or
                query in faq['answer'].lower()):
                results.append(faq)

        return results

    def get_faq_categories(self) -> List[str]:
        """الحصول على جميع الفئات المتاحة"""
        categories = set()
        for faq in self.get_all_faq():
            if 'category' in faq:
                categories.add(faq['category'])
        return sorted(list(categories))

    def format_faq(self, faq: Dict) -> str:
        """تنسيق سؤال وجواب"""
        return (
            f"<b>س: {faq.get('question', '')}</b>\n\n"
            f"{faq.get('answer', '')}\n\n"
            f"<i>الفئة: {faq.get('category', 'عام')}</i>"
        )

    def format_faq_brief(self, faq: Dict) -> str:
        """تنسيق مختصر للسؤال والجواب"""
        return f"<b>س:</b> {faq.get('question', '')[:50]}..."

    def add_faq(self, question: str, answer: str, category: str = "عام") -> bool:
        """إضافة سؤال شائع جديد"""
        try:
            if 'faq' not in self.content:
                self.content['faq'] = []

            faq_id = max([f.get('id', 0) for f in self.content['faq']], default=0) + 1

            new_faq = {
                'id': faq_id,
                'question': question,
                'answer': answer,
                'category': category
            }

            self.content['faq'].append(new_faq)
            logger.info(f"✅ تم إضافة سؤال شائع جديد (ID: {faq_id})")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة السؤال: {e}")
            return False

    def edit_faq(self, faq_id: int, question: Optional[str] = None,
                 answer: Optional[str] = None, category: Optional[str] = None) -> bool:
        """تعديل سؤال شائع"""
        try:
            for faq in self.content.get('faq', []):
                if faq['id'] == faq_id:
                    if question:
                        faq['question'] = question
                    if answer:
                        faq['answer'] = answer
                    if category:
                        faq['category'] = category
                    logger.info(f"✅ تم تعديل السؤال (ID: {faq_id})")
                    return True
            return False
        except Exception as e:
            logger.error(f"❌ خطأ في تعديل السؤال: {e}")
            return False

    def delete_faq(self, faq_id: int) -> bool:
        """حذف سؤال شائع"""
        try:
            self.content['faq'] = [
                f for f in self.content.get('faq', [])
                if f['id'] != faq_id
            ]
            logger.info(f"✅ تم حذف السؤال (ID: {faq_id})")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في حذف السؤال: {e}")
            return False

    # ===================================================================
    # وظائف الدليل المفصل
    # ===================================================================

    def get_detailed_guide(self) -> Dict:
        """الحصول على الدليل المفصل كاملاً"""
        return self.content.get('detailed_guide', {})

    def get_guide_introduction(self) -> str:
        """الحصول على مقدمة الدليل"""
        guide = self.get_detailed_guide()
        return guide.get('introduction', '')

    def get_guide_sections(self) -> List[Dict]:
        """الحصول على جميع أقسام الدليل"""
        guide = self.get_detailed_guide()
        return guide.get('sections', [])

    def get_guide_section(self, section_num: int) -> Optional[Dict]:
        """الحصول على قسم محدد من الدليل"""
        sections = self.get_guide_sections()
        if 0 <= section_num < len(sections):
            return sections[section_num]
        return None

    def search_guide(self, query: str) -> List[Dict]:
        """البحث في الدليل المفصل"""
        query = query.lower()
        results = []

        for section in self.get_guide_sections():
            if (query in section.get('title', '').lower() or
                query in section.get('content', '').lower()):
                results.append(section)

        return results

    def format_guide_section(self, section: Dict) -> str:
        """تنسيق قسم من الدليل"""
        return (
            f"<b>{section.get('title', '')}</b>\n\n"
            f"{section.get('content', '')}"
        )

    def format_guide_menu(self) -> str:
        """تنسيق قائمة الدليل المفصل"""
        sections = self.get_guide_sections()
        menu = "📚 <b>أقسام الدليل المفصل</b>\n\n"

        for i, section in enumerate(sections, 1):
            title = section.get('title', 'بدون عنوان')
            menu += f"{i}️⃣ {title}\n"

        return menu

    def add_guide_section(self, title: str, content: str) -> bool:
        """إضافة قسم جديد للدليل"""
        try:
            if 'detailed_guide' not in self.content:
                self.content['detailed_guide'] = {'sections': []}

            new_section = {
                'title': title,
                'content': content
            }

            self.content['detailed_guide']['sections'].append(new_section)
            logger.info(f"✅ تم إضافة قسم جديد: {title}")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة القسم: {e}")
            return False

    def edit_guide_section(self, section_num: int, title: Optional[str] = None,
                          content: Optional[str] = None) -> bool:
        """تعديل قسم من الدليل"""
        try:
            sections = self.content.get('detailed_guide', {}).get('sections', [])
            if 0 <= section_num < len(sections):
                if title:
                    sections[section_num]['title'] = title
                if content:
                    sections[section_num]['content'] = content
                logger.info(f"✅ تم تعديل القسم رقم {section_num + 1}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ خطأ في تعديل القسم: {e}")
            return False

    def delete_guide_section(self, section_num: int) -> bool:
        """حذف قسم من الدليل"""
        try:
            sections = self.content.get('detailed_guide', {}).get('sections', [])
            if 0 <= section_num < len(sections):
                sections.pop(section_num)
                logger.info(f"✅ تم حذف القسم رقم {section_num + 1}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ خطأ في حذف القسم: {e}")
            return False

    # ===================================================================
    # وظائف عامة
    # ===================================================================

    def get_stats(self) -> Dict:
        """الحصول على إحصائيات المحتويات"""
        return {
            'total_faq': len(self.get_all_faq()),
            'faq_categories': len(self.get_faq_categories()),
            'guide_sections': len(self.get_guide_sections()),
            'categories': self.get_faq_categories()
        }

    def format_stats(self) -> str:
        """تنسيق إحصائيات المحتويات"""
        stats = self.get_stats()
        return (
            f"📊 <b>إحصائيات المحتويات</b>\n\n"
            f"❓ أسئلة شائعة: {stats['total_faq']}\n"
            f"📚 أقسام الدليل: {stats['guide_sections']}\n"
            f"🏷️ الفئات: {stats['faq_categories']}\n\n"
            f"الفئات: {', '.join(stats['categories'])}"
        )


# إنشاء مثيل عام من مدير المحتويات
help_manager = HelpContentManager()
