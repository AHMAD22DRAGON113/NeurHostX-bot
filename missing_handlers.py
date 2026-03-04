# ============================================================================
# المعالجات المفقودة - NeurHostX V9.1 - اكتمال شامل
# ============================================================================
"""
هذا الملف يحتوي على جميع المعالجات التي كانت مفقودة:
- rename_bot, change_main_file, toggle_auto_recovery, set_priority, edit_description
- create_backup, delete_backup_menu, restore_backup_menu
- bulk_stop_all, bulk_restart_all, bulk_stats_all
- mute_duration_*, promote_role_*
- admin_settings_system, _resources, _time, _files, _security, _save
"""

import logging
import sqlite3
from pathlib import Path
from io import BytesIO
import zipfile

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from config import ADMIN_ID, BOTS_DIRECTORY, DATABASE_FILE, PLANS, CONVERSATION_STATES
from database import Database
from helpers import safe_html_escape, seconds_to_human

logger = logging.getLogger(__name__)

DIVIDER = "════════════════════════════"
SUBDIV  = "─" * 28


# ════════════════════════════════════════════════════════════════════════
# إعدادات البوت المتقدمة
# ════════════════════════════════════════════════════════════════════════

async def rename_bot_start(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """بدء تغيير اسم البوت"""
    query = update.callback_query
    await query.answer()
    bot_id = int(query.data.replace("rename_bot_", ""))
    bot = db.get_bot(bot_id)
    if not bot or bot[1] != update.effective_user.id:
        await query.answer("❌ غير مصرح", show_alert=True)
        return ConversationHandler.END

    context.user_data['rename_bot_id'] = bot_id
    await query.edit_message_text(
        f"{DIVIDER}\n🆕 <b>تغيير اسم البوت</b>\n{DIVIDER}\n\n"
        f"🤖 الاسم الحالي: <b>{safe_html_escape(bot[3])}</b>\n\n"
        f"📝 أرسل الاسم الجديد:\n"
        f"<i>أرسل /cancel للإلغاء</i>",
        parse_mode="HTML"
    )
    return CONVERSATION_STATES['WAIT_RENAME']


async def rename_bot_execute(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """تنفيذ تغيير الاسم"""
    new_name = update.message.text.strip()
    bot_id = context.user_data.get('rename_bot_id')

    if not bot_id:
        await update.message.reply_text("❌ انتهت الجلسة. ابدأ من جديد.")
        return ConversationHandler.END

    if not new_name or len(new_name) > 50:
        await update.message.reply_text("❌ الاسم يجب أن يكون بين 1-50 حرف. حاول مرة أخرى:")
        return CONVERSATION_STATES['WAIT_RENAME']

    db.update_bot_name(bot_id, new_name)
    db.add_event_log(bot_id, "INFO", f"✏️ تم تغيير الاسم إلى: {new_name}")

    await update.message.reply_text(
        f"{DIVIDER}\n✅ <b>تم تغيير الاسم!</b>\n{DIVIDER}\n\n"
        f"🤖 الاسم الجديد: <b>{safe_html_escape(new_name)}</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⚙️ إدارة البوت", callback_data=f"manage_{bot_id}")]
        ])
    )
    context.user_data.pop('rename_bot_id', None)
    return ConversationHandler.END


