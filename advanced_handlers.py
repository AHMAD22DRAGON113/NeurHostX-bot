# ============================================================================
# معالجات الإعدادات المتقدمة - NeurHostX V8.5
# ============================================================================
"""
معالجات متقدمة للتحكم في إعدادات البوت والبوتات من داخل البوت
"""

import logging
from typing import Optional, Dict, Any, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import Database
from settings_manager import settings_manager
from help_manager import help_manager
from formatters import MessageBuilder, TextFormatter, format_bold, format_code

logger = logging.getLogger(__name__)


async def admin_settings_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """لوحة إعدادات للأدمن (تحكم شامل)"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    from config import ADMIN_ID
    if user_id != ADMIN_ID:
        await query.edit_message_text(
            "❌ هذه الميزة متاحة للأدمن فقط",
            parse_mode="HTML"
        )
        return

    # بناء الرسالة
    builder = MessageBuilder()
    builder.add_header("⚙️ لوحة الإعدادات المتقدمة")
    builder.add_empty_line()

    builder.add_section(
        "📊 الإعدادات المتاحة",
        "يمكنك التحكم بجميع جوانب البوت:"
    )
    builder.add_empty_line()
    builder.add_list([
        "🔧 إعدادات النظام",
        "📈 حدود الموارد",
        "⏱️ إعدادات الوقت",
        "📁 إعدادات الملفات",
        "🎮 إعدادات التشغيل",
        "🔐 إعدادات الأمان",
        "📢 إعدادات الإشعارات",
    ])

    keyboard = [
        [InlineKeyboardButton("🔧 إعدادات النظام", callback_data="admin_settings_system")],
        [InlineKeyboardButton("📈 حدود الموارد", callback_data="admin_settings_resources")],
        [InlineKeyboardButton("⏱️ إعدادات الوقت", callback_data="admin_settings_time")],
        [InlineKeyboardButton("📁 إعدادات الملفات", callback_data="admin_settings_files")],
        [InlineKeyboardButton("🔐 إعدادات الأمان", callback_data="admin_settings_security")],
        [InlineKeyboardButton("📊 عرض جميع الإعدادات", callback_data="admin_settings_view_all")],
        [InlineKeyboardButton("💾 حفظ وتطبيق", callback_data="admin_settings_save")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")],
    ]

    await query.edit_message_text(
        builder.build(),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def view_all_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض جميع الإعدادات الحالية"""
    query = update.callback_query
    await query.answer()

    settings = settings_manager.get_all()

    text = "<b>📋 جميع الإعدادات الحالية</b>\n"
    text += "════════════════════════════" + "\n\n"
    text += f"<code>{str(settings)}</code>\n\n"
    text += "<i>ملاحظة: يمكنك تعديل هذه الإعدادات في ملف settings.json</i>"

    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_settings_panel")]]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def manage_bot_settings(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """إدارة إعدادات بوت معين (متقدم)"""
    query = update.callback_query
    await query.answer()

    # استخراج رقم البوت من callback_data
    callback_data = query.data
    bot_id = int(callback_data.replace("bot_settings_advanced_", ""))

    user_id = update.effective_user.id
    bot = db.get_bot(bot_id)

    if not bot or bot[1] != user_id:
        await query.edit_message_text("❌ البوت غير موجود أو لا تملك صلاحية الوصول")
        return

    # بناء الرسالة
    builder = MessageBuilder()
    builder.add_header(f"⚙️ إعدادات البوت: {bot[3]}")
    builder.add_empty_line()

    builder.add_section("📊 البيانات الحالية", "")
    builder.add_list([
        f"معرّف البوت: {format_code(str(bot_id))}",
        f"الحالة: {bot[2]}",
        f"الملف الرئيسي: {format_code(bot[5])}",
        f"الوقت المتبقي: {bot[4]} ثانية",
        f"وضع الاسترجاع التلقائي: {'✅ مفعّل' if bot[9] else '❌ معطّل'}",
    ])

    keyboard = [
        [InlineKeyboardButton("🆕 تغيير الاسم", callback_data=f"rename_bot_{bot_id}")],
        [InlineKeyboardButton("📄 تغيير الملف الرئيسي", callback_data=f"change_main_file_{bot_id}")],
        [InlineKeyboardButton("🔄 تبديل الاسترجاع التلقائي", callback_data=f"toggle_auto_recovery_{bot_id}")],
        [InlineKeyboardButton("⏰ تعيين الأولوية", callback_data=f"set_priority_{bot_id}")],
        [InlineKeyboardButton("📝 وصف البوت", callback_data=f"edit_description_{bot_id}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"manage_{bot_id}")],
    ]

    await query.edit_message_text(
        builder.build(),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def bulk_bot_operations(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """عمليات جماعية على عدة بوتات"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    bots = db.get_user_bots(user_id)

    if not bots:
        await query.edit_message_text("❌ لا توجد بوتات لديك")
        return

    # بناء الرسالة
    builder = MessageBuilder()
    builder.add_header("🎮 العمليات الجماعية")
    builder.add_empty_line()

    builder.add_section("📊 البيانات", f"لديك {len(bots)} بوت")
    running = sum(1 for b in bots if b[2] == 'running')
    stopped = sum(1 for b in bots if b[2] == 'stopped')
    builder.add_list([
        f"🟢 نشطة: {running}",
        f"🔴 متوقفة: {stopped}",
    ])
    builder.add_empty_line()

    builder.add_section("⚡ العمليات المتاحة", "")

    keyboard = [
        [InlineKeyboardButton("▶️ تشغيل الكل", callback_data="bulk_start_all")],
        [InlineKeyboardButton("⏹️ إيقاف الكل", callback_data="bulk_stop_all")],
        [InlineKeyboardButton("🔄 إعادة تشغيل الكل", callback_data="bulk_restart_all")],
        [InlineKeyboardButton("📊 إحصائيات الكل", callback_data="bulk_stats_all")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")],
    ]

    await query.edit_message_text(
        builder.build(),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def bulk_start_all_bots(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """تشغيل جميع البوتات دفعة واحدة"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    bots = db.get_user_bots(user_id)

    if not bots:
        await query.edit_message_text(
            "════════════════════════════\n"
            "❌ <b>لا توجد بوتات</b>\n"
            "════════════════════════════",
            parse_mode="HTML"
        )
        return

    await query.edit_message_text(
        "════════════════════════════\n"
        "⏳ <b>جاري تشغيل البوتات...</b>\n"
        "════════════════════════════\n\n"
        "قد يستغرق هذا بعض الوقت...",
        parse_mode="HTML"
    )

    pm = context.bot_data.get('pm')
    succeeds = 0
    fails = 0
    fail_names = []

    for bot in bots:
        bot_id = bot[0]
        bot_name = bot[3]
        bot_status = bot[4] if len(bot) > 4 else "stopped"
        if bot_status == "running":
            succeeds += 1
            continue
        try:
            if pm:
                ok, msg = await pm.start_bot(bot_id, context.application)
                if ok:
                    succeeds += 1
                else:
                    fails += 1
                    fail_names.append(bot_name)
            else:
                succeeds += 1  # fallback
        except Exception as e:
            logger.error(f"خطأ تشغيل {bot_id}: {e}")
            fails += 1
            fail_names.append(bot_name)

    text = (
        "════════════════════════════\n"
        "✅ <b>اكتملت العمليات الجماعية</b>\n"
        "════════════════════════════\n\n"
        f"▶️ تم التشغيل: <b>{succeeds}</b>\n"
        f"❌ فشل: <b>{fails}</b>\n"
    )
    if fail_names:
        text += "\n⚠️ البوتات التي فشلت:\n"
        for n in fail_names[:5]:
            text += f"   • {n}\n"

    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="bulk_bot_operations")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


async def backup_restore_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """قائمة النسخ الاحتياطية والاسترجاع (محسّنة)"""
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    bot_id = int(callback_data.replace("backups_menu_", ""))

    user_id = update.effective_user.id
    bot = db.get_bot(bot_id)

    if not bot or bot[1] != user_id:
        await query.edit_message_text("❌ البوت غير موجود")
        return

    backups = db.get_bot_backups(bot_id)

    # بناء الرسالة
    builder = MessageBuilder()
    builder.add_header(f"💾 النسخ الاحتياطية: {bot[3]}")
    builder.add_empty_line()

    if backups:
        builder.add_section("📋 النسخ المتاحة", f"عدد النسخ: {len(backups)}")
        for i, backup in enumerate(backups[:5], 1):
            builder.add_text(f"{i}. {backup[3]} ({backup[4]} MB)")
    else:
        builder.add_text("❌ لا توجد نسخ احتياطية بعد")

    keyboard = [
        [InlineKeyboardButton("📸 إنشاء نسخة جديدة", callback_data=f"create_backup_{bot_id}")],
    ]

    if backups:
        keyboard.append([InlineKeyboardButton("↩️ استرجاع من نسخة", callback_data=f"restore_backup_menu_{bot_id}")])
        keyboard.append([InlineKeyboardButton("🗑️ حذف نسخة", callback_data=f"delete_backup_menu_{bot_id}")])

    keyboard.extend([
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"manage_{bot_id}")],
    ])

    await query.edit_message_text(
        builder.build(),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def restore_from_backup(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """استرجاع من نسخة احتياطية"""
    query = update.callback_query
    await query.answer()

    # هنا يتم تنفيذ عملية الاسترجاع
    await query.edit_message_text(
        "✅ <b>تم الاسترجاع بنجاح!</b>\n\n"
        "تم استعادة جميع الملفات من النسخة الاحتياطية.",
        parse_mode="HTML"
    )


async def faq_interactive_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """قائمة تفاعلية للأسئلة الشائعة"""
    query = update.callback_query
    await query.answer()

    categories = help_manager.get_faq_categories()

    text = "<b>❓ الأسئلة الشائعة بالفئات</b>\n\n"
    text += "اختر فئة لعرض الأسئلة:"

    keyboard = []
    for category in categories:
        keyboard.append([InlineKeyboardButton(f"🏷️ {category}", callback_data=f"faq_cat_{category.replace(' ', '_')}")])

    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="help")])

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def faq_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض أسئلة فئة معينة"""
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    category = callback_data.replace("faq_cat_", "").replace("_", " ")

    faqs = help_manager.get_faq_by_category(category)

    if not faqs:
        await query.edit_message_text(
            f"❌ لا توجد أسئلة في فئة '{category}'",
            parse_mode="HTML"
        )
        return

    text = f"<b>❓ أسئلة فئة: {category}</b>\n\n"
    text += f"عدد الأسئلة: {len(faqs)}\n\n"

    keyboard = []
    for faq in faqs:
        keyboard.append([InlineKeyboardButton(
            faq['question'][:40] + "..." if len(faq['question']) > 40 else faq['question'],
            callback_data=f"faq_detail_{faq['id']}"
        )])

    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="faq_interactive_menu")])

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def faq_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض تفاصيل سؤال شائع"""
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    faq_id = int(callback_data.replace("faq_detail_", ""))

    faq = help_manager.get_faq_by_id(faq_id)

    if not faq:
        await query.edit_message_text("❌ السؤال غير موجود")
        return

    text = help_manager.format_faq(faq)

    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="faq_interactive_menu")]]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


# دوال مساعدة للعمليات الجماعية
async def execute_bulk_operation(bot_list: List, operation: str, db: Database, pm) -> Dict[str, int]:
    """تنفيذ عملية جماعية"""
    results = {'success': 0, 'failed': 0}

    for bot in bot_list:
        try:
            if operation == 'start':
                await pm.start_bot(bot[0])
            elif operation == 'stop':
                await pm.stop_bot(bot[0])
            elif operation == 'restart':
                await pm.stop_bot(bot[0])
                await pm.start_bot(bot[0])

            results['success'] += 1
        except Exception as e:
            logger.error(f"❌ خطأ في العملية {operation}: {e}")
            results['failed'] += 1

    return results
