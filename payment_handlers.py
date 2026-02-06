# ============================================================================
# معالجات الشراء والدفع - NeurHostX V8.5
# ============================================================================
"""
معالجات متكاملة لعمليات الشراء والدفع بنجوم تيليجرام
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database import Database
from payment_system import PaymentSystem, get_plan_emoji, get_plan_name
from formatters import MessageBuilder

logger = logging.getLogger(__name__)


async def plans_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """قائمة الخطط للشراء"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    # بناء الرسالة
    builder = MessageBuilder()
    builder.add_header("💎 خطط الاشتراك")
    builder.add_empty_line()

    builder.add_text("اختر الخطة المناسبة لاحتياجاتك:")
    builder.add_empty_line()

    # عرض الخطط
    for plan in ['pro', 'ultra', 'supreme']:
        info = PaymentSystem.get_plan_info(plan)
        if not info:
            continue

        plan_text = f"\n<b>{info['emoji']} {info['name']}</b>\n"
        plan_text += f"💰 {info['price']} نجم\n"
        plan_text += f"📝 {info['description']}\n"
        builder.add_text(plan_text)
        builder.add_divider()

    keyboard = [
        [
            InlineKeyboardButton("🟢 احترافي (5 نجوم)", callback_data="buy_plan_pro"),
            InlineKeyboardButton("🟣 فائق (10 نجوم)", callback_data="buy_plan_ultra")
        ],
        [InlineKeyboardButton("👑 أسطوري (25 نجم)", callback_data="buy_plan_supreme")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="my_plan")],
    ]

    await query.edit_message_text(
        builder.build(),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )


async def select_plan_to_buy(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """عرض تفاصيل الخطة المختارة قبل الشراء"""
    query = update.callback_query
    await query.answer()

    # استخراج الخطة من callback_data
    plan = query.data.replace("buy_plan_", "")

    if plan not in ['pro', 'ultra', 'supreme']:
        await query.edit_message_text("❌ الخطة غير صحيحة")
        return

    user_id = query.from_user.id

    # الحصول على معلومات الخطة
    plan_details = PaymentSystem.format_plan_details(plan)

    # بناء الرسالة
    builder = MessageBuilder()
    builder.add_header(f"تأكيد الشراء - {get_plan_emoji(plan)} {get_plan_name(plan)}")
    builder.add_empty_line()
    builder.add_text(plan_details)
    builder.add_empty_line()

    # عرض السعر
    price, _ = PaymentSystem.get_plan_price(plan)
    builder.add_text(f"<b>💳 السعر النهائي: {price} نجم</b>")
    builder.add_empty_line()
    builder.add_text("<i>بعد اختيار الدفع، ستظهر لك نافذة الدفع الآمنة</i>")

    # الأزرار
    keyboard = [
        [InlineKeyboardButton(f"💳 ادفع بـ {price} نجم", callback_data=f"pay_invoice_{plan}")],
        [InlineKeyboardButton("❌ إلغاء", callback_data="plans_menu")],
    ]

    await query.edit_message_text(
        builder.build(),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )


async def send_payment_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """إرسال فاتورة الدفع"""
    query = update.callback_query
    await query.answer()

    # استخراج الخطة
    plan = query.data.replace("pay_invoice_", "")
    user_id = query.from_user.id
    username = query.from_user.username or "مستخدم"

    if plan not in ['pro', 'ultra', 'supreme']:
        await query.edit_message_text("❌ الخطة غير صحيحة")
        return

    # الحصول على معلومات الخطة
    plan_info = PaymentSystem.get_plan_info(plan)
    price, currency = PaymentSystem.get_plan_price(plan)

    # إنشاء بيانات الفاتورة
    title = f"شراء خطة {plan_info['name']}"
    description = f"شراء الخطة {plan_info['name']} - {plan_info['description']}"
    payload = PaymentSystem.get_invoice_payload(user_id, plan)

    # إنشاء قائمة الأسعار (نجوم تيليجرام يستخدم currency_code كـ 'XTR')
    prices = [LabeledPrice(label=f"خطة {plan_info['name']}", amount=price)]

    try:
        # إرسال الفاتورة
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token="",  # نجوم تيليجرام لا تحتاج provider_token
            currency="XTR",  # عملة نجوم تيليجرام
            prices=prices,
            is_flexible=False,
            allow_user_chats=True,
            allow_bot_chats=False
        )

        logger.info(f"✅ تم إرسال فاتورة للمستخدم {user_id} للخطة {plan}")

    except Exception as e:
        logger.error(f"❌ خطأ في إرسال الفاتورة: {e}")
        await query.edit_message_text(
            f"❌ خطأ في عملية الدفع: {str(e)}\n\n"
            "يرجى المحاولة لاحقاً أو التواصل مع الدعم",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data="plans_menu")]
            ])
        )


