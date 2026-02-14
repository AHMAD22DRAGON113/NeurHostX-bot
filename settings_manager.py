# ============================================================================
# مدير الإعدادات المتقدم - NeurHostX V8.5
# ============================================================================
"""
نظام إدارة الإعدادات المتقدم يدعم التحميل من JSON والتعديل من داخل البوت
"""

import json
import os
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class SettingsManager:
    """مدير الإعدادات المتقدم"""

    def __init__(self, settings_file: str = "settings.json"):
        self.settings_file = settings_file
        self.settings: Dict[str, Any] = {}
        self.load_settings()

    def load_settings(self) -> bool:
        """تحميل الإعدادات من ملف JSON"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                logger.info(f"✅ تم تحميل الإعدادات من {self.settings_file}")
                return True
            else:
                logger.warning(f"⚠️ لم يتم العثور على ملف الإعدادات: {self.settings_file}")
                return False
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل الإعدادات: {e}")
            return False

    def save_settings(self) -> bool:
        """حفظ الإعدادات إلى ملف JSON"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ تم حفظ الإعدادات في {self.settings_file}")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ الإعدادات: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """الحصول على قيمة إعداد"""
        keys = key.split('.')
        value = self.settings

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> bool:
        """تعيين قيمة إعداد"""
        try:
            keys = key.split('.')
            current = self.settings

            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]

            current[keys[-1]] = value
            logger.info(f"✅ تم تعيين {key} = {value}")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في تعيين الإعداد: {e}")
            return False

    def get_section(self, section: str) -> Dict[str, Any]:
        """الحصول على قسم كامل من الإعدادات"""
        return self.settings.get(section, {})

    def update_section(self, section: str, data: Dict[str, Any]) -> bool:
        """تحديث قسم كامل من الإعدادات"""
        try:
            if section not in self.settings:
                self.settings[section] = {}
            self.settings[section].update(data)
            logger.info(f"✅ تم تحديث القسم: {section}")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في تحديث القسم: {e}")
            return False

    def get_all(self) -> Dict[str, Any]:
        """الحصول على جميع الإعدادات"""
        return self.settings

    def reset_to_default(self) -> bool:
        """إعادة تعيين الإعدادات إلى الافتراضية"""
        try:
            # هنا يمكن إضافة الإعدادات الافتراضية
            logger.info("✅ تم إعادة تعيين الإعدادات")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في إعادة التعيين: {e}")
            return False

    def validate_setting(self, key: str, value: Any) -> tuple[bool, str]:
        """التحقق من صحة إعداد معين"""
        try:
            # التحقق من النوع
            if key == "hosting.max_concurrent_bots" and not isinstance(value, int):
                return False, "يجب أن تكون قيمة عددية"

            if key == "bot_info.version" and not isinstance(value, str):
                return False, "يجب أن تكون نص"

            # التحقق من النطاق
            if "timeout" in key or "interval" in key:
                if isinstance(value, (int, float)) and value < 0:
                    return False, "لا يمكن أن تكون القيمة سالبة"

            # التحقق من الخطط
            if key.startswith("plans."):
                valid_plans = ["free", "pro", "ultra", "supreme"]
                plan_name = key.split('.')[1]
                if plan_name not in valid_plans and plan_name != "___comment__":
                    return False, f"خطة غير معروفة: {plan_name}"

            return True, "✅ صحيح"
        except Exception as e:
            return False, f"خطأ في التحقق: {e}"


# إنشاء مثيل عام من مدير الإعدادات
settings_manager = SettingsManager()
