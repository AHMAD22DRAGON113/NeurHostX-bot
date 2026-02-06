# ============================================================================
# نظام الإشعارات الذكي - NeuroHost V8.5 Enhanced
# ============================================================================
"""
نظام إشعارات متقدم مع:
- رسائل تسويقية جذابة
- جدولة ذكية
- تحليل التفاعل
"""

import logging
import random
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class NotificationCategory(Enum):
    """فئات الإشعارات"""
    ENGAGEMENT = "engagement"        # التفاعل والعودة
    PROMOTION = "promotion"          # عروض ترويجية
    UPDATE = "update"                # تحديثات النظام
    WARNING = "warning"              # تحذيرات
    ACHIEVEMENT = "achievement"      # إنجازات
    MAINTENANCE = "maintenance"      # صيانة


class SmartNotifications:
    """نظام الإشعارات الذكي"""

    # ═══════════════════════════════════════════════════════════════════════
    # رسائل الإشعارات - متنوعة وجذابة
    # ═══════════════════════════════════════════════════════════════════════

    ENGAGEMENT_MESSAGES = [
        {
            'title': '🚀 هيا بنا لنبدأ!',
            'message': 'لم ترسل أي رسالة لفترة طويلة. هل كل شيء بخير?\n\nتفقد بوتاتك الآن واستمع في تطويرها! 🤖',
            'emoji': '🚀'
        },
        {
            'title': '⚡ حان وقت الإنتاجية',
            'message': 'تابع مشاريعك! استعرض آخر تحديثاتك وتابع أداء بوتاتك 💪',
            'emoji': '⚡'
        },
        {
            'title': '🎯 هدف جديد ينتظرك',
            'message': 'هل تفكر في نشر بوت جديد؟ لدينا كل الأدوات التي تحتاجها! 🛠️',
            'emoji': '🎯'
        },
        {
            'title': '💡 نصيحة مفيدة',
            'message': 'هل تعلم أنه يمكنك تنزيل جميع ملفات بوتك مرة واحدة؟\n\nاستخدم "تحميل الكل" 📥',
            'emoji': '💡'
        },
        {
            'title': '🌟 لقد كنت غائباً',
            'message': 'نحن نفتقدك! عد وتفقد آخر الأخبار والتحديثات 👋',
            'emoji': '🌟'
        },
        {
            'title': '🎪 اكتشف الجديد',
            'message': 'تحديثات جديدة في لوحة التحكم! جرب الميزات الجديدة الآن ✨',
            'emoji': '🎪'
        }
    ]

    PROMOTION_MESSAGES = [
        {
            'title': '🎁 عرض خاص لك',
            'message': 'انضم الآن وحصل على خطة Pro مع خصم 20%! 🔥\n\n⏰ العرض محدود الوقت',
            'emoji': '🎁'
        },
        {
            'title': '👑 خطة Supreme منتظرة',
            'message': 'تريد بوتات غير محدودة ووقت لا نهائي؟\n\n👑 Supreme هي الإجابة! 🌟',
            'emoji': '👑'
        },
        {
            'title': '🚀 ترقية الآن',
            'message': 'احصل على 5 بوتات إضافية!\n\nترقية خطتك واستمتع بمميزات جديدة 🎉',
            'emoji': '🚀'
        },
        {
            'title': '⭐ تبرعاتك مهمة',
            'message': 'ساعد في تطوير المشروع! تبرع بنجم واحد فقط 💝\n\nكل نجم يساعد كثيراً!',
            'emoji': '⭐'
        },
        {
            'title': '💰 خصم العملاء الدائمين',
            'message': 'شكراً لولائك! استمتع بخصم خاص على الخطط القادمة 🎊',
            'emoji': '💰'
        },
        {
            'title': '🎯 عرض محدود',
            'message': 'حتى نهاية الأسبوع فقط:\n\nUltra Plan بسعر Pro! 🔔',
            'emoji': '🎯'
        }
    ]

    WARNING_MESSAGES = [
        {
            'title': '⚠️ الوقت ينفد!',
            'message': 'لديك أقل من 24 ساعة متبقية لبوتاتك 😓\n\nأضف وقتاً الآن! ⏰',
            'emoji': '⚠️'
        },
        {
            'title': '🔔 تنبيه مهم',
            'message': 'بعض بوتاتك توشك على التوقف قريباً 🛑\n\nأضف وقتاً للاستمرار!',
            'emoji': '🔔'
        },
        {
            'title': '😴 بوت نائم',
            'message': 'أحد بوتاتك في وضع السكون 😴\n\nأضف وقتاً لاستيقاظه! ☀️',
            'emoji': '😴'
        }
    ]

    UPDATE_MESSAGES = [
        {
            'title': '🆕 تحديث جديد!',
            'message': 'تم إضافة ميزات جديدة للنظام! 🎉\n\n✨ استكشف الجديد الآن',
            'emoji': '🆕'
        },
        {
            'title': '🔧 تحسينات الأداء',
            'message': 'قمنا بتحسين سرعة النظام! ⚡\n\nستلاحظ الفرق فوراً 🚀',
            'emoji': '🔧'
        },
        {
            'title': '🐛 تم إصلاح الأخطاء',
            'message': 'قمنا بإصلاح عدة مشاكل في التطبيق 🛠️\n\nشكراً للإبلاغ!',
            'emoji': '🐛'
        }
    ]

    ACHIEVEMENT_MESSAGES = [
        {
            'title': '🏆 إنجاز رائع!',
            'message': 'لقد وصلت إلى 5 بوتات! 🎉\n\nأنت نجم! ⭐',
            'emoji': '🏆'
        },
        {
            'title': '🌟 مستخدم مخلص',
            'message': 'أنت معنا منذ 30 يوماً! 🎊\n\nشكراً على الثقة والدعم!',
            'emoji': '🌟'
        },
        {
            'title': '💪 قوة البوت',
            'message': 'بوتك يعمل بدون توقف لمدة أسبوع! 💪\n\nاستمر بالتميز!',
            'emoji': '💪'
        }
    ]

    # ═══════════════════════════════════════════════════════════════════════
    # إدارة الإشعارات
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_random_notification(category: Optional[NotificationCategory] = None) -> Dict:
        """
        الحصول على إشعار عشوائي من فئة معينة أو عشوائي

        Args:
            category: فئة الإشعار (اختياري)

        Returns:
            بيانات الإشعار
        """
        try:
            if category == NotificationCategory.ENGAGEMENT:
                return random.choice(SmartNotifications.ENGAGEMENT_MESSAGES)
            elif category == NotificationCategory.PROMOTION:
                return random.choice(SmartNotifications.PROMOTION_MESSAGES)
            elif category == NotificationCategory.WARNING:
                return random.choice(SmartNotifications.WARNING_MESSAGES)
            elif category == NotificationCategory.UPDATE:
                return random.choice(SmartNotifications.UPDATE_MESSAGES)
            elif category == NotificationCategory.ACHIEVEMENT:
                return random.choice(SmartNotifications.ACHIEVEMENT_MESSAGES)

            # إذا لم تحدد فئة، اختر عشوائياً من جميع الرسائل
            all_messages = (
                SmartNotifications.ENGAGEMENT_MESSAGES +
                SmartNotifications.PROMOTION_MESSAGES +
                SmartNotifications.WARNING_MESSAGES +
                SmartNotifications.UPDATE_MESSAGES +
                SmartNotifications.ACHIEVEMENT_MESSAGES
            )
            return random.choice(all_messages)

        except Exception as e:
            logger.error(f"❌ خطأ في جلب الإشعار: {e}")
            return {}

    @staticmethod
    def schedule_notification(
        db, user_id: int, notification_data: Dict,
        send_after_minutes: int = 0
    ) -> Tuple[bool, str]:
        """
        جدولة إرسال إشعار

        Args:
            db: كائن قاعدة البيانات
            user_id: معرف المستخدم
            notification_data: بيانات الإشعار
            send_after_minutes: بعد كم دقيقة يتم الإرسال

        Returns:
            (نجاح العملية، الرسالة)
        """
        try:
            scheduled_time = datetime.now(timezone.utc) + timedelta(minutes=send_after_minutes)

            notification_record = {
                'user_id': user_id,
                'title': notification_data.get('title', '📢 إشعار'),
                'message': notification_data.get('message', ''),
                'emoji': notification_data.get('emoji', '📢'),
                'scheduled_at': scheduled_time.isoformat(),
                'created_at': datetime.now(timezone.utc).isoformat(),
                'sent': False
            }

            db.set_setting(
                f"scheduled_notification_{user_id}_{datetime.now().timestamp()}",
                str(notification_record)
            )

            logger.info(f"✅ تم جدولة إشعار للمستخدم {user_id}")
            return True, "✅ تم جدولة الإشعار"

        except Exception as e:
            logger.error(f"❌ خطأ في جدولة الإشعار: {e}")
            return False, f"❌ حدث خطأ: {str(e)}"

    # ═══════════════════════════════════════════════════════════════════════
    # تحليل التفاعل
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def analyze_user_engagement(db, user_id: int) -> Dict:
        """
        تحليل مستوى تفاعل المستخدم

        Args:
            db: كائن قاعدة البيانات
            user_id: معرف المستخدم

        Returns:
            بيانات التحليل
        """
        try:
            user = db.get_user(user_id)
            if not user:
                return {}

            last_active = user[14]  # last_active column
            joined_at = user[10]    # joined_at column

            # حساب أيام عدم النشاط
            if last_active:
                try:
                    last_active_date = datetime.fromisoformat(last_active)
                    inactive_days = (datetime.now(timezone.utc) - last_active_date).days
                except:
                    inactive_days = 0
            else:
                inactive_days = 999

            # حساب مدة العضوية
            try:
                joined_date = datetime.fromisoformat(joined_at)
                membership_days = (datetime.now(timezone.utc) - joined_date).days
            except:
                membership_days = 0

            # تحليل النشاط
            engagement_score = 0

            if inactive_days == 0:
                engagement_score = 100
            elif inactive_days <= 7:
                engagement_score = 80
            elif inactive_days <= 30:
                engagement_score = 60
            elif inactive_days <= 90:
                engagement_score = 40
            else:
                engagement_score = 20

            analysis = {
                'engagement_score': engagement_score,
                'inactive_days': inactive_days,
                'membership_days': membership_days,
                'is_active': inactive_days <= 7,
                'is_returning': inactive_days > 7,
                'is_dormant': inactive_days > 30,
                'needs_engagement': inactive_days > 14
            }

            return analysis

        except Exception as e:
            logger.warning(f"خطأ في تحليل التفاعل: {e}")
            return {}

    @staticmethod
    def get_notification_preference(db, user_id: int) -> bool:
        """
        الحصول على تفضيل الإشعارات للمستخدم

        Args:
            db: كائن قاعدة البيانات
            user_id: معرف المستخدم

        Returns:
            هل الإشعارات مفعلة
        """
        try:
            user = db.get_user(user_id)
            if not user:
                return True

            notifications_enabled = user[11]  # notifications_enabled column
            return bool(notifications_enabled)

        except:
            return True

    # ═══════════════════════════════════════════════════════════════════════
    # جودة الإشعارات
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def format_notification_message(notification_data: Dict) -> str:
        """
        تنسيق رسالة الإشعار بصيغة Markdown V2

        Args:
            notification_data: بيانات الإشعار

        Returns:
            الرسالة المنسقة
        """
        try:
            emoji = notification_data.get('emoji', '📢')
            title = notification_data.get('title', '📢 إشعار')
            message = notification_data.get('message', '')

            formatted = (
                f"{emoji} <b>{title}</b>\n"
                f"{'═' * 28}\n\n"
                f"{message}\n\n"
                f"{'─' * 28}\n"
                f"<i>لتعطيل الإشعارات، استخدم /settings</i>"
            )

            return formatted

        except Exception as e:
            logger.error(f"❌ خطأ في تنسيق الإشعار: {e}")
            return ""

    @staticmethod
    def build_notification_keyboard() -> Optional[any]:
        """بناء لوحة أزرار الإشعار"""
        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup

            keyboard = [
                [InlineKeyboardButton("🔙 العودة", callback_data="main_menu")]
            ]

            return InlineKeyboardMarkup(keyboard)

        except Exception as e:
            logger.error(f"❌ خطأ في بناء لوحة الأزرار: {e}")
            return None