async def pre_checkout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """معالج الاستعلام قبل الدفع (التحقق من بيانات الدفع)"""
    query = update.pre_checkout_query
    user_id = query.from_user.id

    # فك تشفير payload
    user_from_payload, plan = PaymentSystem.parse_invoice_payload(query.payload)

    # التحقق من البيانات
    is_valid, message = PaymentSystem.verify_payment(
        query.id,
        user_from_payload,
        plan,
        query.total_amount
    )

    if is_valid:
        # الموافقة على الدفع
        await query.answer(ok=True)
        logger.info(f"✅ تم التحقق من الدفع: المستخدم {user_id}")
    else:
        # رفض الدفع
        await query.answer(ok=False, error_message=message)
        logger.warning(f"⚠️ رفض الدفع: {message}")


async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """معالج الدفع الناجح"""
    message = update.message
    user_id = message.from_user.id
    successful_payment = message.successful_payment

    # فك تشفير payload
    try:
        user_from_payload, plan = PaymentSystem.parse_invoice_payload(successful_payment.invoice_payload)
    except:
        await message.reply_text(
            "❌ خطأ في معالجة الدفع. يرجى التواصل مع الدعم."
        )
        return

    # التحقق من أن المستخدم صحيح
    if user_from_payload != user_id:
        await message.reply_text(
            "❌ خطأ: عدم تطابق بيانات المستخدم"
        )
        logger.error(f"❌ عدم تطابق: {user_from_payload} != {user_id}")
        return

    try:
        # التحقق من الخطة
        if plan not in ['pro', 'ultra', 'supreme']:
            raise ValueError(f"خطة غير صحيحة: {plan}")

        # الحصول على سعر الخطة
        expected_price, _ = PaymentSystem.get_plan_price(plan)

        # التحقق من المبلغ
        if successful_payment.total_amount != expected_price:
            raise ValueError(f"مبلغ غير صحيح: {successful_payment.total_amount}")

        # تحديث خطة المستخدم في قاعدة البيانات
        from config import ADMIN_ID
        db.set_user_plan(user_id, plan, ADMIN_ID)

        # تسجيل الدفع
        PaymentSystem.log_payment(
            user_id,
            plan,
            expected_price,
            "completed",
            successful_payment.telegram_payment_charge_id
        )

        # الحصول على ملخص الدفع
        summary = PaymentSystem.get_payment_summary(user_id, plan, expected_price)

        # إرسال رسالة النجاح
        success_message = (
            f"<b>✅ دفع ناجح!</b>\n\n"
            f"{summary}\n\n"
            f"🎉 تم تفعيل خطتك بنجاح!\n"
            f"استمتع بجميع المميزات الجديدة."
        )

        await message.reply_text(
            success_message,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 عرض خطتي", callback_data="my_plan")],
                [InlineKeyboardButton("🤖 إضافة بوت", callback_data="add_bot")],
            ])
        )

        logger.info(f"✅ دفع ناجح: المستخدم {user_id}, الخطة {plan}")

    except Exception as e:
        logger.error(f"❌ خطأ في معالجة الدفع الناجح: {e}")
        await message.reply_text(
            f"❌ حدث خطأ أثناء معالجة دفعك: {str(e)}\n\n"
            "يرجى التواصل مع الدعم الفني."
        )


