# ============================================================================
# معالجات النظام المحسنة والمدمجة - NeuroHost V8.5
# ============================================================================
"""
معالجات شاملة للميزات الجديدة:
- لوحة التحكم الإدارية المحسنة
- معالجات الدفع والتبرعات
- معالجات الإشعارات الذكية
"""

import logging
from datetime import datetime, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_ID

# استيراد الأنظمة الجديدة
from admin_moderation import AdminModeration, MuteType
from telegram_stars_payment import TelegramStarsPayment, HostingPackage
from smart_notifications import SmartNotifications, NotificationCategory

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# معالجات إدارة المستخدمين المتقدمة
# ═══════════════════════════════════════════════════════════════════════════

async def admin_moderation_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """
    لوحة الإشراف والإدارة المتقدمة 🛡️
    """
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    # التحقق من أن المستخدم أدمن
    if user_id != ADMIN_ID:
        await query.edit_message_text(
            "⛔ <b>غير مصرح</b>\n"
            "هذه الميزة متاحة للأدمن فقط",
            parse_mode="HTML"
        )
        return

    # بناء لوحة الإدارة
    keyboard = [
        [InlineKeyboardButton("🚫 حظر المستخدمين", callback_data="admin_ban_users")],
        [InlineKeyboardButton("🔇 كتم المستخدمين", callback_data="admin_mute_users")],
        [InlineKeyboardButton("⬆️ ترقية المستخدمين", callback_data="admin_promote_users")],
        [InlineKeyboardButton("📊 إحصائيات الإشراف", callback_data="admin_moderation_stats")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
    ]

    message = (
        "🛡️ <b>لوحة الإشراف والإدارة</b>\n"
        f"════════════════════════════\n\n"
        "👇 اختر العملية المراد تنفيذها:\n\n"
        "🚫 <b>الحظر:</b> منع الوصول نهائياً\n"
        "🔇 <b>الكتم:</b> منع التفاعل مؤقتاً\n"
        "⬆️ <b>الترقية:</b> رفع الرتبة\n"
        "📊 <b>الإحصائيات:</b> عرض النشاط"
    )

    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def admin_ban_users(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """إدارة جرد المستخدمين المحظورين"""
    query = update.callback_query
    await query.answer()

    blocked_users = db.get_blocked_users()

    if not blocked_users:
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_moderation_panel")]]
        await query.edit_message_text(
            "✅ لا توجد مستخدمون محظورون حالياً",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        return

    message = "🚫 <b>المستخدمون المحظورون</b>\n" + "════════════════════════════" + "\n\n"

    for user in blocked_users[:10]:  # عرض أول 10 فقط
        user_id = user[0]
        username = user[1] or "بدون اسم"
        message += f"👤 {username}\n💳 ID: <code>{user_id}</code>\n\n"

    message += f"\n📊 الإجمالي: {len(blocked_users)}"

    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_moderation_panel")]]
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def admin_mute_users(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """معالج كتم المستخدمين"""
    query = update.callback_query
    await query.answer()

    # جلب قائمة المستخدمين النشطين
    all_users = db.get_all_users()
    approved = [u for u in all_users if u[4] == 'approved']

    if not approved:
        await query.edit_message_text(
            f"════════════════════════════\n"
            f"🔇 <b>كتم المستخدمين</b>\n"
            f"════════════════════════════\n\n"
            f"❌ لا يوجد مستخدمون نشطون",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data="admin_moderation_panel")]
            ])
        )
        return

    text = (
        f"════════════════════════════\n"
        f"🔇 <b>كتم المستخدم</b>\n"
        f"════════════════════════════\n\n"
        f"اختر المستخدم للكتم:\n"
    )
    keyboard = []
    for user in approved[:8]:
        uid = user[0]
        uname = user[1] or f"ID:{uid}"
        keyboard.append([InlineKeyboardButton(
            f"👤 @{uname}",
            callback_data=f"mute_select_{uid}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_moderation_panel")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    context.user_data['action'] = 'mute'


async def admin_promote_users(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """معالج ترقية المستخدمين"""
    query = update.callback_query
    await query.answer()

    all_users = db.get_all_users()
    approved = [u for u in all_users if u[4] == 'approved']

    if not approved:
        await query.edit_message_text(
            f"════════════════════════════\n"
            f"⬆️ <b>ترقية المستخدم</b>\n"
            f"════════════════════════════\n\n"
            f"❌ لا يوجد مستخدمون نشطون",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data="admin_moderation_panel")]
            ])
        )
        return

    text = (
        f"════════════════════════════\n"
        f"⬆️ <b>ترقية المستخدم</b>\n"
        f"════════════════════════════\n\n"
        f"اختر المستخدم للترقية:\n"
    )
    keyboard = []
    for user in approved[:8]:
        uid = user[0]
        uname = user[1] or f"ID:{uid}"
        role = user[3] or 'user'
        keyboard.append([InlineKeyboardButton(
            f"👤 @{uname} ({role})",
            callback_data=f"promote_select_{uid}"
        )])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_moderation_panel")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    context.user_data['action'] = 'promote'


