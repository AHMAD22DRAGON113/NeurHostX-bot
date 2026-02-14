# ============================================================================
# البرنامج الرئيسي - NeuroHost V8 Enhanced
# ============================================================================

import sys
import logging
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)
from telegram import Update
from telegram.ext import ContextTypes

# استيراد الملفات المنفصلة
from app_setup import setup_logging, check_requirements, create_app, print_startup_banner
from config import ADMIN_ID, CONVERSATION_STATES, TOKEN, DB_FILE
from database import Database
from process_manager import ProcessManager

# معالجات أساسية
from handlers import (
    start, main_menu, my_bots, manage_bot, help_command, my_plan,
    start_bot_action, stop_bot_action, restart_bot_action, time_management,
    add_time_action, recover_bot, view_logs, bot_stats, user_stats, settings,
    toggle_notifications, delete_account_confirm, delete_account_final,
    detailed_guide, faq, upgrade_history
)

# معالجات الملفات
from handlers_files import (
    file_manager, view_file, upload_file, download_file, download_all,
    edit_file_start, handle_file_edit, replace_file, delete_file, confirm_delete_file
)

# معالجات متقدمة (موحدة)
from handlers_advanced import (
    add_bot_start, deploy_zip_start, handle_bot_file, handle_token,
    confirm_delete, delete_bot_action, request_upgrade, select_upgrade,
    approve_upgrade, reject_upgrade, approve_user, reject_user, sys_status,
    admin_panel, admin_users, admin_pending, admin_upgrades, admin_bots,
    bot_backup, bot_settings, clear_logs, admin_blocked,
    admin_settings_panel, view_all_settings, admin_moderation_panel,
    admin_ban_users, admin_moderation_stats, hosting_purchase_menu,
    donate_stars_handler
)

logger = setup_logging()

# ============================================================================
# معالج الأخطاء العام
# ============================================================================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء المحسن"""
    logger.error("خطأ:", exc_info=context.error)
    
    try:
        if isinstance(update, Update):
            error_message = "❌ حدث خطأ غير متوقع. حاول مرة أخرى."
            
            # تحديد نوع الخطأ
            error_str = str(context.error)
            if "Message is not modified" in error_str:
                return  # تجاهل خطأ الرسالة غير المعدلة
            elif "Query is too old" in error_str:
                return  # تجاهل خطأ الاستعلام القديم
            elif "Forbidden" in error_str:
                error_message = "⚠️ البوت محظور أو لا يملك الصلاحيات الكافية"
            elif "Network" in error_str or "Connection" in error_str:
                error_message = "⚠️ خطأ في الاتصال. حاول مرة أخرى."
            
            if update.effective_message:
                await update.effective_message.reply_text(error_message)
            elif update.callback_query:
                await update.callback_query.answer(error_message, show_alert=True)
                
    except Exception as e:
        logger.error(f"خطأ في معالج الأخطاء: {e}")

# ============================================================================
# معالج الإلغاء
# ============================================================================

