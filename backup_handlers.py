# ============================================================================
# معالجات النسخ الاحتياطية - NeurHostX V9.0
# ============================================================================

import io
import logging
from datetime import datetime, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ContextTypes, ConversationHandler

from config import ADMIN_ID, BOTS_DIR, DB_FILE
from backup_system import BackupSystem

logger = logging.getLogger(__name__)

# حالات المحادثة
WAIT_BACKUP_PASSWORD = "WAIT_BACKUP_PASSWORD"
WAIT_RESTORE_FILE    = "WAIT_RESTORE_FILE"
WAIT_RESTORE_PASS    = "WAIT_RESTORE_PASS"
WAIT_CHANNEL_ID      = "WAIT_CHANNEL_ID"


# ═══════════════════════════════════════════════════════════════════════════
# لوحة النسخ الاحتياطية الرئيسية
# ═══════════════════════════════════════════════════════════════════════════

async def backup_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """لوحة النسخ الاحتياطية للأدمن"""
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        await query.answer("⛔ للأدمن فقط", show_alert=True)
        return

    # إحصائيات النسخ الاحتياطية
    channel_id = db.get_setting("backup_channel_id", "")
    auto_backup = db.get_setting("auto_backup_enabled", "0")
    channel_info = channel_id if channel_id else "غير مضبوطة"

    keyboard = [
        [InlineKeyboardButton("📥 تحميل نسخة كاملة", callback_data="backup_download_now")],
        [InlineKeyboardButton("🔐 تحميل مشفّرة بكلمة مرور", callback_data="backup_download_encrypted")],
        [InlineKeyboardButton("📤 رفع واستعادة نسخة", callback_data="backup_restore_upload")],
        [InlineKeyboardButton(
            f"{'✅' if auto_backup == '1' else '❌'} النسخ التلقائي",
            callback_data="backup_toggle_auto"
        )],
        [InlineKeyboardButton("📡 ضبط قناة النسخ التلقائي", callback_data="backup_set_channel")],
        [InlineKeyboardButton("💾 نسخ احتياطي الآن للقناة", callback_data="backup_send_to_channel")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")],
    ]

    text = (
        f"════════════════════════════\n"
        f"💾 <b>لوحة النسخ الاحتياطية</b>\n"
        f"════════════════════════════\n\n"
        f"📡 قناة النسخ: <code>{channel_info}</code>\n"
        f"🔄 النسخ التلقائي: {'✅ مفعّل' if auto_backup == '1' else '❌ معطّل'}\n\n"
        f"{'─'*28}\n\n"
        f"📦 تشمل النسخة الاحتياطية:\n"
        f"   • جميع ملفات البوتات\n"
        f"   • قاعدة البيانات الكاملة\n"
        f"   • جميع الإعدادات\n"
    )

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")


# ═══════════════════════════════════════════════════════════════════════════
# تحميل نسخة احتياطية فوري
# ═══════════════════════════════════════════════════════════════════════════

async def backup_download_now(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """تحميل نسخة احتياطية فورية بدون تشفير"""
    query = update.callback_query
    await query.answer("⏳ جاري إنشاء النسخة الاحتياطية...")

    if update.effective_user.id != ADMIN_ID:
        return

    await query.edit_message_text(
        "════════════════════════════\n"
        "⏳ <b>جاري إنشاء النسخة الاحتياطية...</b>\n"
        "════════════════════════════\n\n"
        "📦 جمع ملفات البوتات...\n"
        "💾 تضمين قاعدة البيانات...",
        parse_mode="HTML"
    )

    try:
        buf = BackupSystem.create_full_backup(BOTS_DIR, DB_FILE)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"neurohost_backup_{ts}.zip"
        buf.name = filename

        await context.bot.send_document(
            chat_id=update.effective_user.id,
            document=InputFile(buf, filename=filename),
            caption=(
                f"════════════════════════════\n"
                f"💾 <b>نسخة احتياطية كاملة</b>\n"
                f"════════════════════════════\n\n"
                f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"🔒 التشفير: بدون\n"
                f"✅ جاهزة للاستعادة"
            ),
            parse_mode="HTML"
        )

        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="backup_panel")]]
        await query.edit_message_text(
            "════════════════════════════\n"
            "✅ <b>تم إرسال النسخة الاحتياطية!</b>\n"
            "════════════════════════════",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"خطأ في النسخ الاحتياطي: {e}")
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="backup_panel")]]
        await query.edit_message_text(
            f"════════════════════════════\n"
            f"❌ <b>فشل إنشاء النسخة</b>\n"
            f"════════════════════════════\n\n"
            f"السبب: {str(e)[:100]}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )


async def backup_download_encrypted(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """طلب كلمة مرور للنسخة المشفرة"""
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        return

    await query.edit_message_text(
        "════════════════════════════\n"
        "🔐 <b>تحميل نسخة مشفّرة</b>\n"
        "════════════════════════════\n\n"
        "🔑 أرسل كلمة المرور لتشفير النسخة:\n\n"
        "⚠️ احتفظ بها في مكان آمن\n"
        "أرسل /cancel للإلغاء",
        parse_mode="HTML"
    )
    return WAIT_BACKUP_PASSWORD


async def backup_receive_password(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """استقبال كلمة المرور وإرسال نسخة مشفرة"""
    password = update.message.text.strip()
    if not password or len(password) < 4:
        await update.message.reply_text("❌ كلمة المرور قصيرة جداً (4 حروف على الأقل)")
        return WAIT_BACKUP_PASSWORD

    msg = await update.message.reply_text(
        "════════════════════════════\n"
        "⏳ <b>جاري إنشاء النسخة المشفّرة...</b>\n"
        "════════════════════════════",
        parse_mode="HTML"
    )

    try:
        buf = BackupSystem.create_full_backup(BOTS_DIR, DB_FILE, password=password)
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"neurohost_encrypted_{ts}.zip"
        buf.name = filename

        await context.bot.send_document(
            chat_id=update.effective_user.id,
            document=InputFile(buf, filename=filename),
            caption=(
                f"════════════════════════════\n"
                f"🔐 <b>نسخة احتياطية مشفّرة</b>\n"
                f"════════════════════════════\n\n"
                f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"🔒 مشفّرة بكلمة مرور\n"
                f"⚠️ لا تشارك كلمة المرور"
            ),
            parse_mode="HTML"
        )
        await msg.edit_text(
            "════════════════════════════\n"
            "✅ <b>تم إرسال النسخة المشفّرة!</b>\n"
            "════════════════════════════",
            parse_mode="HTML"
        )
    except Exception as e:
        await msg.edit_text(f"❌ فشل: {str(e)[:100]}")

    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════════════════════
# استعادة نسخة احتياطية
# ═══════════════════════════════════════════════════════════════════════════

async def backup_restore_upload(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """طلب رفع ملف ZIP للاستعادة"""
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        return

    await query.edit_message_text(
        "════════════════════════════\n"
        "📤 <b>استعادة نسخة احتياطية</b>\n"
        "════════════════════════════\n\n"
        "📎 أرسل ملف النسخة الاحتياطية (.zip)\n\n"
        "⚠️ سيتم استبدال البيانات الحالية\n"
        "أرسل /cancel للإلغاء",
        parse_mode="HTML"
    )
    return WAIT_RESTORE_FILE


async def backup_receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """استقبال ملف النسخة الاحتياطية"""
    doc = update.message.document
    if not doc or not doc.file_name.endswith('.zip'):
        await update.message.reply_text("❌ يرجى إرسال ملف ZIP صحيح")
        return WAIT_RESTORE_FILE

    msg = await update.message.reply_text(
        "════════════════════════════\n"
        "⏳ <b>جاري تحميل الملف...</b>\n"
        "════════════════════════════",
        parse_mode="HTML"
    )

    try:
        tg_file = await context.bot.get_file(doc.file_id)
        buf = io.BytesIO()
        await tg_file.download_to_memory(buf)
        context.user_data['restore_zip'] = buf.getvalue()

        await msg.edit_text(
            "════════════════════════════\n"
            "🔐 <b>هل الملف مشفّر؟</b>\n"
            "════════════════════════════\n\n"
            "إذا كان مشفّراً، أرسل كلمة المرور\n"
            "إذا لم يكن مشفّراً، أرسل: <code>none</code>",
            parse_mode="HTML"
        )
        return WAIT_RESTORE_PASS
    except Exception as e:
        await msg.edit_text(f"❌ فشل تحميل الملف: {str(e)[:100]}")
        return ConversationHandler.END


async def backup_restore_execute(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """تنفيذ الاستعادة"""
    password_text = update.message.text.strip()
    password = None if password_text.lower() == "none" else password_text

    zip_data = context.user_data.get('restore_zip')
    if not zip_data:
        await update.message.reply_text("❌ لم يتم العثور على ملف النسخة")
        return ConversationHandler.END

    msg = await update.message.reply_text(
        "════════════════════════════\n"
        "⏳ <b>جاري الاستعادة...</b>\n"
        "════════════════════════════",
        parse_mode="HTML"
    )

    ok, result_msg = BackupSystem.restore_backup(zip_data, BOTS_DIR, DB_FILE, password)

    await msg.edit_text(
        f"════════════════════════════\n"
        f"{'✅' if ok else '❌'} <b>{'نجحت الاستعادة' if ok else 'فشلت الاستعادة'}</b>\n"
        f"════════════════════════════\n\n"
        f"{result_msg}",
        parse_mode="HTML"
    )

    context.user_data.pop('restore_zip', None)
    return ConversationHandler.END


# ═══════════════════════════════════════════════════════════════════════════
# النسخ الاحتياطي التلقائي
# ═══════════════════════════════════════════════════════════════════════════

async def backup_toggle_auto(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """تفعيل/إيقاف النسخ التلقائي"""
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        return

    current = db.get_setting("auto_backup_enabled", "0")
    new_val = "0" if current == "1" else "1"
    db.set_setting("auto_backup_enabled", new_val)

    status = "✅ مفعّل" if new_val == "1" else "❌ معطّل"
    await query.answer(f"النسخ التلقائي: {status}", show_alert=True)
    await backup_panel(update, context, db)


async def backup_set_channel(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """ضبط قناة النسخ التلقائي"""
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        return

    await query.edit_message_text(
        "════════════════════════════\n"
        "📡 <b>ضبط قناة النسخ التلقائي</b>\n"
        "════════════════════════════\n\n"
        "📌 أرسل معرّف القناة بالتنسيق:\n"
        "<code>@channel_name</code>\n"
        "أو\n"
        "<code>-1001234567890</code>\n\n"
        "⚠️ تأكد من أن البوت أدمن في القناة\n"
        "أرسل /cancel للإلغاء",
        parse_mode="HTML"
    )
    return WAIT_CHANNEL_ID


async def backup_receive_channel(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """استقبال معرّف القناة"""
    channel = update.message.text.strip()
    if not channel:
        await update.message.reply_text("❌ معرّف القناة فارغ")
        return WAIT_CHANNEL_ID

    db.set_setting("backup_channel_id", channel)

    await update.message.reply_text(
        f"════════════════════════════\n"
        f"✅ <b>تم ضبط القناة</b>\n"
        f"════════════════════════════\n\n"
        f"📡 القناة: <code>{channel}</code>\n"
        f"🔄 النسخ التلقائي سيُرسل يومياً",
        parse_mode="HTML"
    )
    return ConversationHandler.END


async def backup_send_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """إرسال نسخة احتياطية الآن إلى القناة"""
    query = update.callback_query
    await query.answer("⏳ جاري الإرسال...")

    if update.effective_user.id != ADMIN_ID:
        return

    channel_id = db.get_setting("backup_channel_id", "")
    if not channel_id:
        await query.answer("❌ لم يتم ضبط قناة النسخ التلقائي", show_alert=True)
        return

    await query.edit_message_text(
        "════════════════════════════\n"
        "⏳ <b>جاري إرسال النسخة للقناة...</b>\n"
        "════════════════════════════",
        parse_mode="HTML"
    )

    ok = await BackupSystem.send_auto_backup(context.bot, channel_id, BOTS_DIR, DB_FILE)

    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="backup_panel")]]
    if ok:
        await query.edit_message_text(
            f"════════════════════════════\n"
            f"✅ <b>تم الإرسال بنجاح!</b>\n"
            f"════════════════════════════\n\n"
            f"📡 القناة: <code>{channel_id}</code>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    else:
        await query.edit_message_text(
            f"════════════════════════════\n"
            f"❌ <b>فشل الإرسال</b>\n"
            f"════════════════════════════\n\n"
            f"تحقق من:\n"
            f"• البوت أدمن في القناة\n"
            f"• معرّف القناة صحيح: <code>{channel_id}</code>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
