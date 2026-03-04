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
        # إرسال الفاتورة - Telegram Stars XTR
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token="",  # نجوم تيليجرام لا تحتاج provider_token
            currency="XTR",    # عملة نجوم تيليجرام
            prices=prices,
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
    """معالج الدفع الناجح - يعالج خطط الاشتراك وشراء وقت الاستضافة والتبرعات"""
    message = update.message
    user_id = message.from_user.id
    successful_payment = message.successful_payment
    payload = successful_payment.invoice_payload

    # ═══ معالجة التبرع ═══
    if payload.startswith("donate_"):
        parts = payload.split("_")
        amount = parts[-1] if len(parts) >= 3 else "?"
        await message.reply_text(
            f"════════════════════════════\n"
            f"💝 <b>شكراً جزيلاً على دعمك!</b>\n"
            f"════════════════════════════\n\n"
            f"⭐ المبلغ: <b>{amount} نجمة</b>\n\n"
            f"❤️ مساهمتك تساعد في تطوير NeurHostX\n"
            f"وتحسين الخدمات للجميع!",
            parse_mode="HTML"
        )
        return

    # ═══ معالجة شراء وقت استضافة ═══
    if payload.startswith("hosting_"):
        try:
            # hosting_{user_id}_{bot_id}_{period}
            parts = payload.split("_")
            bot_id = int(parts[2])
            period = parts[3]

            from enhanced_handlers import HOSTING_PACKAGES
            pkg = HOSTING_PACKAGES.get(period)
            if not pkg:
                raise ValueError(f"باقة غير معروفة: {period}")

            days = pkg["days"]
            seconds_to_add = days * 24 * 3600

            bot = db.get_bot(bot_id)
            if bot:
                current_total = bot[10] or 0
                current_remaining = bot[11] or 0
                db.update_bot_resources(
                    bot_id,
                    total_seconds=current_total + seconds_to_add,
                    remaining_seconds=current_remaining + seconds_to_add,
                    warned_low=0
                )
                db.add_event_log(bot_id, "INFO", f"✅ تمت إضافة {days} يوم عبر الدفع")
                bot_name = bot[3]
            else:
                bot_name = f"البوت #{bot_id}"

            await message.reply_text(
                f"════════════════════════════\n"
                f"✅ <b>تم شراء وقت الاستضافة!</b>\n"
                f"════════════════════════════\n\n"
                f"🤖 البوت: <b>{bot_name}</b>\n"
                f"📦 الباقة: <b>{pkg['label']}</b>\n"
                f"⏱️ المدة المضافة: <b>{days} يوم</b>\n\n"
                f"✨ تم تفعيل المدة فوراً",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🤖 إدارة البوت", callback_data=f"manage_{bot_id}")],
                    [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")]
                ])
            )
            return
        except Exception as e:
            logger.error(f"خطأ في معالجة دفع الاستضافة: {e}")
            await message.reply_text(f"✅ تم استلام الدفع. تواصل مع الدعم لتطبيق الوقت.")
            return

    # ═══ معالجة خطط الاشتراك ═══
    try:
        user_from_payload, plan = PaymentSystem.parse_invoice_payload(payload)
    except (ValueError, TypeError, IndexError) as e:
        logger.warning(f"⚠️ خطأ في payload: {e}")
        await message.reply_text("❌ خطأ في معالجة الدفع. يرجى التواصل مع الدعم.")
        return

    if user_from_payload != user_id:
        await message.reply_text("❌ خطأ: عدم تطابق بيانات المستخدم")
        return

    try:
        if plan not in ['pro', 'ultra', 'supreme']:
            raise ValueError(f"خطة غير صحيحة: {plan}")

        expected_price, _ = PaymentSystem.get_plan_price(plan)

        if successful_payment.total_amount != expected_price:
            raise ValueError(f"مبلغ غير صحيح: {successful_payment.total_amount}")

        from config import ADMIN_ID
        db.set_user_plan(user_id, plan, ADMIN_ID)

        PaymentSystem.log_payment(
            user_id, plan, expected_price, "completed",
            successful_payment.telegram_payment_charge_id
        )

        plan_info = PaymentSystem.get_plan_info(plan)
        plan_name = plan_info.get('name', plan) if plan_info else plan

        await message.reply_text(
            f"════════════════════════════\n"
            f"✅ <b>تم الدفع بنجاح!</b>\n"
            f"════════════════════════════\n\n"
            f"🎉 تم تفعيل خطة <b>{plan_name}</b>\n"
            f"⭐ المبلغ: <b>{expected_price} نجمة</b>\n\n"
            f"{'─'*28}\n"
            f"استمتع بجميع المميزات الجديدة!",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📊 عرض خطتي", callback_data="my_plan")],
                [InlineKeyboardButton("🤖 إضافة بوت", callback_data="add_bot")],
                [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")]
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