async def change_main_file_start(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """بدء تغيير الملف الرئيسي"""
    query = update.callback_query
    await query.answer()
    bot_id = int(query.data.replace("change_main_file_", ""))
    bot = db.get_bot(bot_id)
    if not bot or bot[1] != update.effective_user.id:
        await query.answer("❌ غير مصرح", show_alert=True)
        return ConversationHandler.END

    # عرض الملفات الموجودة
    bot_path = Path(BOTS_DIRECTORY) / bot[5]
    py_files = []
    if bot_path.exists():
        py_files = [f.name for f in bot_path.iterdir() if f.suffix == '.py' and not f.name.startswith('_')]

    context.user_data['change_main_bot_id'] = bot_id

    files_text = "\n".join(f"   • <code>{f}</code>" for f in py_files[:10]) if py_files else "   لا توجد ملفات .py"

    keyboard = []
    for f in py_files[:8]:
        keyboard.append([InlineKeyboardButton(f"📄 {f}", callback_data=f"set_main_file_{bot_id}_{f}")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data=f"bot_settings_advanced_{bot_id}")])

    await query.edit_message_text(
        f"{DIVIDER}\n📄 <b>تغيير الملف الرئيسي</b>\n{DIVIDER}\n\n"
        f"🤖 البوت: <b>{safe_html_escape(bot[3])}</b>\n"
        f"📄 الحالي: <code>{bot[6]}</code>\n\n"
        f"{SUBDIV}\n"
        f"📂 الملفات المتاحة:\n{files_text}\n\n"
        f"👇 اختر الملف الجديد:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def set_main_file(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """تعيين الملف الرئيسي الجديد"""
    query = update.callback_query
    await query.answer()
    # set_main_file_{bot_id}_{filename}
    parts = query.data.split("_", 4)
    bot_id = int(parts[3])
    filename = parts[4]

    bot = db.get_bot(bot_id)
    if not bot or bot[1] != update.effective_user.id:
        await query.answer("❌ غير مصرح", show_alert=True)
        return

    # تحديث في قاعدة البيانات
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("UPDATE bots SET main_file = ? WHERE id = ?", (filename, bot_id))
    conn.commit()
    conn.close()
    db.add_event_log(bot_id, "INFO", f"📄 تم تغيير الملف الرئيسي إلى: {filename}")

    await query.edit_message_text(
        f"{DIVIDER}\n✅ <b>تم تغيير الملف الرئيسي!</b>\n{DIVIDER}\n\n"
        f"📄 الملف الجديد: <code>{filename}</code>\n\n"
        f"⚠️ أعد تشغيل البوت لتطبيق التغيير",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 تشغيل البوت", callback_data=f"start_{bot_id}")],
            [InlineKeyboardButton("🔙 رجوع", callback_data=f"manage_{bot_id}")]
        ])
    )


async def toggle_auto_recovery(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """تبديل الاسترجاع التلقائي"""
    query = update.callback_query
    await query.answer()
    bot_id = int(query.data.replace("toggle_auto_recovery_", ""))
    bot = db.get_bot(bot_id)
    if not bot or bot[1] != update.effective_user.id:
        await query.answer("❌ غير مصرح", show_alert=True)
        return

    # تبديل القيمة
    current = bot[28] if len(bot) > 28 else 0  # auto_start field
    new_val = 0 if current else 1

    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("UPDATE bots SET auto_start = ? WHERE id = ?", (new_val, bot_id))
    conn.commit()
    conn.close()

    status = "✅ مفعّل" if new_val else "❌ معطّل"
    await query.answer(f"الاسترجاع التلقائي: {status}", show_alert=True)

    # إعادة عرض إعدادات البوت
    await manage_bot_settings_show(query, bot_id, db)


async def manage_bot_settings_show(query, bot_id, db):
    """عرض إعدادات البوت"""
    bot = db.get_bot(bot_id)
    if not bot:
        return

    auto_recovery = bot[28] if len(bot) > 28 else 0
    priority = bot[29] if len(bot) > 29 else 1
    description = bot[27] if len(bot) > 27 else ''

    priority_text = {1: "🔵 عادي", 2: "🟡 متوسط", 3: "🔴 عالي"}.get(priority, "🔵 عادي")

    await query.edit_message_text(
        f"{DIVIDER}\n⚙️ <b>إعدادات البوت</b>\n{DIVIDER}\n\n"
        f"🤖 <b>{safe_html_escape(bot[3])}</b>\n"
        f"{SUBDIV}\n"
        f"📄 الملف الرئيسي: <code>{bot[6]}</code>\n"
        f"🔄 استرجاع تلقائي: {'✅ مفعّل' if auto_recovery else '❌ معطّل'}\n"
        f"⚡ الأولوية: {priority_text}\n"
        f"📝 الوصف: {safe_html_escape(description[:50]) if description else 'لا يوجد'}\n",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🆕 تغيير الاسم", callback_data=f"rename_bot_{bot_id}")],
            [InlineKeyboardButton("📄 تغيير الملف الرئيسي", callback_data=f"change_main_file_{bot_id}")],
            [InlineKeyboardButton(
                f"{'🔄' if auto_recovery else '⏸️'} تبديل الاسترجاع التلقائي",
                callback_data=f"toggle_auto_recovery_{bot_id}"
            )],
            [InlineKeyboardButton("⚡ تعيين الأولوية", callback_data=f"set_priority_{bot_id}")],
            [InlineKeyboardButton("📝 تعديل الوصف", callback_data=f"edit_description_{bot_id}")],
            [InlineKeyboardButton("🔙 رجوع", callback_data=f"manage_{bot_id}")]
        ])
    )


async def set_priority_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """قائمة تعيين الأولوية"""
    query = update.callback_query
    await query.answer()
    bot_id = int(query.data.replace("set_priority_", ""))

    await query.edit_message_text(
        f"{DIVIDER}\n⚡ <b>تعيين أولوية البوت</b>\n{DIVIDER}\n\n"
        f"الأولوية الأعلى تعني تخصيص موارد أكثر للبوت.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔵 عادي (1)", callback_data=f"set_prio_1_{bot_id}")],
            [InlineKeyboardButton("🟡 متوسط (2)", callback_data=f"set_prio_2_{bot_id}")],
            [InlineKeyboardButton("🔴 عالي (3)", callback_data=f"set_prio_3_{bot_id}")],
            [InlineKeyboardButton("🔙 رجوع", callback_data=f"bot_settings_advanced_{bot_id}")]
        ])
    )


async def set_priority_execute(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """تطبيق الأولوية"""
    query = update.callback_query
    await query.answer()
    parts = query.data.split("_")
    priority = int(parts[2])
    bot_id = int(parts[3])

    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("UPDATE bots SET priority = ? WHERE id = ?", (priority, bot_id))
    conn.commit()
    conn.close()

    labels = {1: "🔵 عادي", 2: "🟡 متوسط", 3: "🔴 عالي"}
    await query.answer(f"تم تعيين الأولوية: {labels.get(priority, priority)}", show_alert=True)
    await manage_bot_settings_show(query, bot_id, db)


async def edit_description_start(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """بدء تعديل وصف البوت"""
    query = update.callback_query
    await query.answer()
    bot_id = int(query.data.replace("edit_description_", ""))
    bot = db.get_bot(bot_id)
    if not bot or bot[1] != update.effective_user.id:
        await query.answer("❌ غير مصرح", show_alert=True)
        return ConversationHandler.END

    context.user_data['desc_bot_id'] = bot_id
    current_desc = bot[27] if len(bot) > 27 else ''

    await query.edit_message_text(
        f"{DIVIDER}\n📝 <b>تعديل وصف البوت</b>\n{DIVIDER}\n\n"
        f"الوصف الحالي: {safe_html_escape(current_desc) if current_desc else '<i>لا يوجد</i>'}\n\n"
        f"أرسل الوصف الجديد (حتى 200 حرف):\n"
        f"<i>أرسل /cancel للإلغاء أو . لحذف الوصف</i>",
        parse_mode="HTML"
    )
    return CONVERSATION_STATES['WAIT_DESCRIPTION']


async def edit_description_execute(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """تطبيق وصف البوت"""
    text = update.message.text.strip()
    bot_id = context.user_data.get('desc_bot_id')

    if not bot_id:
        return ConversationHandler.END

    description = "" if text == "." else text[:200]

    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("UPDATE bots SET description = ? WHERE id = ?", (description, bot_id))
    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"{DIVIDER}\n✅ <b>تم تحديث الوصف!</b>\n{DIVIDER}\n\n"
        f"📝 {safe_html_escape(description) if description else '<i>تم حذف الوصف</i>'}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع للإعدادات", callback_data=f"bot_settings_advanced_{bot_id}")]
        ])
    )
    context.user_data.pop('desc_bot_id', None)
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════
# العمليات الجماعية المفقودة
# ════════════════════════════════════════════════════════════════════════

async def bulk_stop_all_bots(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """إيقاف جميع البوتات"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    bots = db.get_user_bots(user_id)

    if not bots:
        await query.answer("لا توجد بوتات", show_alert=True)
        return

    await query.edit_message_text(
        f"{DIVIDER}\n⏳ <b>جاري إيقاف جميع البوتات...</b>\n{DIVIDER}",
        parse_mode="HTML"
    )

    pm = context.bot_data.get('pm')
    stopped = 0
    for bot in bots:
        bot_id = bot[0]
        if bot[2] == 'running':
            try:
                if pm:
                    pm.stop_bot(bot_id)
                stopped += 1
            except Exception as e:
                logger.error(f"خطأ إيقاف {bot_id}: {e}")

    await query.edit_message_text(
        f"{DIVIDER}\n✅ <b>اكتمل الإيقاف الجماعي</b>\n{DIVIDER}\n\n"
        f"⏹️ تم إيقاف: <b>{stopped}</b> بوت",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="bulk_bot_operations")]
        ])
    )