async def admin_moderation_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """عرض إحصائيات الإشراف"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    stats = AdminModeration.get_moderation_stats(db, user_id)
    blocked = db.get_blocked_users()

    message = (
        "📊 <b>إحصائيات الإشراف</b>\n"
        f"════════════════════════════\n\n"
        f"🚫 المحظورون: {len(blocked)}\n"
        f"🔇 المكتومون: {stats.get('total_muted', 0)}\n"
        f"📝 الإجراءات اليوم: {stats.get('actions_today', 0)}\n\n"
        f"────────────────────────────\n"
        "⌚ آخر تحديث: الآن"
    )

    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_moderation_panel")]]
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


# ═══════════════════════════════════════════════════════════════════════════
# معالجات الدفع ونجوم تلجرام
# ═══════════════════════════════════════════════════════════════════════════

async def hosting_purchase_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """
    قائمة شراء وقت الاستضافة الإضافي 💳
    """
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    # استخراج معرف البوت من callback_data
    bot_id = context.user_data.get('selected_bot_id', 1)

    keyboard = [
        [InlineKeyboardButton(
            "📅 أسبوع (7 أيام) - 5 ⭐",
            callback_data=f"buy_hosting_week_{bot_id}"
        )],
        [InlineKeyboardButton(
            "📆 شهر (30 يوم) - 15 ⭐",
            callback_data=f"buy_hosting_month_{bot_id}"
        )],
        [InlineKeyboardButton(
            "📊 3 أشهر - 40 ⭐",
            callback_data=f"buy_hosting_3months_{bot_id}"
        )],
        [InlineKeyboardButton(
            "👑 سنة كاملة - 120 ⭐",
            callback_data=f"buy_hosting_year_{bot_id}"
        )],
        [InlineKeyboardButton("💝 تبرع", callback_data="donate_stars")],
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"manage_{bot_id}")]
    ]

    message = (
        "🕥 <b>شراء وقت استضافة إضافي</b>\n"
        f"════════════════════════════\n\n"
        "⭐ اختر الباقة المناسبة:\n\n"
        "💡 <i>سيتم تحديث الوقت تلقائياً بعد الدفع</i>"
    )

    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def donate_stars_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """
    معالج التبرعات بنجوم تلجرام 💝
    """
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("1 ⭐", callback_data="donate_amount_1")],
        [InlineKeyboardButton("5 ⭐", callback_data="donate_amount_5")],
        [InlineKeyboardButton("10 ⭐", callback_data="donate_amount_10")],
        [InlineKeyboardButton("25 ⭐", callback_data="donate_amount_25")],
        [InlineKeyboardButton("تحديد مبلغ", callback_data="donate_custom")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]
    ]

    message = (
        "💝 <b>دعم المشروع بالتبرع</b>\n"
        f"════════════════════════════\n\n"
        "❤️ ساهم في تطوير NeurHostX!\n\n"
        "كل نجم يساعد في:\n"
        "✨ تحسين الخدمات\n"
        "🚀 إضافة ميزات جديدة\n"
        "🛡️ تحسين الأمان\n\n"
        "👇 اختر المبلغ:"
    )

    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


# ═══════════════════════════════════════════════════════════════════════════
# معالجات الإشعارات الذكية
# ═══════════════════════════════════════════════════════════════════════════

async def smart_notifications_preview(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """
    معاينة الإشعارات الذكية 📢
    """
    query = update.callback_query
    await query.answer()

    # الحصول على إشعار عشوائي
    notification = SmartNotifications.get_random_notification()

    if not notification:
        await query.answer("❌ خطأ في جلب الإشعار", show_alert=True)
        return

    keyboard = [
        [InlineKeyboardButton("🔄 إشعار آخر", callback_data="smart_notifications_preview")],
        [InlineKeyboardButton("📊 الفئات", callback_data="notification_categories")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="settings")]
    ]

    formatted_msg = SmartNotifications.format_notification_message(notification)

    await query.edit_message_text(
        formatted_msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def notification_categories(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """
    عرض فئات الإشعارات المختلفة 📂
    """
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("🚀 التفاعل والعودة", callback_data="notif_cat_engagement")],
        [InlineKeyboardButton("🎁 عروض ترويجية", callback_data="notif_cat_promotion")],
        [InlineKeyboardButton("⚠️ تحذيرات", callback_data="notif_cat_warning")],
        [InlineKeyboardButton("🆕 تحديثات", callback_data="notif_cat_update")],
        [InlineKeyboardButton("🏆 إنجازات", callback_data="notif_cat_achievement")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="smart_notifications_preview")]
    ]

    message = (
        "📂 <b>فئات الإشعارات</b>\n"
        f"════════════════════════════\n\n"
        "اختر فئة لعرض أمثلة:\n\n"
        "🚀 <b>التفاعل:</b> رسائل لجعلك نشطاً\n"
        "🎁 <b>عروض:</b> خصومات وعروض خاصة\n"
        "⚠️ <b>تحذيرات:</b> تنبيهات مهمة\n"
        "🆕 <b>تحديثات:</b> أخبار النظام\n"
        "🏆 <b>إنجازات:</b> مكافآت وإنجازات"
    )

    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


# ═══════════════════════════════════════════════════════════════════════════
# معالجات أمان محسنة
# ═══════════════════════════════════════════════════════════════════════════

async def check_user_status(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """
    التحقق من حالة المستخدم (محظور، مكتوم، إلخ)
    """
    user_id = update.effective_user.id

    user = db.get_user(user_id)
    if not user:
        return None

    status = user[9]  # status column

    if status == 'blocked':
        return {
            'allowed': False,
            'reason': '🚫 حسابك محظور'
        }

    # التحقق من الكتم
    is_muted, mute_info = AdminModeration.is_user_muted(db, user_id)
    if is_muted:
        return {
            'allowed': False,
            'reason': f'🔇 أنت مكتوم حالياً\n\n{mute_info}'
        }

    return {
        'allowed': True,
        'reason': None
    }


# ═══════════════════════════════════════════════════════════════════════════
# معالجات مبلغ التبرع - إرسال فاتورة فعلية
# ═══════════════════════════════════════════════════════════════════════════

async def donate_amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """معالج اختيار مبلغ التبرع وإرسال الفاتورة"""
    query = update.callback_query
    await query.answer()

    data = query.data  # donate_amount_1 / donate_amount_5 etc
    try:
        amount = int(data.replace("donate_amount_", ""))
    except Exception:
        await query.answer("❌ مبلغ غير صحيح", show_alert=True)
        return

    from telegram import LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup
    stars_map = {1: "⭐", 5: "⭐⭐⭐⭐⭐", 10: "✨", 25: "💎"}
    star_icon = stars_map.get(amount, "⭐")

    prices = [LabeledPrice(label=f"دعم NeurHostX {star_icon}", amount=amount)]

    try:
        await query.message.reply_text(
            f"════════════════════════════\n"
            f"💝 <b>شكراً على دعمك!</b>\n"
            f"════════════════════════════\n\n"
            f"⭐ المبلغ: <b>{amount} نجمة</b>\n\n"
            f"💡 سيتم فتح نافذة الدفع...",
            parse_mode="HTML"
        )
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title=f"💝 دعم NeurHostX",
            description=f"تبرع بـ {amount} نجمة لدعم تطوير المشروع {star_icon}",
            payload=f"donate_{query.from_user.id}_{amount}",
            provider_token="",
            currency="XTR",
            prices=prices,
        )
    except Exception as e:
        logger.error(f"خطأ في إرسال فاتورة التبرع: {e}")
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="donate_stars")]]
        await query.edit_message_text(
            f"════════════════════════════\n"
            f"════════════════════════════\n"
        f"❌ <b>خطأ في إرسال الفاتورة</b>\n"
        f"════════════════════════════\n\n"
            f"حاول مرة أخرى أو تواصل مع الدعم.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )


async def donate_custom_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """معالج تحديد مبلغ مخصص"""
    query = update.callback_query
    await query.answer()
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [
        [
            InlineKeyboardButton("50 ⭐", callback_data="donate_amount_50"),
            InlineKeyboardButton("100 ⭐", callback_data="donate_amount_100"),
        ],
        [
            InlineKeyboardButton("250 ⭐", callback_data="donate_amount_250"),
            InlineKeyboardButton("500 ⭐", callback_data="donate_amount_500"),
        ],
        [InlineKeyboardButton("🔙 رجوع", callback_data="donate_stars")],
    ]
    await query.edit_message_text(
        f"════════════════════════════\n"
        f"════════════════════════════\n"
        f"💎 <b>تبرع بمبلغ أكبر</b>\n"
        f"════════════════════════════\n\n"
        f"اختر المبلغ المناسب:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


# ═══════════════════════════════════════════════════════════════════════════
# معالج شراء وقت الاستضافة - إرسال فاتورة فعلية
# ═══════════════════════════════════════════════════════════════════════════

HOSTING_PACKAGES = {
    "week":    {"days": 7,   "stars": 5,   "label": "أسبوع (7 أيام)"},
    "month":   {"days": 30,  "stars": 15,  "label": "شهر (30 يوم)"},
    "3months": {"days": 90,  "stars": 40,  "label": "3 أشهر"},
    "year":    {"days": 365, "stars": 120, "label": "سنة كاملة"},
}


async def buy_hosting_time(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """
    معالج شراء وقت الاستضافة - يرسل فاتورة نجوم تيليجرام حقيقية
    callback pattern: buy_hosting_{period}_{bot_id}
    """
    query = update.callback_query
    await query.answer()
    from telegram import LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup

    try:
        # parse: buy_hosting_week_5 or buy_hosting_3months_5
        data = query.data  # buy_hosting_year_3
        # strip prefix
        rest = data[len("buy_hosting_"):]  # year_3
        # split from right to get bot_id
        parts = rest.rsplit("_", 1)
        if len(parts) != 2:
            await query.answer("❌ خطأ في البيانات", show_alert=True)
            return

        period, bot_id_str = parts[0], parts[1]
        bot_id = int(bot_id_str)

        pkg = HOSTING_PACKAGES.get(period)
        if not pkg:
            await query.answer("❌ الباقة غير صحيحة", show_alert=True)
            return

        bot = db.get_bot(bot_id)
        if not bot:
            await query.answer("❌ البوت غير موجود", show_alert=True)
            return

        # ترميز الـ payload
        payload = f"hosting_{update.effective_user.id}_{bot_id}_{period}"
        prices = [LabeledPrice(label=f"⭐ استضافة {pkg['label']}", amount=pkg["stars"])]

        await query.message.reply_text(
            f"════════════════════════════\n"
            f"🕥 <b>شراء وقت استضافة</b>\n"
            f"════════════════════════════\n\n"
            f"🤖 البوت: <b>{bot[3]}</b>\n"
            f"📦 الباقة: <b>{pkg['label']}</b>\n"
            f"⭐ السعر: <b>{pkg['stars']} نجمة</b>\n\n"
            f"💡 جاري فتح نافذة الدفع...",
            parse_mode="HTML"
        )

        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title=f"⭐ استضافة {pkg['label']}",
            description=f"إضافة {pkg['days']} يوم لبوت {bot[3]}",
            payload=payload,
            provider_token="",
            currency="XTR",
            prices=prices,
        )

    except Exception as e:
        logger.error(f"خطأ في شراء وقت استضافة: {e}")
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data=f"hosting_purchase_{bot_id}")]]
        await query.edit_message_text(
            f"════════════════════════════\n"
            f"════════════════════════════\n"
        f"❌ <b>خطأ في الدفع</b>\n"
        f"════════════════════════════\n\n"
            f"السبب: {str(e)[:100]}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