async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج إلغاء المحادثة"""
    # تنظيف بيانات المستخدم
    context.user_data.clear()
    
    await update.message.reply_text(
        "❌ <b>تم الإلغاء</b>\n\n"
        "أرسل /start للعودة للقائمة الرئيسية",
        parse_mode="HTML"
    )
    return ConversationHandler.END

# ============================================================================
# إعداد المعالجات
# ============================================================================

def setup_handlers(app, db, pm):
    """إعداد جميع المعالجات"""
    
    # إنشاء دوال wrapper لتمرير db و pm
    # ═══════════════════════════════════════════════════════════════════════
    
    # معالجات أساسية
    async def start_h(u, c): return await start(u, c, db)
    async def main_menu_h(u, c): return await main_menu(u, c, db)
    async def my_bots_h(u, c): return await my_bots(u, c, db)
    async def manage_bot_h(u, c): return await manage_bot(u, c, db)
    async def start_bot_h(u, c): return await start_bot_action(u, c, db, pm)
    async def stop_bot_h(u, c): return await stop_bot_action(u, c, db, pm)
    async def restart_bot_h(u, c): return await restart_bot_action(u, c, db, pm)
    async def time_mgmt_h(u, c): return await time_management(u, c, db)
    async def add_time_h(u, c): return await add_time_action(u, c, db)
    async def recover_h(u, c): return await recover_bot(u, c, db, pm)
    async def view_logs_h(u, c): return await view_logs(u, c, db)
    async def bot_stats_h(u, c): return await bot_stats(u, c, db)
    async def my_plan_h(u, c): return await my_plan(u, c, db)
    async def user_stats_h(u, c): return await user_stats(u, c, db)
    async def settings_h(u, c): return await settings(u, c, db)
    async def help_h(u, c): return await help_command(u, c)
    async def toggle_notif_h(u, c): return await toggle_notifications(u, c, db)
    async def del_acc_confirm_h(u, c): return await delete_account_confirm(u, c, db)
    async def del_acc_final_h(u, c): return await delete_account_final(u, c, db, pm)
    async def detailed_guide_h(u, c): return await detailed_guide(u, c)
    async def faq_h(u, c): return await faq(u, c)
    async def upgrade_history_h(u, c): return await upgrade_history(u, c, db)
    
    # معالجات الملفات
    async def file_mgr_h(u, c): return await file_manager(u, c, db)
    async def view_file_h(u, c): return await view_file(u, c, db)
    async def download_h(u, c): return await download_file(u, c, db)
    async def download_all_h(u, c): return await download_all(u, c, db)
    async def edit_file_h(u, c): return await edit_file_start(u, c, db)
    async def handle_edit_h(u, c): return await handle_file_edit(u, c, db)
    async def delete_file_h(u, c): return await delete_file(u, c, db)
    async def confirm_del_file_h(u, c): return await confirm_delete_file(u, c, db)
    async def upload_file_h(u, c): return await upload_file(u, c, db)
    async def replace_file_h(u, c): return await replace_file(u, c, db)
    
    # معالجات البوتات
    async def add_bot_h(u, c): return await add_bot_start(u, c, db)
    async def deploy_zip_h(u, c): return await deploy_zip_start(u, c, db)
    async def handle_file_h(u, c): return await handle_bot_file(u, c, db, pm)
    async def handle_token_h(u, c): return await handle_token(u, c, db)
    async def confirm_del_h(u, c): return await confirm_delete(u, c, db)
    async def delete_bot_h(u, c): return await delete_bot_action(u, c, db, pm)
    async def backup_h(u, c): return await bot_backup(u, c, db)
    async def bot_settings_h(u, c): return await bot_settings(u, c, db)
    async def clear_logs_h(u, c): return await clear_logs(u, c, db)
    
    # معالجات الترقيات
    async def req_upgrade_h(u, c): return await request_upgrade(u, c, db)
    async def sel_upgrade_h(u, c): return await select_upgrade(u, c, db)
    async def approve_up_h(u, c): return await approve_upgrade(u, c, db)
    async def reject_up_h(u, c): return await reject_upgrade(u, c, db)
    
    # معالجات الأدمن
    async def approve_u_h(u, c): return await approve_user(u, c, db)
    async def reject_u_h(u, c): return await reject_user(u, c, db)
    async def sys_status_h(u, c): return await sys_status(u, c, db)
    async def admin_panel_h(u, c): return await admin_panel(u, c, db)
    async def admin_users_h(u, c): return await admin_users(u, c, db)
    async def admin_pending_h(u, c): return await admin_pending(u, c, db)
    async def admin_upgrades_h(u, c): return await admin_upgrades(u, c, db)
    async def admin_bots_h(u, c): return await admin_bots(u, c, db)
    async def admin_blocked_h(u, c): return await admin_blocked(u, c, db)
    
    # ═══════════════════════════════════════════════════════════════════════
    # تسجيل المعالجات
    # ═══════════════════════════════════════════════════════════════════════
    
    # أوامر أساسية
    app.add_handler(CommandHandler("start", start_h))
    app.add_handler(CommandHandler("help", help_h))
    
    # القائمة الرئيسية والتنقل
    app.add_handler(CallbackQueryHandler(main_menu_h, pattern="^main_menu$"))
    app.add_handler(CallbackQueryHandler(my_bots_h, pattern="^my_bots$"))
    app.add_handler(CallbackQueryHandler(help_h, pattern="^help$"))
    app.add_handler(CallbackQueryHandler(user_stats_h, pattern="^user_stats$"))
    app.add_handler(CallbackQueryHandler(settings_h, pattern="^settings$"))
    app.add_handler(CallbackQueryHandler(toggle_notif_h, pattern="^toggle_notifications$"))
    app.add_handler(CallbackQueryHandler(del_acc_confirm_h, pattern="^delete_account_confirm$"))
    app.add_handler(CallbackQueryHandler(del_acc_final_h, pattern="^delete_account_final$"))
    app.add_handler(CallbackQueryHandler(detailed_guide_h, pattern="^detailed_guide$"))
    app.add_handler(CallbackQueryHandler(faq_h, pattern="^faq$"))
    
    # إدارة البوتات
    app.add_handler(CallbackQueryHandler(manage_bot_h, pattern=r"^manage_\d+$"))
    app.add_handler(CallbackQueryHandler(start_bot_h, pattern=r"^start_\d+$"))
    app.add_handler(CallbackQueryHandler(stop_bot_h, pattern=r"^stop_\d+$"))
    app.add_handler(CallbackQueryHandler(restart_bot_h, pattern=r"^restart_\d+$"))
    app.add_handler(CallbackQueryHandler(recover_h, pattern=r"^recover_\d+$"))
    
    # إدارة الوقت
    app.add_handler(CallbackQueryHandler(time_mgmt_h, pattern=r"^time_\d+$"))
    app.add_handler(CallbackQueryHandler(add_time_h, pattern=r"^addtime_\d+_.+$"))
    
    # الإحصائيات والسجلات
    app.add_handler(CallbackQueryHandler(view_logs_h, pattern=r"^logs_\d+$"))
    app.add_handler(CallbackQueryHandler(bot_stats_h, pattern=r"^stats_\d+$"))
    app.add_handler(CallbackQueryHandler(clear_logs_h, pattern=r"^clear_logs_\d+$"))
    
    # إعدادات البوت والنسخ الاحتياطي
    app.add_handler(CallbackQueryHandler(bot_settings_h, pattern=r"^bot_settings_\d+$"))
    app.add_handler(CallbackQueryHandler(backup_h, pattern=r"^backup_\d+$"))
    
    # حذف البوتات
    app.add_handler(CallbackQueryHandler(confirm_del_h, pattern=r"^confirm_del_\d+$"))
    app.add_handler(CallbackQueryHandler(delete_bot_h, pattern=r"^delete_\d+$"))
    
    # معالجات الملفات
    app.add_handler(CallbackQueryHandler(file_mgr_h, pattern=r"^files_\d+$"))
    app.add_handler(CallbackQueryHandler(view_file_h, pattern=r"^viewfile_\d+_.+$"))
    app.add_handler(CallbackQueryHandler(download_h, pattern=r"^downloadfile_\d+_.+$"))
    app.add_handler(CallbackQueryHandler(download_all_h, pattern=r"^download_all_\d+$"))
    app.add_handler(CallbackQueryHandler(delete_file_h, pattern=r"^deletefile_\d+_.+$"))
    app.add_handler(CallbackQueryHandler(confirm_del_file_h, pattern=r"^confirmdelfile_\d+_.+$"))
    
    # معالجات الخطط
    app.add_handler(CallbackQueryHandler(my_plan_h, pattern="^my_plan$"))
    app.add_handler(CallbackQueryHandler(req_upgrade_h, pattern="^request_upgrade$"))
    app.add_handler(CallbackQueryHandler(sel_upgrade_h, pattern=r"^select_upgrade_.+$"))
    app.add_handler(CallbackQueryHandler(approve_up_h, pattern=r"^approve_upgrade_\d+$"))
    app.add_handler(CallbackQueryHandler(reject_up_h, pattern=r"^reject_upgrade_\d+$"))
    app.add_handler(CallbackQueryHandler(upgrade_history_h, pattern="^upgrade_history$"))
    
    # معالجات الأدمن
    app.add_handler(CallbackQueryHandler(sys_status_h, pattern="^sys_status$"))
    app.add_handler(CallbackQueryHandler(admin_panel_h, pattern="^admin_panel$"))
    app.add_handler(CallbackQueryHandler(admin_users_h, pattern="^admin_users$"))
    app.add_handler(CallbackQueryHandler(admin_pending_h, pattern="^admin_pending$"))
    app.add_handler(CallbackQueryHandler(admin_upgrades_h, pattern="^admin_upgrades$"))
    app.add_handler(CallbackQueryHandler(admin_bots_h, pattern="^admin_bots$"))
    app.add_handler(CallbackQueryHandler(admin_blocked_h, pattern="^admin_blocked$"))
    app.add_handler(CallbackQueryHandler(approve_u_h, pattern=r"^approve_\d+$"))
    app.add_handler(CallbackQueryHandler(reject_u_h, pattern=r"^reject_\d+$"))
    
    # ═══════════════════════════════════════════════════════════════════════
    # محادثات (ConversationHandlers)
    # ═══════════════════════════════════════════════════════════════════════
    
    # محادثة إضافة بوت
    add_bot_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_bot_h, pattern="^add_bot$")],
        states={
            CONVERSATION_STATES['WAIT_FILE']: [
                MessageHandler(filters.Document.ALL, handle_file_h),
                CommandHandler("cancel", cancel_handler)
            ],
            CONVERSATION_STATES['WAIT_TOKEN']: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_token_h),
                CommandHandler("cancel", cancel_handler)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_handler),
            CommandHandler("start", start_h)
        ],
        per_user=True,
        per_chat=True
    )
    
    # محادثة نشر ZIP
    deploy_zip_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(deploy_zip_h, pattern="^deploy_zip$")],
        states={
            CONVERSATION_STATES['WAIT_FILE']: [
                MessageHandler(filters.Document.ALL, handle_file_h),
                CommandHandler("cancel", cancel_handler)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_handler),
            CommandHandler("start", start_h)
        ],
        per_user=True,
        per_chat=True
    )
    
    # محادثة رفع ملف
    upload_file_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(upload_file_h, pattern=r"^upload_file_\d+$")],
        states={
            CONVERSATION_STATES['WAIT_FILE']: [
                MessageHandler(filters.Document.ALL, handle_file_h),
                CommandHandler("cancel", cancel_handler)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_handler),
            CommandHandler("start", start_h)
        ],
        per_user=True,
        per_chat=True
    )
    
    # محادثة استبدال ملف
    replace_file_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(replace_file_h, pattern=r"^replace_file_\d+$")],
        states={
            CONVERSATION_STATES['WAIT_FILE']: [
                MessageHandler(filters.Document.ALL, handle_file_h),
                CommandHandler("cancel", cancel_handler)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_handler),
            CommandHandler("start", start_h)
        ],
        per_user=True,
        per_chat=True
    )
    
    # محادثة تعديل ملف
    edit_file_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_file_h, pattern=r"^editfile_\d+_.+$")],
        states={
            CONVERSATION_STATES['WAIT_FILE_EDIT']: [
                MessageHandler(
                    filters.Document.ALL | (filters.TEXT & ~filters.COMMAND),
                    handle_edit_h
                ),
                CommandHandler("cancel", cancel_handler)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_handler),
            CommandHandler("start", start_h)
        ],
        per_user=True,
        per_chat=True
    )
    
    # تسجيل المحادثات
    app.add_handler(add_bot_conv)
    app.add_handler(deploy_zip_conv)
    app.add_handler(upload_file_conv)
    app.add_handler(replace_file_conv)
    app.add_handler(edit_file_conv)
    
    # معالج الأخطاء
    app.add_error_handler(error_handler)
    
    logger.info(f"✅ تم تسجيل {len(app.handlers[0])} معالج")

# ============================================================================
# البرنامج الرئيسي
# ============================================================================

def main():
    """البرنامج الرئيسي"""
    try:
        # التحقق من المتطلبات
        check_requirements()
        
        # طباعة بيان البداية
        print_startup_banner()
        
        # إعداد قاعدة البيانات
        db = Database(DB_FILE)
        logger.info("✅ تم تهيئة قاعدة البيانات")
        
        # إنشاء مدير العمليات
        pm = ProcessManager(db)
        logger.info("✅ تم إنشاء مدير العمليات")
        
        # إنشاء التطبيق
        app = create_app()
        logger.info("✅ تم إنشاء تطبيق البوت")
        
        # إعداد المعالجات
        setup_handlers(app, db, pm)
        logger.info("✅ تم إعداد المعالجات")
        
        # بدء التطبيق
        logger.info("🚀 بدء البوت...")
        print("\n" + "="*50)
        print("🟢 البوت يعمل الآن - اضغط Ctrl+C للإيقاف")
        print("="*50 + "\n")
        
        app.run_polling(drop_pending_updates=True)
        
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف البوت من قبل المستخدم")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"❌ خطأ حرج: {e}")
        print(f"\n❌ خطأ حرج: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