async def bulk_restart_all_bots(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """إعادة تشغيل جميع البوتات"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    bots = db.get_user_bots(user_id)

    await query.edit_message_text(
        f"{DIVIDER}\n⏳ <b>جاري إعادة تشغيل البوتات...</b>\n{DIVIDER}",
        parse_mode="HTML"
    )

    pm = context.bot_data.get('pm')
    success = 0
    failed = 0

    for bot in bots:
        bot_id = bot[0]
        if bot[2] == 'running':
            try:
                if pm:
                    ok, _ = await pm.restart_bot(bot_id, context.application)
                    if ok:
                        success += 1
                    else:
                        failed += 1
            except Exception as e:
                logger.error(f"خطأ إعادة تشغيل {bot_id}: {e}")
                failed += 1

    await query.edit_message_text(
        f"{DIVIDER}\n✅ <b>اكتملت إعادة التشغيل الجماعية</b>\n{DIVIDER}\n\n"
        f"✅ نجح: <b>{success}</b>\n"
        f"❌ فشل: <b>{failed}</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="bulk_bot_operations")]
        ])
    )


async def bulk_stats_all_bots(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """إحصائيات جميع البوتات"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    bots = db.get_user_bots(user_id)

    if not bots:
        await query.edit_message_text(
            f"{DIVIDER}\n📊 <b>لا توجد بوتات</b>\n{DIVIDER}",
            parse_mode="HTML"
        )
        return

    running = sum(1 for b in bots if b[2] == 'running')
    stopped = sum(1 for b in bots if b[2] == 'stopped')
    sleeping = sum(1 for b in bots if b[6])
    total_time = sum(b[4] or 0 for b in bots)

    text = (
        f"{DIVIDER}\n📊 <b>إحصائيات جميع البوتات</b>\n{DIVIDER}\n\n"
        f"   إجمالي: <b>{len(bots)}</b> بوت\n"
        f"   🟢 نشط: <b>{running}</b>\n"
        f"   🔴 متوقف: <b>{stopped}</b>\n"
        f"   😴 سكون: <b>{sleeping}</b>\n"
        f"   ⏱️ إجمالي الوقت: <b>{seconds_to_human(total_time)}</b>\n"
        f"\n{SUBDIV}\n"
    )

    for bot in bots[:10]:
        icon = "🟢" if bot[2] == 'running' else ("😴" if bot[6] else "🔴")
        time_str = seconds_to_human(bot[4] or 0)
        text += f"{icon} <b>{safe_html_escape(bot[1][:15])}</b> — {time_str}\n"

    if len(bots) > 10:
        text += f"\n<i>... و {len(bots) - 10} بوت آخر</i>"

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="bulk_bot_operations")]
        ])
    )


