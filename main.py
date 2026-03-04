# ============================================================================
# NeurHostX V9.2 — النسخة النهائية المتكاملة للنشر
# ============================================================================

import sys
import logging
from telegram.ext import (
    CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, PreCheckoutQueryHandler, filters,
)
from telegram import Update
from telegram.ext import ContextTypes

from app_setup import setup_logging, check_requirements, create_app, print_startup_banner
from config import ADMIN_ID, CONVERSATION_STATES, DB_FILE
from database import Database
from process_manager import ProcessManager

# ── المعالجات الأساسية ──
from handlers import (
    start, main_menu, my_bots, manage_bot, help_command, my_plan,
    start_bot_action, stop_bot_action, restart_bot_action,
    time_management, add_time_action, recover_bot,
    view_logs, download_logs, bot_stats, user_stats, settings,
    toggle_notifications, delete_account_confirm, delete_account_final,
    detailed_guide, faq, upgrade_history
)
from handlers_files import (
    file_manager, view_file, upload_file, download_file, download_all,
    edit_file_start, handle_file_edit, replace_file, delete_file, confirm_delete_file
)
from handlers_advanced import (
    add_bot_start, deploy_zip_start, handle_bot_file, handle_token,
    confirm_delete, delete_bot_action, request_upgrade, select_upgrade,
    approve_upgrade, reject_upgrade, approve_user, reject_user, sys_status,
    admin_panel, admin_users, admin_pending, admin_upgrades, admin_bots,
    bot_backup, bot_settings, clear_logs, admin_blocked,
    bulk_bot_operations, bulk_start_all_bots,
    backup_restore_menu, restore_from_backup,
    faq_interactive_menu, faq_category, faq_detail,
    admin_settings_panel, view_all_settings, manage_bot_settings,
)
from enhanced_handlers import (
    admin_moderation_panel, admin_ban_users, admin_mute_users,
    admin_promote_users, admin_moderation_stats,
    hosting_purchase_menu, buy_hosting_time,
    donate_stars_handler, donate_amount_handler, donate_custom_handler,
    smart_notifications_preview, notification_categories,
)
from payment_handlers import (
    plans_menu, select_plan_to_buy, send_payment_invoice,
    pre_checkout_callback, successful_payment_callback,
    purchase_history, refund_request,
)
from backup_handlers import (
    backup_panel, backup_download_now, backup_download_encrypted,
    backup_restore_upload, backup_receive_file, backup_restore_execute,
    backup_toggle_auto, backup_set_channel, backup_receive_channel,
    backup_send_to_channel, backup_receive_password,
    WAIT_BACKUP_PASSWORD, WAIT_RESTORE_FILE, WAIT_RESTORE_PASS, WAIT_CHANNEL_ID,
)
from missing_handlers import (
    rename_bot_start, rename_bot_execute,
    change_main_file_start, set_main_file,
    toggle_auto_recovery, set_priority_menu, set_priority_execute,
    edit_description_start, edit_description_execute,
    bulk_stop_all_bots, bulk_restart_all_bots, bulk_stats_all_bots,
    mute_duration_handler, promote_role_handler,
    mute_select_handler, promote_select_handler,
    admin_settings_system, admin_settings_resources, admin_settings_time,
    admin_settings_files, admin_settings_security, admin_settings_save,
    create_bot_backup, delete_backup_menu_handler,
)
from ux_improvements import (
    ping_command, status_command, my_bots_command,
    uptime_stats, quick_restart_all, health_check,
)

logger = setup_logging()


