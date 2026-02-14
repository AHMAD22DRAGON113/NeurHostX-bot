# ============================================================================
# نظام الدفع الموحد - NeuroHost V8.5 Ultimate
# ============================================================================
"""
نظام دفع شامل ومتكامل:
- شراء الخطط بنجوم تيليجرام
- شراء وقت إضافي
- نظام التبرعات
- معالجة الفواتير
- التحقق من الدفع
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, List
from enum import Enum
from telegram import LabeledPrice

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# تعاريف الأسعار والخطط
# ═══════════════════════════════════════════════════════════════════════════

class HostingPackage(Enum):
    """باقات الوقت الإضافي"""
    WEEK_1 = (5, "أسبوع واحد (7 أيام)", 604800)
    WEEKS_2 = (9, "أسبوعين (14 يوم)", 1209600)
    MONTH_1 = (15, "شهر واحد (30 يوم)", 2592000)
    MONTHS_3 = (40, "3 أشهر", 7776000)
    MONTHS_6 = (70, "6 أشهر", 15552000)
    YEAR_1 = (120, "سنة واحدة", 31536000)

    @property
    def stars_amount(self):
        return self.value[0]

    @property
    def display_name(self):
        return self.value[1]

    @property
    def duration_seconds(self):
        return self.value[2]


class PlanPrice(Enum):
    """أسعار الخطط بالنجوم"""
    FREE = 0
    PRO = 5
    ULTRA = 10
    SUPREME = 25


class PaymentStatus(Enum):
    """حالات الدفع"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ═══════════════════════════════════════════════════════════════════════════
# فئة نظام الدفع الموحد
# ═══════════════════════════════════════════════════════════════════════════

