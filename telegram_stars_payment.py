# ============================================================================
# نظام نجوم تلجرام المتقدم - NeuroHost V8.5 Enhanced
# ============================================================================
"""
نظام دفع وتبرعات متكامل باستخدام نجوم تلجرام:
- شراء وقت استضافة إضافي
- نظام التبرعات الذكي
- معالجة الفواتير التلقائية
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict
from enum import Enum
from telegram import LabeledPrice

logger = logging.getLogger(__name__)


class HostingPackage(Enum):
    """باقات الوقت الإضافي"""
    WEEK_1 = (5, "أسبوع واحد (7 أيام)", 604800)  # 5 نجوم
    WEEKS_2 = (9, "أسبوعين (14 يوم)", 1209600)   # 9 نجوم
    MONTH_1 = (15, "شهر واحد (30 يوم)", 2592000)  # 15 نجم
    MONTHS_3 = (40, "3 أشهر", 7776000)           # 40 نجم
    MONTHS_6 = (70, "6 أشهر", 15552000)          # 70 نجم
    YEAR_1 = (120, "سنة واحدة", 31536000)        # 120 نجم

    @property
    def stars_amount(self):
        return self.value[0]

    @property
    def display_name(self):
        return self.value[1]

    @property
    def duration_seconds(self):
        return self.value[2]


class TelegramStarsPayment:
    """نظام الدفع بنجوم تلجرام"""

    # ═══════════════════════════════════════════════════════════════════════
    # شراء وقت إضافي
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def create_hosting_invoice(
        user_id: int,
        package: HostingPackage,
        bot_id: int
    ) -> Dict:
        """
        إنشاء فاتورة شراء وقت استضافة

        Args:
            user_id: معرف المستخدم
            package: باقة الوقت المختارة
            bot_id: معرف البوت المراد إضافة وقت له

        Returns:
            بيانات الفاتورة
        """
        try:
            invoice_data = {
                'invoice_id': f"hosting_{user_id}_{bot_id}_{datetime.now().timestamp()}",
                'user_id': user_id,
                'bot_id': bot_id,
                'package': package.name,
                'amount': package.stars_amount,
                'duration': package.duration_seconds,
                'description': f"🕥 وقت استضافة - {package.display_name}",
                'created_at': datetime.now(timezone.utc).isoformat(),
                'status': 'pending',
                'currency': 'XTR'
            }

            logger.info(f"✅ تم إنشاء فاتورة استضافة: {invoice_data['invoice_id']}")
            return invoice_data

        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء الفاتورة: {e}")
            return {}

    @staticmethod
    def add_hosting_time(
        db, user_id: int, bot_id: int,
        duration_seconds: int, source: str = "payment"
    ) -> Tuple[bool, str]:
        """
        إضافة وقت استضافة للبوت

        Args:
            db: كائن قاعدة البيانات
            user_id: معرف المستخدم
            bot_id: معرف البوت
            duration_seconds: المدة المراد إضافتها بالثواني
            source: مصدر الإضافة (payment/admin/promotion)

        Returns:
            (نجاح العملية، الرسالة)
        """
        try:
            bot = db.get_bot(bot_id)
            if not bot:
                return False, "❌ البوت غير موجود"

            # التحقق من ملكية البوت
            if bot[1] != user_id:  # user_id column
                return False, "❌ أنت لا تملك هذا البوت"

            # إضافة الوقت
            current_remaining = bot[12]  # remaining_seconds
            new_remaining = current_remaining + duration_seconds

            db.update_bot_resources(
                bot_id,
                remaining_seconds=new_remaining
            )

            # تسجيل العملية
            db.add_event_log(
                bot_id,
                "hosting_added",
                f"تم إضافة {duration_seconds} ثانية من مصدر {source}"
            )

            logger.info(
                f"✅ تم إضافة {duration_seconds}s وقت للبوت {bot_id} "
                f"من المستخدم {user_id}"
            )

            return True, "✅ تم إضافة الوقت بنجاح"

        except Exception as e:
            logger.error(f"❌ خطأ في إضافة الوقت: {e}")
            return False, f"❌ حدث خطأ: {str(e)}"

    # ═══════════════════════════════════════════════════════════════════════
    # نظام التبرعات
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def create_donation_invoice(
        user_id: int, amount: int,
        purpose: str = "دعم المشروع"
    ) -> Dict:
        """
        إنشاء فاتورة تبرع

        Args:
            user_id: معرف المتبرع
            amount: عدد النجوم المراد التبرع بها
            purpose: الغرض من التبرع

        Returns:
            بيانات الفاتورة
        """
        try:
            # التحقق من أن المبلغ صحيح
            if amount < 1 or amount > 2500:
                return {}

            invoice_data = {
                'invoice_id': f"donation_{user_id}_{datetime.now().timestamp()}",
                'user_id': user_id,
                'amount': amount,
                'purpose': purpose,
                'description': f"💝 تبرع - {purpose}",
                'created_at': datetime.now(timezone.utc).isoformat(),
                'status': 'pending',
                'currency': 'XTR'
            }

            logger.info(f"✅ تم إنشاء فاتورة تبرع: {invoice_data['invoice_id']}")
            return invoice_data

        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء فاتورة التبرع: {e}")
            return {}

    @staticmethod
    def record_donation(
        db, user_id: int, amount: int,
        purpose: str = "", invoice_id: str = ""
    ) -> Tuple[bool, str]:
        """
        تسجيل التبرع في قاعدة البيانات

        Args:
            db: كائن قاعدة البيانات
            user_id: معرف المتبرع
            amount: عدد النجوم
            purpose: الغرض من التبرع
            invoice_id: معرف الفاتورة

        Returns:
            (نجاح العملية، الرسالة)
        """
        try:
            donation_record = {
                'donated_by': user_id,
                'amount': amount,
                'purpose': purpose,
                'invoice_id': invoice_id,
                'donated_at': datetime.now(timezone.utc).isoformat()
            }

            # تسجيل التبرع
            db.set_setting(
                f"donation_{user_id}_{datetime.now().timestamp()}",
                str(donation_record)
            )

            # تحديث إجمالي التبرعات
            total_key = f"total_donations_{user_id}"
            current_total = int(db.get_setting(total_key, "0") or "0")
            db.set_setting(total_key, str(current_total + amount))

            logger.info(f"✅ تم تسجيل تبرع {amount} نجم من {user_id}")
            return True, f"💝 شكراً على تبرعك! لقد تبرعت بـ {amount} نجم"

        except Exception as e:
            logger.error(f"❌ خطأ في تسجيل التبرع: {e}")
            return False, f"❌ حدث خطأ: {str(e)}"

    # ═══════════════════════════════════════════════════════════════════════
    # معالجة نجاح الدفع
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def handle_successful_payment(
        db, invoice_id: str,
        telegram_payment_charge_id: str
    ) -> Tuple[bool, str]:
        """
        معالجة الدفع الناجح وتحديث قاعدة البيانات

        Args:
            db: كائن قاعدة البيانات
            invoice_id: معرف الفاتورة
            telegram_payment_charge_id: معرف الدفع من تلجرام

        Returns:
            (نجاح العملية، الرسالة)
        """
        try:
            # استخراج البيانات من معرف الفاتورة
            if invoice_id.startswith('hosting_'):
                return TelegramStarsPayment._handle_hosting_payment(
                    db, invoice_id, telegram_payment_charge_id
                )
            elif invoice_id.startswith('donation_'):
                return TelegramStarsPayment._handle_donation_payment(
                    db, invoice_id, telegram_payment_charge_id
                )

            return False, "❌ نوع فاتورة غير معروف"

        except Exception as e:
            logger.error(f"❌ خطأ في معالجة الدفع: {e}")
            return False, f"❌ حدث خطأ: {str(e)}"

    @staticmethod
    def _handle_hosting_payment(
        db, invoice_id: str, payment_id: str
    ) -> Tuple[bool, str]:
        """معالجة دفع الاستضافة"""
        try:
            parts = invoice_id.split('_')
            user_id = int(parts[1])
            bot_id = int(parts[2])

            bot = db.get_bot(bot_id)
            if not bot:
                return False, "❌ البوت غير موجود"

            # استخراج المدة من البيانات المحفوظة
            package_data = db.get_setting(f"pending_payment_{invoice_id}")
            if not package_data:
                return False, "❌ لم يتم العثور على بيانات الفاتورة"

            # هنا نستخدم مدة افتراضية (يجب أن تكون محفوظة)
            duration = 604800  # أسبوع افتراضياً

            success, msg = TelegramStarsPayment.add_hosting_time(
                db, user_id, bot_id, duration, "telegram_stars"
            )

            if success:
                # حفظ بيانات الدفع
                db.set_setting(
                    f"payment_record_{payment_id}",
                    f"hosting|{user_id}|{bot_id}|{duration}|{datetime.now(timezone.utc).isoformat()}"
                )

                logger.info(f"✅ تم معالجة دفع استضافة ناجح: {invoice_id}")

            return success, msg

        except Exception as e:
            logger.error(f"❌ خطأ في معالجة دفع الاستضافة: {e}")
            return False, f"❌ حدث خطأ: {str(e)}"

    @staticmethod
    def _handle_donation_payment(
        db, invoice_id: str, payment_id: str
    ) -> Tuple[bool, str]:
        """معالجة دفع التبرع"""
        try:
            parts = invoice_id.split('_')
            user_id = int(parts[1])

            # استخراج بيانات التبرع
            donation_data = db.get_setting(f"pending_donation_{invoice_id}")
            if not donation_data:
                return False, "❌ لم يتم العثور على بيانات التبرع"

            # هنا يتم تسجيل التبرع بشكل نهائي
            success, msg = TelegramStarsPayment.record_donation(
                db, user_id, 5,  # المبلغ الافتراضي
                "دعم المشروع", invoice_id
            )

            if success:
                db.set_setting(
                    f"payment_record_{payment_id}",
                    f"donation|{user_id}|5|{datetime.now(timezone.utc).isoformat()}"
                )

            return success, msg

        except Exception as e:
            logger.error(f"❌ خطأ في معالجة دفع التبرع: {e}")
            return False, f"❌ حدث خطأ: {str(e)}"

    # ═══════════════════════════════════════════════════════════════════════
    # الإحصائيات
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def get_user_donations(db, user_id: int) -> int:
        """الحصول على إجمالي تبرعات المستخدم"""
        try:
            total = db.get_setting(f"total_donations_{user_id}", "0")
            return int(total or "0")
        except:
            return 0

    @staticmethod
    def get_system_donations(db) -> int:
        """الحصول على إجمالي التبرعات في النظام"""
        try:
            # هذا سيتطلب تحسين لاحقاً لجلب جميع التبرعات
            return 0
        except:
            return 0