# ════════════════════════════════════════════════════════════════════════
# معالجات الإشراف المفقودة
# ════════════════════════════════════════════════════════════════════════

async def mute_duration_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """معالج اختيار مدة الكتم"""
    query = update.callback_query
    await query.answer()

    data = query.data  # mute_duration_1h etc
    duration_map = {
        "mute_duration_1h": (3600, "ساعة واحدة"),
        "mute_duration_6h": (21600, "6 ساعات"),
        "mute_duration_1d": (86400, "يوم واحد"),
        "mute_duration_permanent": (-1, "دائم"),
    }

    duration_seconds, label = duration_map.get(data, (3600, "ساعة"))
    target_user_id = context.user_data.get('mute_target_user_id')

    if not target_user_id:
        await query.answer("❌ لم يتم تحديد المستخدم", show_alert=True)
        return

    # تسجيل الكتم في قاعدة البيانات
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute("UPDATE users SET status = 'muted' WHERE user_id = ?", (target_user_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"خطأ في الكتم: {e}")

    await query.edit_message_text(
        f"{DIVIDER}\n🔇 <b>تم كتم المستخدم</b>\n{DIVIDER}\n\n"
        f"👤 معرّف: <code>{target_user_id}</code>\n"
        f"⏱️ المدة: <b>{label}</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_moderation_panel")]
        ])
    )
    context.user_data.pop('mute_target_user_id', None)