# ════════════════════════════════════════════════════════════════════════
# معالج الأخطاء العام
# ════════════════════════════════════════════════════════════════════════

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء المركزي"""
    err = str(context.error) if context.error else ""

    # تجاهل الأخطاء المعروفة والبسيطة
    ignored_errors = [
        "Message is not modified", "Query is too old",
        "Bad Gateway", "Timed out", "PEER_ID_INVALID",
        "Connection reset", "Network error", "webhook",
        "Message to delete not found", "message to edit not found",
        "Conflict: terminated by other getUpdates",
    ]
    for ignored in ignored_errors:
        if ignored.lower() in err.lower():
            return

    logger.error(f"❌ خطأ: {err[:300]}", exc_info=context.error)

    if not isinstance(update, Update):
        return

    try:
        if "Forbidden" in err or "bot was blocked" in err.lower():
            return  # المستخدم حظر البوت
        elif "can't parse" in err.lower():
            user_msg = "❌ خطأ في تنسيق الرسالة"
        else:
            user_msg = "❌ حدث خطأ مؤقت. حاول مرة أخرى."

        if update.callback_query:
            try:
                await update.callback_query.answer(user_msg, show_alert=True)
            except Exception:
                pass
        elif update.effective_message:
            try:
                await update.effective_message.reply_text(user_msg)
            except Exception:
                pass
    except Exception:
        pass


async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إلغاء أي عملية جارية"""
    context.user_data.clear()
    if update.message:
        await update.message.reply_text(
            "════════════════════════════\n"
            "❌ <b>تم الإلغاء</b>\n"
            "════════════════════════════\n\n"
            "أرسل /start للعودة للقائمة الرئيسية",
            parse_mode="HTML"
        )
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════════════
# أوامر الأدمن
# ════════════════════════════════════════════════════════════════════════

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """أمر /admin"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ هذا الأمر للأدمن فقط")
        return
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    await update.message.reply_text(
        "════════════════════════════\n"
        "👑 <b>لوحة تحكم الأدمن</b>\n"
        "════════════════════════════",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👑 فتح لوحة التحكم", callback_data="admin_panel")]
        ]),
        parse_mode="HTML"
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """أمر /stats - للأدمن"""
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        stats = db.get_system_stats()
        all_bots = db.get_all_bots()
        await update.message.reply_text(
            f"════════════════════════════\n"
            f"📊 <b>إحصائيات النظام</b>\n"
            f"════════════════════════════\n\n"
            f"👥 المستخدمون: <b>{stats.get('total_users', 0)}</b>\n"
            f"   ✅ معتمدون: <b>{stats.get('approved_users', 0)}</b>\n"
            f"   ⏳ معلقون: <b>{stats.get('pending_users', 0)}</b>\n"
            f"{'─'*28}\n"
            f"🤖 إجمالي البوتات: <b>{stats.get('total_bots', 0)}</b>\n"
            f"🟢 نشطة الآن: <b>{stats.get('running_bots', 0)}</b>\n"
            f"📤 ترقيات معلقة: <b>{stats.get('pending_upgrades', 0)}</b>\n",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")


async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """أمر /broadcast - إرسال لكل المستخدمين"""
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text(
            "⚙️ الاستخدام: <code>/broadcast [الرسالة]</code>",
            parse_mode="HTML"
        )
        return

    message = " ".join(context.args)
    users = db.get_all_users()
    approved = [u for u in users if len(u) > 4 and u[4] == 'approved']

    sent = 0
    failed = 0
    for user in approved:
        try:
            await context.bot.send_message(
                user[0],
                f"📢 <b>إشعار من الإدارة</b>\n\n{message}",
                parse_mode="HTML"
            )
            sent += 1
        except Exception:
            failed += 1

    await update.message.reply_text(
        f"✅ تم الإرسال: {sent} | ❌ فشل: {failed}"
    )


# ════════════════════════════════════════════════════════════════════════
# تسجيل جميع المعالجات
# ════════════════════════════════════════════════════════════════════════

def setup_handlers(app, db, pm):
    """تسجيل جميع المعالجات بشكل منظم ومتكامل"""

    app.bot_data['pm'] = pm
    app.bot_data['db'] = db

    # ── Wrapper functions ──
    def _d(fn):
        """Wrapper للدوال التي تحتاج db فقط"""
        async def w(u, c): return await fn(u, c, db)
        return w

    def _dp(fn):
        """Wrapper للدوال التي تحتاج db و pm"""
        async def w(u, c): return await fn(u, c, db, pm)
        return w

    # ════ أوامر ════
    app.add_handler(CommandHandler("start",     _d(start)))
    app.add_handler(CommandHandler("help",      lambda u, c: help_command(u, c)))
    app.add_handler(CommandHandler("admin",     _d(admin_command)))
    app.add_handler(CommandHandler("stats",     _d(stats_command)))
    app.add_handler(CommandHandler("broadcast", _d(broadcast_command)))
    app.add_handler(CommandHandler("cancel",    cancel_handler))
    app.add_handler(CommandHandler("ping",      ping_command))
    app.add_handler(CommandHandler("status",    _d(status_command)))
    app.add_handler(CommandHandler("bots",      _d(my_bots_command)))

    # ════ تنقل أساسي ════
    app.add_handler(CallbackQueryHandler(_d(main_menu),              pattern="^main_menu$"))
    app.add_handler(CallbackQueryHandler(_d(my_bots),                pattern="^my_bots$"))
    app.add_handler(CallbackQueryHandler(lambda u,c: help_command(u,c), pattern="^help$"))
    app.add_handler(CallbackQueryHandler(_d(user_stats),             pattern="^user_stats$"))
    app.add_handler(CallbackQueryHandler(_d(settings),               pattern="^settings$"))
    app.add_handler(CallbackQueryHandler(_d(toggle_notifications),   pattern="^toggle_notifications$"))
    app.add_handler(CallbackQueryHandler(_d(delete_account_confirm), pattern="^delete_account_confirm$"))
    app.add_handler(CallbackQueryHandler(_dp(delete_account_final),  pattern="^delete_account_final$"))
    app.add_handler(CallbackQueryHandler(lambda u,c: detailed_guide(u,c), pattern="^detailed_guide$"))
    app.add_handler(CallbackQueryHandler(_d(upgrade_history),        pattern="^upgrade_history$"))

    # ════ إدارة البوتات ════
    app.add_handler(CallbackQueryHandler(_d(manage_bot),             pattern=r"^manage_\d+$"))
    app.add_handler(CallbackQueryHandler(_dp(start_bot_action),      pattern=r"^start_\d+$"))
    app.add_handler(CallbackQueryHandler(_dp(stop_bot_action),       pattern=r"^stop_\d+$"))
    app.add_handler(CallbackQueryHandler(_dp(restart_bot_action),    pattern=r"^restart_\d+$"))
    app.add_handler(CallbackQueryHandler(_dp(recover_bot),           pattern=r"^recover_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(time_management),        pattern=r"^time_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(add_time_action),        pattern=r"^addtime_\d+_.+$"))
    app.add_handler(CallbackQueryHandler(_d(view_logs),              pattern=r"^logs_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(download_logs),          pattern=r"^download_logs_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(bot_stats),              pattern=r"^stats_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(clear_logs),             pattern=r"^clear_logs_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(bot_settings),           pattern=r"^bot_settings_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(bot_backup),             pattern=r"^backup_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(confirm_delete),         pattern=r"^confirm_del_\d+$"))
    app.add_handler(CallbackQueryHandler(_dp(delete_bot_action),     pattern=r"^delete_\d+$"))

    # ════ مدير الملفات ════
    app.add_handler(CallbackQueryHandler(_d(file_manager),           pattern=r"^files_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(file_manager),           pattern=r"^browse_\d+_.+$"))
    app.add_handler(CallbackQueryHandler(_d(view_file),              pattern=r"^viewfile_\d+_.+$"))
    app.add_handler(CallbackQueryHandler(_d(download_file),          pattern=r"^downloadfile_\d+_.+$"))
    app.add_handler(CallbackQueryHandler(_d(download_all),           pattern=r"^download_all_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(delete_file),            pattern=r"^deletefile_\d+_.+$"))
    app.add_handler(CallbackQueryHandler(_d(confirm_delete_file),    pattern=r"^confirmdelfile_\d+_.+$"))

    # ════ إعدادات البوت الفردي ════
    app.add_handler(CallbackQueryHandler(_d(bot_settings),           pattern=r"^bot_settings_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(manage_bot_settings),    pattern=r"^bot_settings_advanced_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(rename_bot_start),       pattern=r"^rename_bot_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(change_main_file_start), pattern=r"^change_main_file_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(set_main_file),          pattern=r"^set_main_file_\d+_.+$"))
    app.add_handler(CallbackQueryHandler(_d(toggle_auto_recovery),   pattern=r"^toggle_auto_recovery_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(set_priority_menu),      pattern=r"^set_priority_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(set_priority_execute),   pattern=r"^set_prio_[123]_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(edit_description_start), pattern=r"^edit_description_\d+$"))

    # ════ الخطط والترقيات ════
    app.add_handler(CallbackQueryHandler(_d(my_plan),                pattern="^my_plan$"))
    app.add_handler(CallbackQueryHandler(_d(request_upgrade),        pattern="^request_upgrade$"))
    app.add_handler(CallbackQueryHandler(_d(select_upgrade),         pattern=r"^select_upgrade_.+$"))
    app.add_handler(CallbackQueryHandler(_d(approve_upgrade),        pattern=r"^approve_upgrade_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(reject_upgrade),         pattern=r"^reject_upgrade_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(approve_user),           pattern=r"^approve_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(reject_user),            pattern=r"^reject_\d+$"))

    # ════ لوحة الأدمن ════
    app.add_handler(CallbackQueryHandler(_d(sys_status),             pattern="^sys_status$"))
    app.add_handler(CallbackQueryHandler(_d(admin_panel),            pattern="^admin_panel$"))
    app.add_handler(CallbackQueryHandler(_d(admin_users),            pattern="^admin_users$"))
    app.add_handler(CallbackQueryHandler(_d(admin_pending),          pattern="^admin_pending$"))
    app.add_handler(CallbackQueryHandler(_d(admin_upgrades),         pattern="^admin_upgrades$"))
    app.add_handler(CallbackQueryHandler(_d(admin_bots),             pattern="^admin_bots$"))
    app.add_handler(CallbackQueryHandler(_d(admin_blocked),          pattern="^admin_blocked$"))

    # ════ الإشراف ════
    app.add_handler(CallbackQueryHandler(_d(admin_moderation_panel),   pattern="^admin_moderation_panel$"))
    app.add_handler(CallbackQueryHandler(_d(admin_ban_users),          pattern="^admin_ban_users$"))
    app.add_handler(CallbackQueryHandler(_d(admin_mute_users),         pattern="^admin_mute_users$"))
    app.add_handler(CallbackQueryHandler(_d(admin_promote_users),      pattern="^admin_promote_users$"))
    app.add_handler(CallbackQueryHandler(_d(admin_moderation_stats),   pattern="^admin_moderation_stats$"))
    app.add_handler(CallbackQueryHandler(_d(mute_duration_handler),    pattern=r"^mute_duration_(1h|6h|1d|permanent)$"))
    app.add_handler(CallbackQueryHandler(_d(promote_role_handler),     pattern=r"^promote_role_(moderator|premium|admin)$"))
    app.add_handler(CallbackQueryHandler(_d(mute_select_handler),      pattern=r"^mute_select_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(promote_select_handler),   pattern=r"^promote_select_\d+$"))

    # ════ إعدادات النظام ════
    app.add_handler(CallbackQueryHandler(_d(admin_settings_panel),     pattern="^admin_settings_panel$"))
    app.add_handler(CallbackQueryHandler(_d(view_all_settings),        pattern="^admin_settings_view_all$"))
    app.add_handler(CallbackQueryHandler(_d(admin_settings_system),    pattern="^admin_settings_system$"))
    app.add_handler(CallbackQueryHandler(_d(admin_settings_resources), pattern="^admin_settings_resources$"))
    app.add_handler(CallbackQueryHandler(_d(admin_settings_time),      pattern="^admin_settings_time$"))
    app.add_handler(CallbackQueryHandler(_d(admin_settings_files),     pattern="^admin_settings_files$"))
    app.add_handler(CallbackQueryHandler(_d(admin_settings_security),  pattern="^admin_settings_security$"))
    app.add_handler(CallbackQueryHandler(_d(admin_settings_save),      pattern="^admin_settings_save$"))

    # ════ العمليات الجماعية ════
    app.add_handler(CallbackQueryHandler(_d(bulk_bot_operations),      pattern="^bulk_bot_operations$"))
    app.add_handler(CallbackQueryHandler(_d(bulk_start_all_bots),      pattern="^bulk_start_all$"))
    app.add_handler(CallbackQueryHandler(_d(bulk_stop_all_bots),       pattern="^bulk_stop_all$"))
    app.add_handler(CallbackQueryHandler(_d(bulk_restart_all_bots),    pattern="^bulk_restart_all$"))
    app.add_handler(CallbackQueryHandler(_d(bulk_stats_all_bots),      pattern="^bulk_stats_all$"))
    app.add_handler(CallbackQueryHandler(_d(backup_restore_menu),      pattern=r"^backups_menu_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(restore_from_backup),      pattern=r"^restore_backup_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(restore_from_backup),      pattern=r"^restore_backup_menu_\d+$"))

    # ════ الإشعارات والمساعدة ════
    app.add_handler(CallbackQueryHandler(_d(smart_notifications_preview), pattern="^smart_notifications_preview$"))
    app.add_handler(CallbackQueryHandler(_d(notification_categories),     pattern="^notification_categories$"))
    app.add_handler(CallbackQueryHandler(_d(notification_categories),     pattern=r"^notif_cat_\w+$"))
    app.add_handler(CallbackQueryHandler(lambda u,c: faq_interactive_menu(u,c), pattern="^faq_interactive_menu$"))
    app.add_handler(CallbackQueryHandler(lambda u,c: faq_interactive_menu(u,c), pattern="^faq$"))
    app.add_handler(CallbackQueryHandler(lambda u,c: faq_category(u,c),   pattern=r"^faq_cat_.+$"))
    app.add_handler(CallbackQueryHandler(lambda u,c: faq_detail(u,c),     pattern=r"^faq_detail_\d+$"))

    # ════ الدفع والاستضافة ════
    app.add_handler(CallbackQueryHandler(_d(plans_menu),               pattern="^plans_menu$"))
    app.add_handler(CallbackQueryHandler(_d(select_plan_to_buy),       pattern=r"^buy_plan_(pro|ultra|supreme)$"))
    app.add_handler(CallbackQueryHandler(_d(send_payment_invoice),     pattern=r"^pay_invoice_(pro|ultra|supreme)$"))
    app.add_handler(CallbackQueryHandler(_d(purchase_history),         pattern="^purchase_history$"))
    app.add_handler(CallbackQueryHandler(_d(refund_request),           pattern="^refund_request$"))
    app.add_handler(CallbackQueryHandler(_d(hosting_purchase_menu),    pattern=r"^hosting_purchase_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(buy_hosting_time),         pattern=r"^buy_hosting_(week|month|3months|year)_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(donate_stars_handler),     pattern="^donate_stars$"))
    app.add_handler(CallbackQueryHandler(_d(donate_amount_handler),    pattern=r"^donate_amount_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(donate_custom_handler),    pattern="^donate_custom$"))
    app.add_handler(PreCheckoutQueryHandler(_d(pre_checkout_callback)))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, _d(successful_payment_callback)))

    # ════ النسخ الاحتياطية ════
    app.add_handler(CallbackQueryHandler(_d(backup_panel),             pattern="^backup_panel$"))
    app.add_handler(CallbackQueryHandler(_d(backup_download_now),      pattern="^backup_download_now$"))
    app.add_handler(CallbackQueryHandler(_d(backup_toggle_auto),       pattern="^backup_toggle_auto$"))
    app.add_handler(CallbackQueryHandler(_d(backup_set_channel),       pattern="^backup_set_channel$"))
    app.add_handler(CallbackQueryHandler(_d(backup_send_to_channel),   pattern="^backup_send_to_channel$"))
    app.add_handler(CallbackQueryHandler(_d(create_bot_backup),        pattern=r"^create_backup_\d+$"))
    app.add_handler(CallbackQueryHandler(_d(delete_backup_menu_handler), pattern=r"^delete_backup_menu_\d+$"))

    # ════ تحسينات تجربة المستخدم ════
    app.add_handler(CallbackQueryHandler(_d(uptime_stats),             pattern="^uptime_stats$"))
    app.add_handler(CallbackQueryHandler(_d(quick_restart_all),        pattern="^quick_restart_all$"))
    app.add_handler(CallbackQueryHandler(_d(health_check),             pattern="^health_check$"))

    # ════ ConversationHandlers ════

    # ─ رفع بوت جديد ─
    add_bot_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(_d(add_bot_start), pattern="^add_bot$")],
        states={
            CONVERSATION_STATES['WAIT_FILE']: [
                MessageHandler(filters.Document.ALL, _dp(handle_bot_file)),
                CommandHandler("cancel", cancel_handler)
            ],
            CONVERSATION_STATES['WAIT_TOKEN']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, _d(handle_token)),
                CommandHandler("cancel", cancel_handler)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler), CommandHandler("start", _d(start))],
        per_user=True, per_chat=True, allow_reentry=True,
    )

    # ─ نشر ZIP ─
    deploy_zip_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(_d(deploy_zip_start), pattern="^deploy_zip$")],
        states={
            CONVERSATION_STATES['WAIT_FILE']: [
                MessageHandler(filters.Document.ALL, _dp(handle_bot_file)),
                CommandHandler("cancel", cancel_handler)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler), CommandHandler("start", _d(start))],
        per_user=True, per_chat=True, allow_reentry=True,
    )

    # ─ رفع ملف لبوت موجود ─
    upload_file_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(_d(upload_file), pattern=r"^upload_file_\d+$")],
        states={
            CONVERSATION_STATES['WAIT_FILE']: [
                MessageHandler(filters.Document.ALL, _dp(handle_bot_file)),
                CommandHandler("cancel", cancel_handler)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler), CommandHandler("start", _d(start))],
        per_user=True, per_chat=True, allow_reentry=True,
    )

    # ─ استبدال ملف ─
    replace_file_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(_d(replace_file), pattern=r"^replace_file_\d+$")],
        states={
            CONVERSATION_STATES['WAIT_FILE']: [
                MessageHandler(filters.Document.ALL, _dp(handle_bot_file)),
                CommandHandler("cancel", cancel_handler)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler), CommandHandler("start", _d(start))],
        per_user=True, per_chat=True, allow_reentry=True,
    )

    # ─ تعديل ملف ─
    edit_file_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(_d(edit_file_start), pattern=r"^editfile_\d+_.+$")],
        states={
            CONVERSATION_STATES['WAIT_FILE_EDIT']: [
                MessageHandler(
                    filters.Document.ALL | (filters.TEXT & ~filters.COMMAND),
                    _d(handle_file_edit)
                ),
                CommandHandler("cancel", cancel_handler)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler), CommandHandler("start", _d(start))],
        per_user=True, per_chat=True, allow_reentry=True,
    )

    # ─ تغيير اسم البوت ─
    rename_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(_d(rename_bot_start), pattern=r"^rename_bot_\d+$")],
        states={
            CONVERSATION_STATES['WAIT_RENAME']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, _d(rename_bot_execute)),
                CommandHandler("cancel", cancel_handler)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)],
        per_user=True, per_chat=True, allow_reentry=True,
    )

    # ─ تعديل وصف البوت ─
    desc_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(_d(edit_description_start), pattern=r"^edit_description_\d+$")],
        states={
            CONVERSATION_STATES['WAIT_DESCRIPTION']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, _d(edit_description_execute)),
                CommandHandler("cancel", cancel_handler)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)],
        per_user=True, per_chat=True, allow_reentry=True,
    )

    # ─ نسخة احتياطية مشفّرة ─
    backup_enc_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(_d(backup_download_encrypted), pattern="^backup_download_encrypted$")],
        states={
            WAIT_BACKUP_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, _d(backup_receive_password)),
                CommandHandler("cancel", cancel_handler)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)],
        per_user=True, per_chat=True, allow_reentry=True,
    )

    # ─ استعادة نسخة احتياطية ─
    backup_restore_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(_d(backup_restore_upload), pattern="^backup_restore_upload$")],
        states={
            WAIT_RESTORE_FILE: [
                MessageHandler(filters.Document.ALL, _d(backup_receive_file)),
                CommandHandler("cancel", cancel_handler)
            ],
            WAIT_RESTORE_PASS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, _d(backup_restore_execute)),
                CommandHandler("cancel", cancel_handler)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)],
        per_user=True, per_chat=True, allow_reentry=True,
    )

    # ─ ضبط قناة النسخ الاحتياطي ─
    backup_channel_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(_d(backup_set_channel), pattern="^backup_set_channel$")],
        states={
            WAIT_CHANNEL_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, _d(backup_receive_channel)),
                CommandHandler("cancel", cancel_handler)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)],
        per_user=True, per_chat=True, allow_reentry=True,
    )

    # إضافة جميع ConversationHandlers
    for conv in [
        add_bot_conv, deploy_zip_conv, upload_file_conv, replace_file_conv,
        edit_file_conv, rename_conv, desc_conv,
        backup_enc_conv, backup_restore_conv, backup_channel_conv,
    ]:
        app.add_handler(conv)

    app.add_error_handler(error_handler)

    total = sum(len(v) for v in app.handlers.values())
    logger.info(f"✅ تم تسجيل {total} معالج بنجاح")
    return total


# ════════════════════════════════════════════════════════════════════════
# نقطة الدخول الرئيسية
# ════════════════════════════════════════════════════════════════════════

def main():
    """نقطة الدخول الرئيسية"""
    try:
        check_requirements()
        print_startup_banner()

        # تهيئة قاعدة البيانات
        db = Database(DB_FILE)
        logger.info("✅ قاعدة البيانات تعمل")

        # تهيئة مدير العمليات
        pm = ProcessManager(db)
        logger.info("✅ مدير العمليات جاهز")

        # إنشاء التطبيق
        app = create_app()
        logger.info("✅ تطبيق البوت جاهز")

        # تسجيل المعالجات
        total = setup_handlers(app, db, pm)

        print("\n" + "=" * 58)
        print(f"🚀 NeurHostX V9.2 يعمل | {total} معالج مسجّل")
        print("   اضغط Ctrl+C للإيقاف")
        print("=" * 58 + "\n")

        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
        )

    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف البوت بنجاح")
        sys.exit(0)
    except ValueError as e:
        logger.critical(f"❌ خطأ في الإعداد: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"❌ خطأ حرج: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