class UnifiedPaymentSystem:
    """نظام الدفع الموحد المتكامل"""

    # معلومات الخطط
    PLAN_INFO = {
        'pro': {
            'name': '🟢 خطة احترافية',
            'emoji': '🟢',
            'price': 5,
            'currency': 'XTR',
            'description': 'خطة احترافية بـ 5 نجوم',
            'features': [
                '5 بوتات كحد أقصى',
                'وقت استضافة أسبوع',
                'استرجاع يومي 2 ساعة',
                'مدير ملفات متقدم',
                'دعم فني أساسي'
            ],
        },
        'ultra': {
            'name': '🟣 خطة فائقة',
            'emoji': '🟣',
            'price': 10,
            'currency': 'XTR',
            'description': 'خطة فائقة بـ 10 نجوم',
            'features': [
                '10 بوتات كحد أقصى',
                'وقت استضافة شهر',
                'استرجاع يومي مجاني',
                'مدير ملفات كامل',
                'دعم فني متقدم',
                'نسخ احتياطي تلقائي'
            ],
        },
        'supreme': {
            'name': '👑 خطة أسطورية',
            'emoji': '👑',
            'price': 25,
            'currency': 'XTR',
            'description': 'خطة أسطورية بـ 25 نجم',
            'features': [
                'بوتات غير محدودة',
                'اسثضافة غير محدودة',
                'موارد حصرية',
                'دعم فني VIP',
                'أولوية عالية'
            ],
        }
    }

    # ─────────────────────────────────────────────────────────────────────
    # عمليات إنشاء الفواتير
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def create_plan_invoice(plan: str) -> Optional[List[LabeledPrice]]:
        """إنشاء فاتورة لشراء خطة"""
        try:
            plan_info = UnifiedPaymentSystem.PLAN_INFO.get(plan)
            if not plan_info:
                logger.error(f"خطة غير موجودة: {plan}")
                return None

            prices = [
                LabeledPrice(
                    label=plan_info['name'],
                    amount=plan_info['price'] * 1  # Telegram Stars
                )
            ]

            logger.info(f"✅ تم إنشاء فاتورة الخطة: {plan}")
            return prices

        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء فاتورة الخطة: {e}")
            return None

    @staticmethod
    def create_hosting_invoice(package: HostingPackage) -> Optional[List[LabeledPrice]]:
        """إنشاء فاتورة شراء وقت إضافي"""
        try:
            prices = [
                LabeledPrice(
                    label=package.display_name,
                    amount=package.stars_amount
                )
            ]

            logger.info(f"✅ تم إنشاء فاتورة الوقت: {package.display_name}")
            return prices

        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء فاتورة الوقت: {e}")
            return None

    @staticmethod
    def create_donation_invoice(amount: int) -> Optional[List[LabeledPrice]]:
        """إنشاء فاتورة تبرع"""
        try:
            if amount < 1:
                logger.error("مبلغ التبرع يجب أن يكون ≥ 1 نجم")
                return None

            prices = [
                LabeledPrice(
                    label=f"💝 تبرع {amount} نجم",
                    amount=amount
                )
            ]

            logger.info(f"✅ تم إنشاء فاتورة تبرع: {amount} نجم")
            return prices

        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء فاتورة التبرع: {e}")
            return None

    # ─────────────────────────────────────────────────────────────────────
    # معلومات الخطط
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_plan_info(plan: str) -> Optional[Dict]:
        """الحصول على معلومات خطة"""
        return UnifiedPaymentSystem.PLAN_INFO.get(plan)

    @staticmethod
    def format_plan_details(plan: str) -> str:
        """تنسيق تفاصيل الخطة للعرض"""
        info = UnifiedPaymentSystem.get_plan_info(plan)
        if not info:
            return "❌ خطة غير موجودة"

        text = f"<b>{info['emoji']} {info['name']}</b>\n"
        text += f"{'─' * 35}\n\n"
        text += f"💰 السعر: <b>{info['price']} نجم</b>\n\n"
        text += f"<b>المميزات:</b>\n"

        for feature in info.get('features', []):
            text += f"✨ {feature}\n"

        return text

    # ─────────────────────────────────────────────────────────────────────
    # معالجة الدفع
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def log_payment(db, user_id: int, payment_type: str, amount: int, 
                   status: PaymentStatus, description: str = "") -> bool:
        """تسجيل عملية دفع في قاعدة البيانات"""
        try:
            if hasattr(db, 'add_payment_log'):
                db.add_payment_log(
                    user_id=user_id,
                    payment_type=payment_type,
                    amount=amount,
                    status=status.value,
                    description=description,
                    timestamp=datetime.now(timezone.utc)
                )
                logger.info(f"✅ تم تسجيل الدفع: {user_id} - {payment_type} - {amount} نجم")
                return True
            else:
                logger.warning("قاعدة البيانات لا تدعم تسجيل الدفع")
                return False

        except Exception as e:
            logger.error(f"❌ خطأ في تسجيل الدفع: {e}")
            return False

    @staticmethod
    def verify_payment(db, user_id: int, payment_id: str) -> Tuple[bool, str]:
        """التحقق من عملية دفع"""
        try:
            if hasattr(db, 'get_payment'):
                payment = db.get_payment(payment_id)
                if not payment:
                    return False, "عملية دفع غير موجودة"

                if payment[1] != user_id:
                    return False, "المستخدم غير متطابق"

                if payment[3] != PaymentStatus.COMPLETED.value:
                    return False, "الدفع لم يكتمل"

                logger.info(f"✅ تم التحقق من الدفع: {payment_id}")
                return True, "تم التحقق بنجاح"
            else:
                logger.warning("قاعدة البيانات لا تدعم التحقق من الدفع")
                return True, "بدون تحقق (نمط اختبار)"

        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من الدفع: {e}")
            return False, str(e)

    # ─────────────────────────────────────────────────────────────────────
    # الإحصائيات المالية
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_revenue_stats(db, days: int = 30) -> Dict:
        """الحصول على إحصائيات الإيرادات"""
        try:
            since = datetime.now(timezone.utc) - timedelta(days=days)

            if hasattr(db, 'get_revenue_stats'):
                stats = db.get_revenue_stats(days)
                return stats
            else:
                logger.warning("قاعدة البيانات لا تدعم إحصائيات الإيرادات")
                return {
                    'total_sales': 0,
                    'total_revenue': 0,
                    'avg_transaction': 0,
                    'transactions_count': 0
                }

        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على الإحصائيات: {e}")
            return {}

    # ─────────────────────────────────────────────────────────────────────
    # دوال مساعدة
    # ─────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_plan_emoji(plan: str) -> str:
        """الحصول على إيموجي الخطة"""
        info = UnifiedPaymentSystem.get_plan_info(plan)
        return info.get('emoji', '📦') if info else '📦'

    @staticmethod
    def get_plan_name(plan: str) -> str:
        """الحصول على اسم الخطة"""
        info = UnifiedPaymentSystem.get_plan_info(plan)
        return info.get('name', 'خطة مجهولة') if info else 'خطة مجهولة'

    @staticmethod
    def get_plan_price(plan: str) -> Tuple[int, str]:
        """الحصول على سعر الخطة بالنجوم والعملة"""
        info = UnifiedPaymentSystem.get_plan_info(plan)
        if info:
            return info.get('price', 0), 'XTR'  # Telegram Stars
        return 0, 'XTR'

    @staticmethod
    def get_invoice_payload(user_id: int, plan: str) -> str:
        """إنشاء معرف فاتورة فريد"""
        import json
        payload = {'user_id': user_id, 'plan': plan}
        return json.dumps(payload)

    @staticmethod
    def parse_invoice_payload(payload: str) -> Tuple[int, str]:
        """فك تشفير معرف الفاتورة"""
        import json
        try:
            data = json.loads(payload)
            return data.get('user_id', 0), data.get('plan', 'free')
        except:
            return 0, 'free'

    @staticmethod
    def verify_payment(payment_id: str, user_id: int, plan: str, amount: int) -> Tuple[bool, str]:
        """التحقق من صحة بيانات الدفع"""
        expected_price, _ = UnifiedPaymentSystem.get_plan_price(plan)
        
        if amount != expected_price:
            return False, f"المبلغ غير صحيح. المتوقع: {expected_price}"
        
        if not plan in ['free', 'pro', 'ultra', 'supreme']:
            return False, "الخطة غير صحيحة"
        
        return True, "تم التحقق بنجاح"

    @staticmethod
    def format_stars(amount: int) -> str:
        """تنسيق مبلغ النجوم"""
        return f"<b>{amount} ⭐</b>"

    @staticmethod
    def get_hosting_packages() -> List[Tuple[str, HostingPackage]]:
        """الحصول على قائمة الباقات المتاحة"""
        return [
            ("أسبوع (5 نجوم)", HostingPackage.WEEK_1),
            ("أسبوعين (9 نجوم)", HostingPackage.WEEKS_2),
            ("شهر (15 نجم)", HostingPackage.MONTH_1),
            ("3 أشهر (40 نجم)", HostingPackage.MONTHS_3),
            ("6 أشهر (70 نجم)", HostingPackage.MONTHS_6),
            ("سنة (120 نجم)", HostingPackage.YEAR_1),
        ]