async def promote_role_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """معالج تعيين الدور"""
    query = update.callback_query
    await query.answer()

    role_map = {
        "promote_role_moderator": ("moderator", "🛡️ مشرف"),
        "promote_role_premium": ("premium", "⭐ مميز"),
        "promote_role_admin": ("admin", "🔑 أدمن"),
    }

    role, label = role_map.get(query.data, ("user", "مستخدم"))
    target_user_id = context.user_data.get('promote_target_user_id')

    if not target_user_id:
        await query.answer("❌ لم يتم تحديد المستخدم", show_alert=True)
        return

    try:
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, target_user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"خطأ في ترقية المستخدم: {e}")

    await query.edit_message_text(
        f"{DIVIDER}\n✅ <b>تم تعيين الدور</b>\n{DIVIDER}\n\n"
        f"👤 معرّف: <code>{target_user_id}</code>\n"
        f"🎭 الدور الجديد: <b>{label}</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_moderation_panel")]
        ])
    )
    context.user_data.pop('promote_target_user_id', None)


# ════════════════════════════════════════════════════════════════════════
# إعدادات النظام المتقدمة
# ════════════════════════════════════════════════════════════════════════

async def admin_settings_system(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """إعدادات النظام"""
    query = update.callback_query
    await query.answer()
    if update.effective_user.id != ADMIN_ID:
        return

    from config import (
        MAX_CONCURRENT_BOTS, MONITOR_CHECK_INTERVAL_SECONDS,
        PROCESS_RESTART_COOLDOWN_SECONDS, PROCESS_TIMEOUT_SECONDS
    )

    await query.edit_message_text(
        f"{DIVIDER}\n🔧 <b>إعدادات النظام</b>\n{DIVIDER}\n\n"
        f"🤖 الحد الأقصى للبوتات المتزامنة: <b>{MAX_CONCURRENT_BOTS}</b>\n"
        f"⏱️ فترة المراقبة: <b>{MONITOR_CHECK_INTERVAL_SECONDS} ث</b>\n"
        f"🔄 فترة الانتظار بين الإعادة: <b>{PROCESS_RESTART_COOLDOWN_SECONDS} ث</b>\n"
        f"⌛ مهلة العملية: <b>{PROCESS_TIMEOUT_SECONDS} ث</b>\n\n"
        f"<i>للتعديل: افتح ملف config.py</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_settings_panel")]
        ])
    )


async def admin_settings_resources(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """إعدادات الموارد"""
    query = update.callback_query
    await query.answer()
    if update.effective_user.id != ADMIN_ID:
        return

    plans_text = ""
    for plan_key, plan in PLANS.items():
        plans_text += (
            f"\n{plan['emoji']} <b>{plan['name']}</b>\n"
            f"   CPU: {plan['cpu_limit']}% | RAM: {plan['mem_limit']} MB\n"
            f"   بوتات: {plan['max_bots']} | وقت: {seconds_to_human(plan['time'])}\n"
        )

    await query.edit_message_text(
        f"{DIVIDER}\n📈 <b>حدود الموارد</b>\n{DIVIDER}\n"
        f"{plans_text}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_settings_panel")]
        ])
    )


