# ============================================================================
# نظام الإشراف والإدارة المتقدم - NeuroHost V8.5 Enhanced
# ============================================================================
"""
نظام إدارة شامل يتضمن:
- الحظر (Ban) - منع الوصول نهائياً
- الكتم (Mute) - منع التفاعل مؤقتاً
- الترقية (Promote) - ترقية المستخدمين للرتب الأعلى
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, List
from enum import Enum

logger = logging.getLogger(__name__)


class MuteType(Enum):
    """أنواع الكتم المختلفة"""
    HOURS_1 = (3600, "ساعة واحدة")
    HOURS_3 = (10800, "3 ساعات")
    HOURS_6 = (21600, "6 ساعات")
    HOURS_12 = (43200, "12 ساعة")
    DAYS_1 = (86400, "يوم واحد")
    DAYS_3 = (259200, "3 أيام")
    DAYS_7 = (604800, "أسبوع واحد")
    PERMANENT = (-1, "دائم")

    @property
    def duration_seconds(self):
        return self.value[0]

    @property
    def display_name(self):
        return self.value[1]


class AdminModeration:
    """نظام الإشراف والإدارة المتقدم"""

    # ═══════════════════════════════════════════════════════════════════════
    # نظام الحظر (Ban System)
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def ban_user(db, user_id: int, admin_id: int, reason: str = "") -> Tuple[bool, str]:
        """
        حظر المستخدم منع الوصول للبوت نهائياً

        Args:
            db: كائن قاعدة البيانات
            user_id: معرف المستخدم
            admin_id: معرف الأدمن
            reason: سبب الحظر

        Returns:
            (نجاح العملية، الرسالة الوصفية)
        """
        try:
            # التحقق من أن المستخدم ليس أدمن
            if user_id == admin_id:
                return False, "❌ لا يمكن حظر حسابك الشخصي"

            # التحقق من عدم حظره بالفعل
            user = db.get_user(user_id)
            if not user:
                return False, "❌ المستخدم غير موجود في النظام"

            if user[9] == 'blocked':  # status column
                return False, "⚠️ المستخدم محظور بالفعل"

            # حظر المستخدم
            db.update_user_status(user_id, 'blocked')

            # تسجيل حدث الحظر
            log_message = f"تم حظر من قبل Admin {admin_id}"
            if reason:
                log_message += f" - السبب: {reason}"

            db.set_setting(
                f"ban_log_{user_id}",
                f"{datetime.now(timezone.utc).isoformat()}|{log_message}"
            )

            logger.info(f"✅ تم حظر المستخدم {user_id} من قبل {admin_id}")
            return True, f"✅ تم حظر المستخدم {user_id} بنجاح"

        except Exception as e:
            logger.error(f"❌ خطأ في حظر المستخدم: {e}")
            return False, f"❌ حدث خطأ: {str(e)}"

    @staticmethod
    def unban_user(db, user_id: int, admin_id: int) -> Tuple[bool, str]:
        """
        فك الحظر عن المستخدم

        Args:
            db: كائن قاعدة البيانات
            user_id: معرف المستخدم
            admin_id: معرف الأدمن

        Returns:
            (نجاح العملية، الرسالة الوصفية)
        """
        try:
            user = db.get_user(user_id)
            if not user:
                return False, "❌ المستخدم غير موجود"

            if user[9] != 'blocked':  # status
                return False, "⚠️ المستخدم غير محظور"

            # فك الحظر
            db.update_user_status(user_id, 'approved')

            logger.info(f"✅ تم فك حظر المستخدم {user_id} من قبل {admin_id}")
            return True, f"✅ تم فك حظر المستخدم {user_id}"

        except Exception as e:
            logger.error(f"❌ خطأ في فك الحظر: {e}")
            return False, f"❌ حدث خطأ: {str(e)}"

    # ═══════════════════════════════════════════════════════════════════════
    # نظام الكتم (Mute System)
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def mute_user(
        db, user_id: int, admin_id: int,
        mute_type: MuteType, reason: str = ""
    ) -> Tuple[bool, str]:
        """
        كتم المستخدم عن التفاعل مع أوامر معينة

        Args:
            db: كائن قاعدة البيانات
            user_id: معرف المستخدم
            admin_id: معرف الأدمن
            mute_type: نوع الكتم (مدة زمنية)
            reason: سبب الكتم

        Returns:
            (نجاح العملية، الرسالة الوصفية)
        """
        try:
            if user_id == admin_id:
                return False, "❌ لا يمكن كتم حسابك الشخصي"

            user = db.get_user(user_id)
            if not user:
                return False, "❌ المستخدم غير موجود"

            # حساب وقت انتهاء الكتم
            now = datetime.now(timezone.utc)

            if mute_type.duration_seconds == -1:
                # كتم دائم
                end_time = now + timedelta(days=36500)  # 100 سنة
                end_time_str = "دائم"
            else:
                end_time = now + timedelta(seconds=mute_type.duration_seconds)
                end_time_str = end_time.isoformat()

            # تطبيق الكتم
            mute_data = {
                'muted': True,
                'mute_start': now.isoformat(),
                'mute_end': end_time_str,
                'mute_type': mute_type.display_name,
                'mute_reason': reason,
                'muted_by': admin_id
            }

            db.set_setting(f"mute_{user_id}", str(mute_data))

            logger.info(f"✅ تم كتم المستخدم {user_id} لمدة {mute_type.display_name}")
            return True, f"✅ تم كتم المستخدم لمدة {mute_type.display_name}"

        except Exception as e:
            logger.error(f"❌ خطأ في كتم المستخدم: {e}")
            return False, f"❌ حدث خطأ: {str(e)}"

    @staticmethod
    def unmute_user(db, user_id: int) -> Tuple[bool, str]:
        """فك الكتم عن المستخدم"""
        try:
            db.set_setting(f"mute_{user_id}", "")
            logger.info(f"✅ تم فك كتم المستخدم {user_id}")
            return True, f"✅ تم فك الكتم"
        except Exception as e:
            logger.error(f"❌ خطأ في فك الكتم: {e}")
            return False, f"❌ حدث خطأ: {str(e)}"

    @staticmethod
    def is_user_muted(db, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        التحقق من كتم المستخدم

        Returns:
            (هل مكتوم، السبب والمدة المتبقية)
        """
        try:
            mute_data_str = db.get_setting(f"mute_{user_id}")
            if not mute_data_str:
                return False, None

            import json
            mute_data = json.loads(mute_data_str)

            if not mute_data.get('muted'):
                return False, None

            end_time = datetime.fromisoformat(mute_data['mute_end'])
            now = datetime.now(timezone.utc)

            if now > end_time:
                # انتهت مدة الكتم
                db.set_setting(f"mute_{user_id}", "")
                return False, None

            # حساب الوقت المتبقي
            remaining = end_time - now
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60

            reason_text = f"السبب: {mute_data.get('mute_reason', 'لم يحدد')}"
            remaining_text = f"⏱️ الوقت المتبقي: {hours}h {minutes}m"

            return True, f"{reason_text}\n{remaining_text}"

        except Exception as e:
            logger.warning(f"خطأ في التحقق من الكتم: {e}")
            return False, None

    # ═══════════════════════════════════════════════════════════════════════
    # نظام الترقية (Promote System)
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def promote_user(
        db, user_id: int, admin_id: int,
        new_role: str, reason: str = ""
    ) -> Tuple[bool, str]:
        """
        ترقية المستخدم لرتبة أعلى

        Args:
            db: كائن قاعدة البيانات
            user_id: معرف المستخدم
            admin_id: معرف الأدمن
            new_role: الرتبة الجديدة (moderator, premium, admin)
            reason: سبب الترقية

        Returns:
            (نجاح العملية، الرسالة الوصفية)
        """
        try:
            # التحقق من صحة الرتبة
            valid_roles = ['user', 'moderator', 'premium', 'admin']
            if new_role not in valid_roles:
                return False, f"❌ رتبة غير صحيحة. الخيارات: {', '.join(valid_roles)}"

            user = db.get_user(user_id)
            if not user:
                return False, "❌ المستخدم غير موجود"

            old_role = user[3]  # role column

            # التحقق من عدم الترقية لنفس الرتبة
            if old_role == new_role:
                return False, f"⚠️ المستخدم بالفعل في رتبة {new_role}"

            # تطبيق الترقية
            db.set_user_role(user_id, new_role)

            # تسجيل عملية الترقية
            promotion_log = {
                'old_role': old_role,
                'new_role': new_role,
                'promoted_at': datetime.now(timezone.utc).isoformat(),
                'promoted_by': admin_id,
                'reason': reason
            }

            db.set_setting(f"promotion_log_{user_id}", str(promotion_log))

            role_names = {
                'user': '👤 مستخدم عادي',
                'moderator': '🛡️ مشرف',
                'premium': '⭐ مميز',
                'admin': '🔑 أدمن'
            }

            logger.info(f"✅ تم ترقية {user_id} من {old_role} إلى {new_role}")
            return True, f"✅ تمت ترقية المستخدم من {role_names.get(old_role, old_role)} إلى {role_names.get(new_role, new_role)}"

        except Exception as e:
            logger.error(f"❌ خطأ في ترقية المستخدم: {e}")
            return False, f"❌ حدث خطأ: {str(e)}"

    @staticmethod
    def demote_user(db, user_id: int, admin_id: int) -> Tuple[bool, str]:
        """خفض رتبة المستخدم"""
        try:
            user = db.get_user(user_id)
            if not user:
                return False, "❌ المستخدم غير موجود"

            current_role = user[3]

            # تحديد الرتبة الأقل
            role_hierarchy = ['user', 'moderator', 'premium', 'admin']
            current_index = role_hierarchy.index(current_role)

            if current_index == 0:
                return False, "⚠️ المستخدم بالفعل في أقل رتبة"

            new_role = role_hierarchy[current_index - 1]
            db.set_user_role(user_id, new_role)

            logger.info(f"✅ تم خفض رتبة {user_id} إلى {new_role}")
            return True, f"✅ تم خفض الرتبة إلى {new_role}"

        except Exception as e:
            logger.error(f"❌ خطأ في خفض الرتبة: {e}")
            return False, f"❌ حدث خطأ: {str(e)}"

    # ═══════════════════════════════════════════════════════════════════════
    # إحصائيات الإشراف
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_moderation_stats(db, admin_id: int) -> Dict:
        """الحصول على إحصائيات الإشراف"""
        try:
            blocked = db.get_blocked_users()

            stats = {
                'total_banned': len(blocked),
                'total_moderated': db.get_setting(f"moderated_by_{admin_id}", "0"),
                'actions_today': 0
            }

            return stats
        except Exception as e:
            logger.warning(f"خطأ في جلب إحصائيات الإشراف: {e}")
            return {}