# ═══════════════════════════════════════════════════════════════════════════
# دوال تسهيلية للتوافقية مع الملفات القديمة
# ═══════════════════════════════════════════════════════════════════════════

def get_plan_emoji(plan: str) -> str:
    """دالة متوافقة للحصول على إيموجي الخطة"""
    return UnifiedPaymentSystem.get_plan_emoji(plan)


def get_plan_name(plan: str) -> str:
    """دالة متوافقة للحصول على اسم الخطة"""
    return UnifiedPaymentSystem.get_plan_name(plan)


def create_plan_invoice(plan: str) -> Optional[List[LabeledPrice]]:
    """دالة متوافقة لإنشاء فاتورة خطة"""
    return UnifiedPaymentSystem.create_plan_invoice(plan)


# ═══════════════════════════════════════════════════════════════════════════
# استيراد متوافق
# ═══════════════════════════════════════════════════════════════════════════

PaymentSystem = UnifiedPaymentSystem
TelegramStarsPayment = UnifiedPaymentSystem

__all__ = [
    'UnifiedPaymentSystem',
    'PaymentSystem',
    'TelegramStarsPayment',
    'HostingPackage',
    'PlanPrice',
    'PaymentStatus',
    'get_plan_emoji',
    'get_plan_name',
    'create_plan_invoice',
]
