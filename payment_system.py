# ============================================================================
# نظام الشراء والدفع بنجوم تيليجرام - NeurHostX V8.5
# ============================================================================
"""
نظام متكامل لشراء الخطط باستخدام نجوم تيليجرام
يشمل الفواتير والدفع والتحقق والتأكيد
"""

import logging
from typing import Dict, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PlanPrice(Enum):
    """أسعار الخطط بالنجوم"""
    FREE = 0          # مجاني
    PRO = 5           # احترافي (5 نجوم = ~$5)
    ULTRA = 10        # فائق (10 نجوم = ~$10)
    SUPREME = 25      # أسطوري (25 نجم = ~$25)


class PaymentStatus(Enum):
    """حالات الدفع"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentSystem:
    """نظام الدفع المتكامل"""

    # معلومات الخطط
    PLAN_INFO = {
        'pro': {
            'name': '🟢 خطة احترافية',
            'emoji': '🟢',
            'price': 5,  # 5 نجوم
            'currency': 'XTR',  # Telegram Stars
            'description': 'خطة احترافية مع 5 بوتات وأسبوع وقت فقط بـ 5 نجوم',
            'features': [
                '5 بوتات كحد أقصى',
                'وقت استضافة أسبوع',
                'استرجاع يومي 2 ساعة',
                'مدير ملفات متقدم',
                'دعم فني أساسي'
            ]
        },
        'ultra': {
            'name': '🟣 خطة فائقة',
            'emoji': '🟣',
            'price': 10,  # 10 نجوم
            'currency': 'XTR',
            'description': 'خطة فائقة مع 10 بوتات وشهر وقت بـ 10 نجوم',
            'features': [
                '10 بوتات كحد أقصى',
                'وقت استضافة شهر',
                'استرجاع يومي 3 ساعات',
                'مدير ملفات كامل',
                'دعم فني متقدم',
                'إحصائيات متقدمة',
                'أولوية عالية'
            ]
        },
        'supreme': {
            'name': '👑 خطة أسطورية',
            'emoji': '👑',
            'price': 25,  # 25 نجم
            'currency': 'XTR',
            'description': 'خطة أسطورية مع بوتات غير محدودة ووقت غير محدود بـ 25 نجم',
            'features': [
                'بوتات غير محدودة',
                'وقت تشغيل لا نهائي',
                'استرجاع غير محدود',
                'موارد حصرية',
                'دعم VIP 24/7',
                'أولوية قصوى',
                'نسخ احتياطي فوري',
                'API خاص'
            ]
        }
    }

    @staticmethod
    def get_plan_price(plan: str) -> Tuple[int, str]:
        """الحصول على سعر الخطة

        Args:
            plan: اسم الخطة (pro/ultra/supreme)

        Returns:
            (السعر بالنجوم، رمز العملة)
        """
        if plan not in PaymentSystem.PLAN_INFO:
            return 0, 'XTR'

        info = PaymentSystem.PLAN_INFO[plan]
        return info['price'], info['currency']

    @staticmethod
    def get_plan_info(plan: str) -> Optional[Dict]:
        """الحصول على معلومات الخطة الكاملة"""
        return PaymentSystem.PLAN_INFO.get(plan)

    @staticmethod
    def get_invoice_payload(user_id: int, plan: str) -> str:
        """إنشاء payload للفاتورة

        Args:
            user_id: معرف المستخدم
            plan: اسم الخطة

        Returns:
            payload كـ string
        """
        return f"{user_id}_{plan}_{datetime.now().timestamp()}"

    @staticmethod
    def parse_invoice_payload(payload: str) -> Tuple[int, str]:
        """فك تشفير payload الفاتورة

        Args:
            payload: payload من الفاتورة

        Returns:
            (معرف المستخدم، اسم الخطة)
        """
        try:
            parts = payload.split('_')
            user_id = int(parts[0])
            plan = parts[1]
            return user_id, plan
        except:
            return 0, ''

    @staticmethod
    def format_price(price: int) -> str:
        """تنسيق السعر للعرض

        Args:
            price: السعر بالنجوم

        Returns:
            السعر المنسق
        """
        if price == 0:
            return 'مجاني'
        return f'{price} نجم'

    @staticmethod
    def calculate_duration(plan: str) -> int:
        """حساب مدة الخطة بالأيام

        Args:
            plan: اسم الخطة

        Returns:
            عدد الأيام
        """
        durations = {
            'free': 1,      # يومي
            'pro': 7,       # أسبوع
            'ultra': 30,    # شهر
            'supreme': 365  # سنة
        }
        return durations.get(plan, 1)

    @staticmethod
    def get_expiration_date(plan: str) -> datetime:
        """حساب تاريخ انتهاء الخطة

        Args:
            plan: اسم الخطة

        Returns:
            تاريخ الانتهاء
        """
        duration = PaymentSystem.calculate_duration(plan)
        return datetime.now() + timedelta(days=duration)

    @staticmethod
    def format_plan_details(plan: str) -> str:
        """تنسيق تفاصيل الخطة للعرض

        Args:
            plan: اسم الخطة

        Returns:
            نص مفصل عن الخطة
        """
        info = PaymentSystem.get_plan_info(plan)
        if not info:
            return 'الخطة غير موجودة'

        text = f"<b>{info['name']}</b>\n"
        text += f"{'=' * 40}\n\n"

        text += f"<b>💰 السعر:</b> {info['price']} نجم\n"
        text += f"<b>📅 المدة:</b> "

        if plan == 'free':
            text += "يومي\n"
        elif plan == 'pro':
            text += "أسبوع\n"
        elif plan == 'ultra':
            text += "شهر\n"
        else:
            text += "سنة\n"

        text += f"\n<b>✨ المميزات:</b>\n"
        for feature in info['features']:
            text += f"✅ {feature}\n"

        return text

    @staticmethod
    def create_payment_invoice(
        user_id: int,
        plan: str,
        title: str = '',
        description: str = ''
    ) -> Dict:
        """إنشاء بيانات الفاتورة

        Args:
            user_id: معرف المستخدم
            plan: اسم الخطة
            title: عنوان الفاتورة
            description: وصف الفاتورة

        Returns:
            قاموس بيانات الفاتورة
        """
        price, currency = PaymentSystem.get_plan_price(plan)
        plan_info = PaymentSystem.get_plan_info(plan)

        if not plan_info:
            return {}

        if not title:
            title = plan_info['name']
        if not description:
            description = plan_info['description']

        payload = PaymentSystem.get_invoice_payload(user_id, plan)

        return {
            'title': title,
            'description': description,
            'payload': payload,
            'provider_token': '',  # سيتم تعيينه من قبل البوت
            'currency': currency,
            'prices': [
                {
                    'label': f"خطة {plan_info['name']}",
                    'amount': price
                }
            ],
            'plan': plan,
            'user_id': user_id,
            'price': price
        }

    @staticmethod
    def verify_payment(
        pre_checkout_query_id: str,
        user_id: int,
        plan: str,
        amount: int
    ) -> Tuple[bool, str]:
        """التحقق من الدفع قبل المعالجة

        Args:
            pre_checkout_query_id: معرف الاستعلام
            user_id: معرف المستخدم
            plan: اسم الخطة
            amount: المبلغ بالنجوم

        Returns:
            (نجح؟، رسالة)
        """
        # التحقق من أن الخطة موجودة
        if plan not in PaymentSystem.PLAN_INFO:
            return False, "الخطة غير موجودة"

        # التحقق من السعر
        correct_price, _ = PaymentSystem.get_plan_price(plan)
        if amount != correct_price:
            return False, f"السعر غير صحيح. التوقع: {correct_price}, المستلم: {amount}"

        # التحقق من المستخدم
        if not user_id or user_id <= 0:
            return False, "معرف المستخدم غير صالح"

        logger.info(f"✅ تحقق من الدفع: المستخدم {user_id}, الخطة {plan}, المبلغ {amount}")
        return True, "تحقق ناجح"

    @staticmethod
    def log_payment(
        user_id: int,
        plan: str,
        amount: int,
        status: str,
        transaction_id: str = ''
    ) -> None:
        """تسجيل عملية الدفع

        Args:
            user_id: معرف المستخدم
            plan: اسم الخطة
            amount: المبلغ
            status: حالة الدفع
            transaction_id: معرف المعاملة
        """
        log_message = (
            f"💳 دفع: المستخدم={user_id}, "
            f"الخطة={plan}, "
            f"المبلغ={amount} نجم, "
            f"الحالة={status}"
        )

        if transaction_id:
            log_message += f", المعاملة={transaction_id}"

        logger.info(log_message)

    @staticmethod
    def get_payment_summary(
        user_id: int,
        plan: str,
        amount: int
    ) -> str:
        """الحصول على ملخص الدفع

        Args:
            user_id: معرف المستخدم
            plan: اسم الخطة
            amount: المبلغ

        Returns:
            نص ملخص الدفع
        """
        plan_info = PaymentSystem.get_plan_info(plan)
        if not plan_info:
            return "معلومات غير متاحة"

        expiry_date = PaymentSystem.get_expiration_date(plan)

        text = "<b>📋 ملخص الدفع</b>\n\n"
        text += f"<b>الخطة:</b> {plan_info['name']}\n"
        text += f"<b>السعر:</b> {amount} نجم\n"
        text += f"<b>تاريخ الشراء:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        text += f"<b>تاريخ الانتهاء:</b> {expiry_date.strftime('%Y-%m-%d')}\n\n"

        text += "<b>✨ المميزات المفعلة:</b>\n"
        for feature in plan_info['features']:
            text += f"✅ {feature}\n"

        return text


# دوال مساعدة سريعة
def get_plan_emoji(plan: str) -> str:
    """الحصول على رمز الخطة"""
    info = PaymentSystem.get_plan_info(plan)
    if info:
        return info['emoji']
    return '🔵'


def get_plan_name(plan: str) -> str:
    """الحصول على اسم الخطة"""
    info = PaymentSystem.get_plan_info(plan)
    if info:
        return info['name']
    return 'خطة مجهولة'


def is_paid_plan(plan: str) -> bool:
    """التحقق من أن الخطة مدفوعة"""
    return plan in ['pro', 'ultra', 'supreme']


def get_all_paid_plans() -> list:
    """الحصول على جميع الخطط المدفوعة"""
    return [p for p in PaymentSystem.PLAN_INFO.keys() if is_paid_plan(p)]