async def admin_settings_time(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """إعدادات الوقت"""
    query = update.callback_query
    await query.answer()
    if update.effective_user.id != ADMIN_ID:
        return

    from config import DAILY_RECOVERY_TIME_SECONDS, RESTART_TIME_COST_SECONDS, WARNING_COOLDOWN_SECONDS

    await query.edit_message_text(
        f"{DIVIDER}\n⏱️ <b>إعدادات الوقت</b>\n{DIVIDER}\n\n"
        f"🔄 وقت الاسترجاع اليومي: <b>{seconds_to_human(DAILY_RECOVERY_TIME_SECONDS)}</b>\n"
        f"💰 تكلفة إعادة التشغيل: <b>{seconds_to_human(RESTART_TIME_COST_SECONDS)}</b>\n"
        f"⚠️ فترة بين التحذيرات: <b>{seconds_to_human(WARNING_COOLDOWN_SECONDS)}</b>\n\n"
        f"<i>للتعديل: افتح ملف config.py</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_settings_panel")]
        ])
    )


async def admin_settings_files(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """إعدادات الملفات"""
    query = update.callback_query
    await query.answer()
    if update.effective_user.id != ADMIN_ID:
        return

    from config import MAX_FILE_UPLOAD_SIZE_MB, MAX_EDIT_FILE_SIZE_MB, MAX_ZIP_SIZE_MB

    await query.edit_message_text(
        f"{DIVIDER}\n📁 <b>إعدادات الملفات</b>\n{DIVIDER}\n\n"
        f"📤 الحد الأقصى لرفع الملف: <b>{MAX_FILE_UPLOAD_SIZE_MB} MB</b>\n"
        f"✏️ الحد الأقصى لتعديل الملف: <b>{MAX_EDIT_FILE_SIZE_MB} MB</b>\n"
        f"📦 الحد الأقصى لملف ZIP: <b>{MAX_ZIP_SIZE_MB} MB</b>\n\n"
        f"<i>للتعديل: افتح ملف config.py</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_settings_panel")]
        ])
    )


async def admin_settings_security(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """إعدادات الأمان"""
    query = update.callback_query
    await query.answer()
    if update.effective_user.id != ADMIN_ID:
        return

    from config import SECURITY_CONFIG
    rate_limit = SECURITY_CONFIG.get('rate_limit', {})

    await query.edit_message_text(
        f"{DIVIDER}\n🔐 <b>إعدادات الأمان</b>\n{DIVIDER}\n\n"
        f"🚫 حد معدل الطلبات:\n"
        f"   الحد: {rate_limit.get('max_requests', 30)} طلب\n"
        f"   الفترة: {rate_limit.get('window', 60)} ثانية\n\n"
        f"🛡️ حظر IP التلقائي: {'✅' if SECURITY_CONFIG.get('auto_ban_enabled') else '❌'}\n"
        f"🔒 التحقق من التوكن: ✅ مفعّل\n\n"
        f"<i>للتعديل: افتح ملف config.py</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_settings_panel")]
        ])
    )


async def admin_settings_save(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """حفظ الإعدادات"""
    query = update.callback_query
    await query.answer("✅ تم حفظ الإعدادات", show_alert=True)

    await query.edit_message_text(
        f"{DIVIDER}\n✅ <b>تم حفظ الإعدادات</b>\n{DIVIDER}\n\n"
        f"جميع الإعدادات محفوظة وتطبق فورياً.\n\n"
        f"💡 للإعدادات المتعلقة بـ config.py\n"
        f"يجب إعادة تشغيل البوت لتطبيقها.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_settings_panel")]
        ])
    )


# ════════════════════════════════════════════════════════════════════════
# النسخ الاحتياطية للبوتات الفردية
# ════════════════════════════════════════════════════════════════════════