async def purchase_history(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """عرض سجل الشراء"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    # الحصول على معلومات المستخدم
    user_data = db.get_user(user_id)
    if not user_data:
        await query.edit_message_text("❌ بيانات المستخدم غير موجودة")
        return

    # الحصول على سجل الترقيات (هذا يحتوي على سجل الشراء)
    upgrade_history_data = db.get_user_upgrade_history(user_id)

    builder = MessageBuilder()
    builder.add_header("📜 سجل الشراء")
    builder.add_empty_line()

    if not upgrade_history_data:
        builder.add_text("❌ لا توجد عمليات شراء سابقة")
    else:
        for i, record in enumerate(upgrade_history_data[:10], 1):
            # record = (id, user_id, current_plan, requested_plan, status, created_at, reviewed_at, reviewed_by)
            builder.add_text(f"\n<b>الشراء #{i}</b>")
            builder.add_text(f"الخطة: {get_plan_emoji(record[3])} {get_plan_name(record[3])}")
            builder.add_text(f"التاريخ: {record[5]}")
            builder.add_text(f"الحالة: {'✅ مكتمل' if record[4] == 'approved' else '⏳ قيد المراجعة'}")
            builder.add_divider()

    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="my_plan")]]

    await query.edit_message_text(
        builder.build(),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )


async def refund_request(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """طلب استرجاع مبلغ"""
    query = update.callback_query
    await query.answer()

    builder = MessageBuilder()
    builder.add_header("💰 طلب استرجاع")
    builder.add_empty_line()
    builder.add_text(
        "📌 سياسة الاسترجاع:\n\n"
        "• المبالغ القابلة للاسترجاع: آخر 14 يوم من التفعيل\n"
        "• شرط الاسترجاع: عدم استخدام الخطة\n"
        "• طريقة الاسترجاع: نجوم تيليجرام\n"
        "• وقت المعالجة: 24-48 ساعة\n\n"
        "لطلب استرجاع، يرجى التواصل مع الدعم الفني."
    )
    builder.add_empty_line()

    keyboard = [
        [InlineKeyboardButton("📧 التواصل مع الدعم", url="https://t.me/neurohost_support")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="my_plan")],
    ]

    await query.edit_message_text(
        builder.build(),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )


# دالة تجميع: إضافة معالجات الشراء إلى البوت
def setup_payment_handlers(app, db):
    """تثبيت معالجات الدفع في التطبيق"""
    from telegram.ext import CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler
    from telegram.ext import filters

    # معالجات الاستفسار
    async def plans_menu_h(u, c): return await plans_menu(u, c, db)
    async def select_plan_h(u, c): return await select_plan_to_buy(u, c, db)
    async def send_invoice_h(u, c): return await send_payment_invoice(u, c, db)
    async def purchase_history_h(u, c): return await purchase_history(u, c, db)
    async def refund_request_h(u, c): return await refund_request(u, c, db)

    # تسجيل المعالجات
    app.add_handler(CallbackQueryHandler(plans_menu_h, pattern="^plans_menu$"))
    app.add_handler(CallbackQueryHandler(select_plan_h, pattern=r"^buy_plan_(pro|ultra|supreme)$"))
    app.add_handler(CallbackQueryHandler(send_invoice_h, pattern=r"^pay_invoice_(pro|ultra|supreme)$"))
    app.add_handler(CallbackQueryHandler(purchase_history_h, pattern="^purchase_history$"))
    app.add_handler(CallbackQueryHandler(refund_request_h, pattern="^refund_request$"))

    # معالجات الدفع
    async def pre_checkout_h(u, c): return await pre_checkout_callback(u, c, db)
    async def successful_payment_h(u, c): return await successful_payment_callback(u, c, db)

    app.add_handler(PreCheckoutQueryHandler(pre_checkout_h))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_h))

    logger.info("✅ تم تثبيت معالجات الدفع")