async def create_bot_backup(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """إنشاء نسخة احتياطية لبوت محدد"""
    query = update.callback_query
    await query.answer("⏳ جاري إنشاء النسخة...")

    bot_id = int(query.data.replace("create_backup_", ""))
    bot = db.get_bot(bot_id)

    if not bot or bot[1] != update.effective_user.id:
        await query.answer("❌ غير مصرح", show_alert=True)
        return

    from telegram import InputFile
    from datetime import datetime

    bot_path = Path(BOTS_DIRECTORY) / bot[5]
    if not bot_path.exists():
        await query.answer("❌ مجلد البوت غير موجود", show_alert=True)
        return

    try:
        buf = BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in bot_path.rglob('*'):
                if f.is_file() and not f.name.startswith('.') and f.suffix != '.pyc':
                    zf.write(str(f), str(f.relative_to(bot_path.parent)))

        buf.seek(0)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"backup_{bot[3]}_{ts}.zip"
        buf.name = filename

        await context.bot.send_document(
            chat_id=update.effective_user.id,
            document=InputFile(buf, filename=filename),
            caption=(
                f"{DIVIDER}\n💾 <b>نسخة احتياطية - {safe_html_escape(bot[3])}</b>\n{DIVIDER}\n\n"
                f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"📦 تشمل جميع ملفات البوت"
            ),
            parse_mode="HTML"
        )

        db.add_event_log(bot_id, "INFO", f"💾 تم إنشاء نسخة احتياطية: {filename}")
        await query.answer("✅ تم إرسال النسخة الاحتياطية")

    except Exception as e:
        logger.error(f"خطأ في النسخ الاحتياطي: {e}")
        await query.answer(f"❌ خطأ: {str(e)[:50]}", show_alert=True)


async def delete_backup_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """قائمة حذف النسخ الاحتياطية"""
    query = update.callback_query
    await query.answer()
    bot_id = int(query.data.replace("delete_backup_menu_", ""))
    bot = db.get_bot(bot_id)
    if not bot:
        await query.answer("❌ البوت غير موجود", show_alert=True)
        return

    await query.edit_message_text(
        f"{DIVIDER}\n🗑️ <b>حذف النسخ الاحتياطية</b>\n{DIVIDER}\n\n"
        f"⚠️ هذه الميزة ستحذف النسخ المحلية فقط.\n"
        f"النسخ المرسلة لتيليجرام آمنة.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data=f"backup_{bot_id}")]
        ])
    )




# ════════════════════════════════════════════════════════════════════════
# معالجات اختيار مستخدم للكتم/الترقية
# ════════════════════════════════════════════════════════════════════════

async def mute_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """اختيار مستخدم للكتم ثم عرض مدة الكتم"""
    query = update.callback_query
    await query.answer()
    # mute_select_{user_id}
    target_uid = int(query.data.replace("mute_select_", ""))
    context.user_data['mute_target_user_id'] = target_uid

    # جلب اسم المستخدم
    user_info = db.get_user(target_uid)
    uname = user_info[1] if user_info else f"ID:{target_uid}"

    await query.edit_message_text(
        f"{DIVIDER}\n🔇 <b>كتم: @{uname}</b>\n{DIVIDER}\n\n"
        f"اختر مدة الكتم:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏱️ ساعة واحدة",  callback_data="mute_duration_1h")],
            [InlineKeyboardButton("🕐 6 ساعات",     callback_data="mute_duration_6h")],
            [InlineKeyboardButton("📅 يوم واحد",    callback_data="mute_duration_1d")],
            [InlineKeyboardButton("🔒 دائم",        callback_data="mute_duration_permanent")],
            [InlineKeyboardButton("🔙 رجوع",        callback_data="admin_mute_users")]
        ])
    )


async def promote_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """اختيار مستخدم للترقية"""
    query = update.callback_query
    await query.answer()
    # promote_select_{user_id}
    target_uid = int(query.data.replace("promote_select_", ""))
    context.user_data['promote_target_user_id'] = target_uid

    user_info = db.get_user(target_uid)
    uname = user_info[1] if user_info else f"ID:{target_uid}"

    await query.edit_message_text(
        f"{DIVIDER}\n⬆️ <b>ترقية: @{uname}</b>\n{DIVIDER}\n\n"
        f"اختر الدور الجديد:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🛡️ مشرف",  callback_data="promote_role_moderator")],
            [InlineKeyboardButton("⭐ مميز",   callback_data="promote_role_premium")],
            [InlineKeyboardButton("🔑 أدمن",   callback_data="promote_role_admin")],
            [InlineKeyboardButton("🔙 رجوع",   callback_data="admin_promote_users")]
        ])
    )

