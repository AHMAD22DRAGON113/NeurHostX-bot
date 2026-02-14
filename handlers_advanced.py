# ============================================================================
# معالجات متقدمة - NeuroHost V8 Enhanced (البوتات والأدمن والترقيات)
# ============================================================================

import re
import sys
import time
import shutil
import logging
import asyncio
import zipfile
import io
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ContextTypes, ConversationHandler
from config import (
    BOTS_DIR, MAX_FILE_SIZE_MB, PLANS, ADMIN_ID, 
    DEVELOPER_USERNAME, DB_FILE, CONVERSATION_STATES
)
from helpers import (
    safe_html_escape, get_file_size, seconds_to_human, 
    get_current_time, render_bar, extract_token_from_code,
    validate_token, get_bot_id_from_callback, generate_unique_folder
)

logger = logging.getLogger(__name__)

# ============================================================================
# إضافة البوتات
# ============================================================================

async def add_bot_start(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """بدء إضافة البوت"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # التحقق من حد البوتات
    plan = db.get_user_plan(user_id, ADMIN_ID)
    plan_config = PLANS.get(plan, PLANS['free'])
    current_bots = db.count_user_bots(user_id)
    
    if current_bots >= plan_config['max_bots']:
        await query.edit_message_text(
            f"⚠️ <b>وصلت للحد الأقصى للبوتات</b>\n"
            f"{'─' * 35}\n\n"
            f"📦 خطتك: {plan_config['emoji']} {plan_config['name']}\n"
            f"🤖 البوتات: {current_bots}/{plan_config['max_bots']}\n\n"
            f"💡 قم بترقية خطتك لإضافة المزيد من البوتات",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 طلب ترقية", callback_data="request_upgrade")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]
            ]),
            parse_mode="HTML"
        )
        return ConversationHandler.END
    
    await query.message.reply_text(
        "📤 <b>إضافة بوت جديد</b>\n"
        f"{'─' * 35}\n\n"
        "📎 أرسل ملف البوت بصيغة <code>.py</code>\n\n"
        "💡 <b>ملاحظات:</b>\n"
        "• سيتم اكتشاف التوكن تلقائياً إن وجد\n"
        "• يمكنك إرسال ملف ZIP للمشاريع الكبيرة\n"
        f"• الحد الأقصى للحجم: {MAX_FILE_SIZE_MB}MB\n\n"
        "❌ للإلغاء أرسل /cancel",
        parse_mode="HTML"
    )
    
    context.user_data['bot_action'] = 'add_bot'
    return CONVERSATION_STATES['WAIT_FILE']

async def deploy_zip_start(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """بدء نشر ZIP"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # التحقق من حد البوتات
    plan = db.get_user_plan(user_id, ADMIN_ID)
    plan_config = PLANS.get(plan, PLANS['free'])
    current_bots = db.count_user_bots(user_id)
    
    if current_bots >= plan_config['max_bots']:
        await query.edit_message_text(
            f"⚠️ <b>وصلت للحد الأقصى للبوتات</b>\n\n"
            f"💡 قم بترقية خطتك لإضافة المزيد",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📤 طلب ترقية", callback_data="request_upgrade")],
                [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]
            ]),
            parse_mode="HTML"
        )
        return ConversationHandler.END
    
    await query.message.reply_text(
        "📦 <b>نشر بوت من ZIP</b>\n"
        f"{'─' * 35}\n\n"
        "📎 أرسل ملف ZIP يحتوي على ملفات البوت\n\n"
        "💡 <b>المتطلبات:</b>\n"
        "• يجب أن يحتوي على ملف <code>main.py</code> أو <code>bot.py</code>\n"
        "• ضع <code>requirements.txt</code> لتثبيت المتطلبات تلقائياً\n"
        f"• الحد الأقصى للحجم: {MAX_FILE_SIZE_MB}MB\n\n"
        "❌ للإلغاء أرسل /cancel",
        parse_mode="HTML"
    )
    
    context.user_data['bot_action'] = 'deploy_zip'
    return CONVERSATION_STATES['WAIT_FILE']

async def handle_bot_file(update: Update, context: ContextTypes.DEFAULT_TYPE, db, pm):
    """معالجة ملف البوت"""
    doc = update.message.document
    
    if not doc:
        await update.message.reply_text(
            "❌ لم يتم اكتشاف ملف\n\n"
            "💡 أرسل ملف .py أو .zip"
        )
        return CONVERSATION_STATES['WAIT_FILE']
    
    try:
        # التحقق من الحجم
        if doc.file_size and doc.file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
            await update.message.reply_text(
                f"❌ <b>الملف كبير جداً</b>\n\n"
                f"الحد الأقصى: {MAX_FILE_SIZE_MB}MB\n"
                f"حجم الملف: {doc.file_size / (1024*1024):.1f}MB",
                parse_mode="HTML"
            )
            return CONVERSATION_STATES['WAIT_FILE']
        
        # التحقق من وجود عملية رفع/استبدال
        upload_bot_id = context.user_data.get('upload_bot_id')
        replace_bot_id = context.user_data.get('replace_bot_id')
        
        if upload_bot_id:
            return await handle_bot_file_upload(update, context, doc, upload_bot_id, db)
        elif replace_bot_id:
            return await handle_bot_file_replace(update, context, doc, replace_bot_id, db)
        
        # معالجة حسب نوع الملف
        if doc.file_name.endswith('.zip'):
            return await handle_bot_zip(update, context, db, pm)
        elif doc.file_name.endswith('.py'):
            return await handle_bot_py(update, context, doc, db)
        else:
            await update.message.reply_text(
                "❌ <b>صيغة غير مدعومة</b>\n\n"
                "الصيغ المدعومة:\n"
                "• ملفات Python (.py)\n"
                "• أرشيف ZIP (.zip)",
                parse_mode="HTML"
            )
            return CONVERSATION_STATES['WAIT_FILE']
            
    except Exception as e:
        logger.error(f"خطأ في معالجة الملف: {e}")
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)[:50]}")
        return ConversationHandler.END

async def handle_bot_py(update: Update, context: ContextTypes.DEFAULT_TYPE, doc, db):
    """معالجة ملف .py"""
    try:
        user_id = update.effective_user.id
        folder = generate_unique_folder("bot", user_id)
        bot_path = Path(BOTS_DIR) / folder
        bot_path.mkdir(parents=True, exist_ok=True)
        
        # تحميل الملف
        file = await context.bot.get_file(doc.file_id)
        file_path = bot_path / doc.file_name
        await file.download_to_drive(str(file_path))
        
        # البحث عن التوكن
        token = None
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                token = extract_token_from_code(content)
        except Exception as e:
            logger.warning(f"فشل قراءة الملف للبحث عن التوكن: {e}")
        
        if token:
            # التحقق من عدم استخدام التوكن
            existing_bot = db.get_bot_by_token(token)
            if existing_bot:
                await update.message.reply_text(
                    "⚠️ <b>التوكن مستخدم بالفعل</b>\n\n"
                    "هذا التوكن مسجل لبوت آخر.\n"
                    "استخدم توكن مختلف أو احذف البوت القديم.",
                    parse_mode="HTML"
                )
                shutil.rmtree(bot_path)
                return ConversationHandler.END
            
            # إضافة البوت
            bot_id = db.add_bot(user_id, token, doc.file_name, folder, doc.file_name)
            
            if bot_id:
                db.add_event_log(bot_id, "INFO", "✅ تم إضافة البوت بنجاح")
                await update.message.reply_text(
                    "✅ <b>تم إضافة البوت بنجاح!</b>\n"
                    f"{'─' * 35}\n\n"
                    f"🆔 المعرّف: <code>{bot_id}</code>\n"
                    f"📝 الاسم: <code>{safe_html_escape(doc.file_name)}</code>\n"
                    f"🔑 التوكن: <code>{token[:25]}...</code>\n\n"
                    "💡 يمكنك الآن تشغيل البوت من قائمة 'بوتاتي'",
                    parse_mode="HTML"
                )
                return ConversationHandler.END
            else:
                await update.message.reply_text("❌ فشل إضافة البوت. حاول مرة أخرى.")
                shutil.rmtree(bot_path)
                return ConversationHandler.END
        else:
            # طلب التوكن يدوياً
            context.user_data['bot_data'] = {
                'name': doc.file_name,
                'folder': folder,
                'main_file': doc.file_name
            }
            
            await update.message.reply_text(
                "⚠️ <b>لم يتم اكتشاف التوكن</b>\n"
                f"{'─' * 35}\n\n"
                "📎 أرسل توكن البوت:\n"
                "<code>123456789:ABCDefGHIjkLmnoPQRsTuvWXYz</code>\n\n"
                "💡 احصل على التوكن من @BotFather\n\n"
                "❌ للإلغاء أرسل /cancel",
                parse_mode="HTML"
            )
            return CONVERSATION_STATES['WAIT_TOKEN']
        
    except Exception as e:
        logger.error(f"خطأ في معالجة ملف البوت: {e}")
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)[:50]}")
        return ConversationHandler.END

async def handle_bot_zip(update: Update, context: ContextTypes.DEFAULT_TYPE, db, pm):
    """معالجة ملف ZIP"""
    doc = update.message.document
    user_id = update.effective_user.id
    folder = generate_unique_folder("zip", user_id)
    dest_path = Path(BOTS_DIR) / folder
    
    msg = await update.message.reply_text(
        "⏳ <b>جاري معالجة الملف...</b>\n\n"
        "📦 فك الضغط...",
        parse_mode="HTML"
    )
    
    try:
        # تحميل وفك الضغط
        file = await context.bot.get_file(doc.file_id)
        file_bytes = await file.download_as_bytearray()
        
        dest_path.mkdir(parents=True, exist_ok=True)
        
        zip_buffer = io.BytesIO(file_bytes)
        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            zip_ref.extractall(str(dest_path))
        
        await msg.edit_text(
            "⏳ <b>جاري معالجة الملف...</b>\n\n"
            "✅ فك الضغط\n"
            "🔍 البحث عن الملفات...",
            parse_mode="HTML"
        )
        
        # البحث عن الملف الرئيسي
        main_file = None
        candidates = ['main.py', 'bot.py', 'app.py', 'run.py', 'index.py', 'start.py']
        
        for candidate in candidates:
            for file_path in dest_path.rglob(candidate):
                main_file = str(file_path.relative_to(dest_path))
                break
            if main_file:
                break
        
        if not main_file:
            py_files = list(dest_path.rglob('*.py'))
            if py_files:
                main_file = str(py_files[0].relative_to(dest_path))
        
        # البحث عن التوكن
        token = None
        for py_file in dest_path.rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    token = extract_token_from_code(content)
                    if token:
                        break
            except:
                continue
        
        # تثبيت المتطلبات
        await msg.edit_text(
            "⏳ <b>جاري معالجة الملف...</b>\n\n"
            "✅ فك الضغط\n"
            "✅ اكتشاف الملفات\n"
            "📦 تثبيت المتطلبات...",
            parse_mode="HTML"
        )
        
        req_file = dest_path / 'requirements.txt'
        requirements_installed = False
        
        if req_file.exists():
            try:
                process = await asyncio.create_subprocess_exec(
                    sys.executable, "-m", "pip", "install", "-q", "-r", str(req_file),
                    cwd=str(dest_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await asyncio.wait_for(process.wait(), timeout=180)
                requirements_installed = True
            except asyncio.TimeoutError:
                logger.warning(f"⏱️ انتهت مهلة تثبيت المتطلبات للبوت {folder}")
            except Exception as e:
                logger.warning(f"⚠️ خطأ في تثبيت المتطلبات: {e}")
        
        # إضافة البوت
        bot_name = Path(doc.file_name).stem
        bot_id = db.add_bot(user_id, token or '', bot_name, folder, main_file or 'main.py')
        
        if bot_id:
            result_text = (
                "✅ <b>تم نشر البوت بنجاح!</b>\n"
                f"{'═' * 35}\n\n"
                f"🆔 المعرّف: <code>{bot_id}</code>\n"
                f"📝 الاسم: <code>{safe_html_escape(bot_name)}</code>\n"
                f"📄 الملف الرئيسي: <code>{safe_html_escape(main_file or 'غير مكتشف')}</code>\n"
            )
            
            if token:
                result_text += f"🔑 التوكن: <code>{token[:20]}...</code>\n"
            else:
                result_text += "⚠️ التوكن: لم يتم اكتشافه\n"
            
            if req_file.exists():
                result_text += f"📦 المتطلبات: {'✅ تم التثبيت' if requirements_installed else '⚠️ فشل التثبيت'}\n"
            
            result_text += "\n🎉 البوت جاهز للتشغيل!"
            
            await msg.edit_text(result_text, parse_mode="HTML")
            db.add_event_log(bot_id, "INFO", "📦 تم نشر البوت من ملف ZIP")
        else:
            await msg.edit_text("❌ فشل إضافة البوت. قد يكون التوكن مستخدماً.")
            if dest_path.exists():
                shutil.rmtree(dest_path)
        
        return ConversationHandler.END
        
    except zipfile.BadZipFile:
        await msg.edit_text("❌ الملف ليس أرشيف ZIP صالح")
        return ConversationHandler.END
    except Exception as e:
        logger.exception(f"خطأ في معالجة ZIP: {e}")
        await msg.edit_text(f"❌ خطأ: {str(e)[:50]}")
        if dest_path.exists():
            shutil.rmtree(dest_path)
        return ConversationHandler.END

async def handle_token(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """معالجة إدخال التوكن"""
    try:
        token = update.message.text.strip()
        
        if not validate_token(token):
            await update.message.reply_text(
                "❌ <b>توكن غير صحيح</b>\n\n"
                "الصيغة الصحيحة:\n"
                "<code>123456789:ABCDefGHIjkLmnoPQRsTuvWXYz1234567890</code>\n\n"
                "💡 احصل على التوكن من @BotFather",
                parse_mode="HTML"
            )
            return CONVERSATION_STATES['WAIT_TOKEN']
        
        existing_bot = db.get_bot_by_token(token)
        if existing_bot:
            await update.message.reply_text(
                "⚠️ <b>التوكن مستخدم بالفعل</b>",
                parse_mode="HTML"
            )
            return ConversationHandler.END
        
        bot_data = context.user_data.get('bot_data')
        if not bot_data:
            await update.message.reply_text("❌ خطأ. ابدأ من جديد بالضغط على 'إضافة بوت'")
            return ConversationHandler.END
        
        user_id = update.effective_user.id
        bot_id = db.add_bot(
            user_id,
            token,
            bot_data['name'],
            bot_data['folder'],
            bot_data['main_file']
        )
        
        if bot_id:
            db.add_event_log(bot_id, "INFO", "✅ تم إضافة البوت بنجاح")
            await update.message.reply_text(
                "✅ <b>تم إضافة البوت بنجاح!</b>\n"
                f"{'─' * 35}\n\n"
                f"🆔 المعرّف: <code>{bot_id}</code>\n"
                f"🔑 التوكن: <code>{token[:25]}...</code>\n\n"
                "💡 ابدأ البوت من قائمة 'بوتاتي'",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text("❌ فشل إضافة البوت")
        
        context.user_data.pop('bot_data', None)
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"خطأ في معالجة التوكن: {e}")
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)[:50]}")
        return ConversationHandler.END

# ============================================================================
# رفع واستبدال الملفات (للبوتات الموجودة)
# ============================================================================

async def handle_bot_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE, doc, bot_id, db):
    """معالجة رفع ملف للبوت"""
    try:
        bot = db.get_bot(bot_id)
        if not bot:
            await update.message.reply_text("❌ البوت غير موجود")
            context.user_data.pop('upload_bot_id', None)
            return ConversationHandler.END
        
        bot_path = Path(BOTS_DIR) / bot[5]
        file_path = bot_path / doc.file_name
        
        # تحميل الملف
        file = await context.bot.get_file(doc.file_id)
        await file.download_to_drive(str(file_path))
        
        await update.message.reply_text(
            f"✅ <b>تم رفع الملف</b>\n"
            f"{'─' * 35}\n\n"
            f"📄 الملف: <code>{safe_html_escape(doc.file_name)}</code>\n"
            f"💾 الحجم: {get_file_size(file_path)}",
            parse_mode="HTML"
        )
        
        db.add_event_log(bot_id, "INFO", f"📤 تم رفع الملف: {doc.file_name}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {str(e)[:50]}")
        logger.error(f"خطأ في رفع الملف: {e}")
    
    context.user_data.pop('upload_bot_id', None)
    return ConversationHandler.END

async def handle_bot_file_replace(update: Update, context: ContextTypes.DEFAULT_TYPE, doc, bot_id, db):
    """معالجة استبدال ملف البوت"""
    try:
        bot = db.get_bot(bot_id)
        if not bot:
            await update.message.reply_text("❌ البوت غير موجود")
            context.user_data.pop('replace_bot_id', None)
            return ConversationHandler.END
        
        bot_path = Path(BOTS_DIR) / bot[5]
        old_main_file = bot[6]
        old_file_path = bot_path / old_main_file
        new_file_path = bot_path / doc.file_name
        
        # إنشاء نسخة احتياطية
        if old_file_path.exists():
            backup_path = bot_path / f"{old_main_file}.backup"
            shutil.copy2(old_file_path, backup_path)
        
        # تحميل الملف الجديد
        file = await context.bot.get_file(doc.file_id)
        await file.download_to_drive(str(new_file_path))
        
        # تحديث قاعدة البيانات
        db.update_bot_status(bot_id, "stopped", None)
        
        import sqlite3
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("UPDATE bots SET main_file = ? WHERE id = ?", (doc.file_name, bot_id))
        conn.commit()
        conn.close()
        
        await update.message.reply_text(
            f"✅ <b>تم استبدال الملف</b>\n"
            f"{'─' * 35}\n\n"
            f"📄 الملف الجديد: <code>{safe_html_escape(doc.file_name)}</code>\n"
            f"📄 الملف القديم: <code>{safe_html_escape(old_main_file)}</code>\n"
            f"💾 نسخة احتياطية: <code>{old_main_file}.backup</code>\n\n"
            f"⚠️ تم إيقاف البوت - ابدأه مرة أخرى",
            parse_mode="HTML"
        )
        
        db.add_event_log(bot_id, "INFO", f"🔄 تم استبدال الملف: {old_main_file} → {doc.file_name}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {str(e)[:50]}")
        logger.error(f"خطأ في استبدال الملف: {e}")
    
    context.user_data.pop('replace_bot_id', None)
    return ConversationHandler.END

# ============================================================================
# حذف البوتات
# ============================================================================

async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """تأكيد حذف البوت"""
    query = update.callback_query
    await query.answer()
    
    try:
        bot_id = get_bot_id_from_callback(query.data)
        if not bot_id:
            await query.answer("❌ خطأ", show_alert=True)
            return
        
        bot = db.get_bot(bot_id)
        
        if not bot:
            await query.edit_message_text(
                "❌ البوت غير موجود",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 رجوع", callback_data="my_bots")
                ]])
            )
            return
        
        text = (
            f"⚠️ <b>تأكيد الحذف</b>\n"
            f"{'═' * 40}\n\n"
            f"🤖 البوت: <code>{safe_html_escape(bot[3])}</code>\n"
            f"🆔 المعرّف: <code>{bot_id}</code>\n\n"
            f"⚠️ <b>تحذير:</b>\n"
            f"• سيتم حذف جميع ملفات البوت\n"
            f"• سيتم حذف جميع السجلات\n"
            f"• <b>لا يمكن التراجع عن هذا!</b>"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("✅ نعم، احذف", callback_data=f"delete_{bot_id}"),
                InlineKeyboardButton("❌ إلغاء", callback_data=f"manage_{bot_id}")
            ]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"خطأ في تأكيد الحذف: {e}")
        await query.answer("❌ حدث خطأ", show_alert=True)

async def delete_bot_action(update: Update, context: ContextTypes.DEFAULT_TYPE, db, pm):
    """حذف البوت"""
    query = update.callback_query
    await query.answer("⏳ جاري حذف البوت...")
    
    try:
        bot_id = get_bot_id_from_callback(query.data)
        if not bot_id:
            await query.answer("❌ خطأ", show_alert=True)
            return
        
        bot = db.get_bot(bot_id)
        
        if not bot:
            await query.edit_message_text("❌ البوت غير موجود")
            return
        
        bot_name = bot[3]
        
        # إيقاف البوت إذا كان يعمل
        pm.stop_bot(bot_id)
        
        # حذف ملفات البوت
        bot_path = Path(BOTS_DIR) / bot[5]
        try:
            if bot_path.exists():
                shutil.rmtree(bot_path)
        except Exception as e:
            logger.warning(f"فشل حذف مجلد البوت: {e}")
        
        # حذف من قاعدة البيانات
        db.delete_bot(bot_id)
        
        await query.edit_message_text(
            "✅ <b>تم حذف البوت</b>\n"
            f"{'─' * 35}\n\n"
            f"🤖 البوت <code>{safe_html_escape(bot_name)}</code> تم إزالته نهائياً.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 العودة للبوتات", callback_data="my_bots")
            ]]),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"خطأ في حذف البوت: {e}")
        await query.message.reply_text(f"❌ حدث خطأ: {str(e)[:50]}")

# ============================================================================
# نظام الترقيات
# ============================================================================

async def request_upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """طلب الترقية"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    current_plan = db.get_user_plan(user_id, ADMIN_ID)
    
    if current_plan == 'supreme':
        await query.answer("👑 أنت بالفعل في أعلى خطة!", show_alert=True)
        return
    
    text = (
        f"💎 <b>طلب ترقية الخطة</b>\n"
        f"{'═' * 40}\n\n"
        f"📦 خطتك الحالية: {PLANS[current_plan]['emoji']} <b>{PLANS[current_plan]['name']}</b>\n\n"
        f"🆙 <b>اختر الخطة المطلوبة:</b>\n"
    )
    
    keyboard = []
    for plan_key, plan_config in PLANS.items():
        if plan_key != current_plan and plan_key != 'free':
            time_display = "♾️" if plan_config['time'] > 999999 else seconds_to_human(plan_config['time'])
            text += (
                f"\n{plan_config['emoji']} <b>{plan_config['name']}</b>\n"
                f"   ⏱️ {time_display} | 🤖 {plan_config['max_bots']} بوتات\n"
                f"   💰 {plan_config['price']}\n"
            )
            keyboard.append([InlineKeyboardButton(
                f"{plan_config['emoji']} {plan_config['name']} - {plan_config['price']}",
                callback_data=f"select_upgrade_{plan_key}"
            )])
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="my_plan")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def select_upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """اختيار خطة الترقية"""
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = update.effective_user.id
        parts = query.data.split("_")
        new_plan = parts[2] if len(parts) > 2 else None
        
        if not new_plan:
            await query.answer("❌ خطأ", show_alert=True)
            return
        
        current_plan = db.get_user_plan(user_id, ADMIN_ID)
        
        plan_config = PLANS.get(new_plan)
        if not plan_config:
            await query.answer("❌ خطة غير موجودة", show_alert=True)
            return
        
        # إضافة طلب الترقية
        request_id = db.add_upgrade_request(user_id, current_plan, new_plan)
        
        # إخطار الأدمن
        user = update.effective_user
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"📤 <b>طلب ترقية جديد</b>\n"
                    f"{'═' * 40}\n\n"
                    f"👤 المستخدم: @{user.username or 'N/A'}\n"
                    f"🆔 المعرّف: <code>{user_id}</code>\n"
                    f"📦 الخطة الحالية: {PLANS[current_plan]['name']}\n"
                    f"🆙 الخطة المطلوبة: {plan_config['emoji']} {plan_config['name']}\n"
                    f"💰 السعر: {plan_config['price']}\n"
                    f"🎫 معرّف الطلب: <code>{request_id}</code>\n"
                    f"📅 التاريخ: {get_current_time()[:19]}"
                ),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ قبول", callback_data=f"approve_upgrade_{request_id}"),
                        InlineKeyboardButton("❌ رفض", callback_data=f"reject_upgrade_{request_id}")
                    ]
                ]),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"فشل إخطار الأدمن بطلب الترقية: {e}")
        
        await query.edit_message_text(
            f"📤 <b>تم إرسال طلب الترقية</b>\n"
            f"{'─' * 35}\n\n"
            f"🆙 الخطة: {plan_config['emoji']} <b>{plan_config['name']}</b>\n"
            f"💰 السعر: <b>{plan_config['price']}</b>\n\n"
            f"💳 <b>طريقة الدفع:</b>\n"
            f"تواصل مع {DEVELOPER_USERNAME} لإتمام الدفع\n\n"
            f"⏳ سيقوم الأدمن بمراجعة طلبك قريباً",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجوع", callback_data="my_plan")
            ]]),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"خطأ في طلب الترقية: {e}")
        await query.message.reply_text(f"❌ حدث خطأ: {str(e)[:50]}")

async def approve_upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """الموافقة على طلب الترقية"""
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id != ADMIN_ID:
        await query.answer("⛔ صلاحيات الأدمن مطلوبة", show_alert=True)
        return
    
    try:
        parts = query.data.split("_")
        request_id = int(parts[2]) if len(parts) > 2 else None
        
        if not request_id:
            await query.answer("❌ خطأ", show_alert=True)
            return
        
        # جلب معلومات الطلب
        request = db.get_upgrade_request(request_id)
        if not request:
            await query.answer("❌ الطلب غير موجود", show_alert=True)
            return
        
        user_id = request[1]
        new_plan = request[3]
        
        # تطبيق الترقية
        db.approve_upgrade(request_id)
        
        plan_config = PLANS.get(new_plan, PLANS['free'])
        
        # إخطار المستخدم
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    f"🎉 <b>تهانينا! تمت ترقية خطتك</b>\n"
                    f"{'═' * 40}\n\n"
                    f"📦 الخطة الجديدة: {plan_config['emoji']} <b>{plan_config['name']}</b>\n\n"
                    f"✨ <b>المميزات:</b>\n"
                    f"   • 🤖 {plan_config['max_bots']} بوتات\n"
                    f"   • ⏱️ {seconds_to_human(plan_config['time'])}\n"
                    f"   • 💻 CPU: {plan_config['cpu_limit']}%\n"
                    f"   • 🧠 RAM: {plan_config['mem_limit']}MB\n\n"
                    f"🚀 استمتع بمميزاتك الجديدة!"
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass
        
        await query.edit_message_text(
            f"✅ <b>تم قبول طلب الترقية</b>\n\n"
            f"المستخدم: <code>{user_id}</code>\n"
            f"الخطة: {plan_config['emoji']} {plan_config['name']}",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"خطأ في الموافقة على الترقية: {e}")
        await query.answer("❌ حدث خطأ", show_alert=True)

async def reject_upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """رفض طلب الترقية"""
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id != ADMIN_ID:
        await query.answer("⛔ صلاحيات الأدمن مطلوبة", show_alert=True)
        return
    
    try:
        parts = query.data.split("_")
        request_id = int(parts[2]) if len(parts) > 2 else None
        
        if not request_id:
            await query.answer("❌ خطأ", show_alert=True)
            return
        
        # جلب معلومات الطلب
        request = db.get_upgrade_request(request_id)
        if not request:
            await query.answer("❌ الطلب غير موجود", show_alert=True)
            return
        
        user_id = request[1]
        
        # رفض الطلب
        db.reject_upgrade(request_id)
        
        # إخطار المستخدم
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    f"❌ <b>تم رفض طلب الترقية</b>\n\n"
                    f"للاستفسار تواصل مع {DEVELOPER_USERNAME}"
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass
        
        await query.edit_message_text(
            f"❌ <b>تم رفض طلب الترقية</b>\n"
            f"المستخدم: <code>{user_id}</code>",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"خطأ في رفض الترقية: {e}")
        await query.answer("❌ حدث خطأ", show_alert=True)

# ============================================================================
# إدارة المستخدمين
# ============================================================================

async def approve_user(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """قبول المستخدم"""
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id != ADMIN_ID:
        await query.answer("⛔ صلاحيات الأدمن مطلوبة", show_alert=True)
        return
    
    try:
        user_id = get_bot_id_from_callback(query.data)
        if not user_id:
            await query.answer("❌ خطأ", show_alert=True)
            return
        
        db.update_user_status(user_id, 'approved')
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=(
                    "🎉 <b>تهانينا! تم قبولك</b>\n"
                    f"{'─' * 35}\n\n"
                    "يمكنك الآن استخدام NeuroHost بالكامل.\n\n"
                    "🚀 أرسل /start للبدء!"
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass
        
        await query.edit_message_text(
            f"✅ تم قبول المستخدم <code>{user_id}</code>",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"خطأ في قبول المستخدم: {e}")
        await query.answer("❌ حدث خطأ", show_alert=True)

async def reject_user(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """رفض المستخدم"""
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id != ADMIN_ID:
        await query.answer("⛔ صلاحيات الأدمن مطلوبة", show_alert=True)
        return
    
    try:
        user_id = get_bot_id_from_callback(query.data)
        if not user_id:
            await query.answer("❌ خطأ", show_alert=True)
            return
        
        db.update_user_status(user_id, 'blocked')
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="🚫 <b>تم رفض طلبك</b>",
                parse_mode="HTML"
            )
        except Exception:
            pass
        
        await query.edit_message_text(
            f"❌ تم رفض المستخدم <code>{user_id}</code>",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"خطأ في رفض المستخدم: {e}")
        await query.answer("❌ حدث خطأ", show_alert=True)

# ============================================================================
# لوحة تحكم الأدمن
# ============================================================================

async def sys_status(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """حالة النظام"""
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id != ADMIN_ID:
        await query.answer("⛔ صلاحيات الأدمن مطلوبة", show_alert=True)
        return
    
    try:
        # جمع معلومات النظام
        cpu = mem = disk = 0
        mem_total = mem_used = disk_total = disk_used = 0
        process_count = 0
        
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            mem_total = psutil.virtual_memory().total / (1024**3)
            mem_used = psutil.virtual_memory().used / (1024**3)
            disk_total = psutil.disk_usage('/').total / (1024**3)
            disk_used = psutil.disk_usage('/').used / (1024**3)
            process_count = len(psutil.pids())
        except ImportError:
            pass
        
        # إحصائيات من قاعدة البيانات
        stats = db.get_system_stats()
        
        text = (
            f"📊 <b>حالة النظام - NeuroHost V8</b>\n"
            f"{'═' * 45}\n\n"
            f"💻 <b>موارد الخادم:</b>\n"
            f"   CPU: {render_bar(cpu)}\n"
            f"   RAM: {render_bar(mem)} ({mem_used:.1f}/{mem_total:.1f} GB)\n"
            f"   Disk: {render_bar(disk)} ({disk_used:.1f}/{disk_total:.1f} GB)\n"
            f"   العمليات: {process_count}\n\n"
            f"📈 <b>إحصائيات المنصة:</b>\n"
            f"   👥 المستخدمون: <b>{stats.get('approved_users', 0)}</b>\n"
            f"   🤖 البوتات: <b>{stats.get('total_bots', 0)}</b> ({stats.get('running_bots', 0)} نشط)\n"
            f"   ⏳ طلبات معلقة: <b>{stats.get('pending_users', 0)}</b> مستخدم\n"
            f"   📤 ترقيات معلقة: <b>{stats.get('pending_upgrades', 0)}</b>\n\n"
            f"💎 <b>توزيع الخطط:</b>\n"
        )
        
        for plan_key in PLANS.keys():
            plan_config = PLANS[plan_key]
            count = stats.get(f'plan_{plan_key}', 0)
            text += f"   {plan_config['emoji']} {plan_config['name']}: <b>{count}</b>\n"
        
        text += f"\n🕐 آخر تحديث: {get_current_time()[:19]}"
        
        keyboard = [
            [
                InlineKeyboardButton("👥 المستخدمون", callback_data="admin_users"),
                InlineKeyboardButton("🤖 البوتات", callback_data="admin_bots")
            ],
            [
                InlineKeyboardButton("📤 الترقيات", callback_data="admin_upgrades"),
                InlineKeyboardButton("⏳ المعلقون", callback_data="admin_pending")
            ],
            [
                InlineKeyboardButton("🔄 تحديث", callback_data="sys_status"),
                InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")
            ]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"خطأ في عرض حالة النظام: {e}")
        await query.answer("❌ حدث خطأ", show_alert=True)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """لوحة تحكم الأدمن"""
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id != ADMIN_ID:
        await query.answer("⛔ صلاحيات الأدمن مطلوبة", show_alert=True)
        return
    
    text = (
        f"👑 <b>لوحة تحكم الأدمن</b>\n"
        f"{'═' * 40}\n\n"
        f"مرحباً بك في لوحة التحكم الرئيسية.\n"
        f"اختر القسم الذي تريد إدارته:\n"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("📊 حالة النظام", callback_data="sys_status"),
            InlineKeyboardButton("👥 المستخدمون", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton("🤖 البوتات", callback_data="admin_bots"),
            InlineKeyboardButton("📤 الترقيات", callback_data="admin_upgrades")
        ],
        [
            InlineKeyboardButton("⏳ المعلقون", callback_data="admin_pending")
        ],
        [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """إدارة المستخدمين"""
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id != ADMIN_ID:
        await query.answer("⛔ صلاحيات الأدمن مطلوبة", show_alert=True)
        return
    
    try:
        users = db.get_all_users()
        
        text = (
            f"👥 <b>إدارة المستخدمين</b>\n"
            f"{'═' * 40}\n\n"
            f"📊 الإجمالي: <b>{len(users)}</b> مستخدم\n\n"
        )
        
        for user in users[:10]:
            user_id = user[0]
            username = user[1]
            status = user[4]
            plan = user[5] if len(user) > 5 else 'free'
            
            status_icon = {'approved': '✅', 'pending': '⏳', 'blocked': '🚫'}.get(status, '❓')
            plan_emoji = PLANS.get(plan, {}).get('emoji', '📦')
            
            text += f"{status_icon} <code>{user_id}</code> | @{username or 'N/A'} | {plan_emoji}\n"
        
        if len(users) > 10:
            text += f"\n... و {len(users) - 10} مستخدم آخر"
        
        keyboard = [
            [
                InlineKeyboardButton("⏳ المعلقون", callback_data="admin_pending"),
                InlineKeyboardButton("🚫 المحظورون", callback_data="admin_blocked")
            ],
            [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"خطأ في عرض المستخدمين: {e}")
        await query.answer("❌ حدث خطأ", show_alert=True)

async def admin_pending(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """المستخدمون المعلقون"""
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id != ADMIN_ID:
        await query.answer("⛔ صلاحيات الأدمن مطلوبة", show_alert=True)
        return
    
    try:
        pending = db.get_pending_users()
        
        if not pending:
            text = (
                f"⏳ <b>الطلبات المعلقة</b>\n"
                f"{'═' * 40}\n\n"
                f"✅ لا توجد طلبات معلقة حالياً"
            )
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]]
        else:
            text = (
                f"⏳ <b>الطلبات المعلقة ({len(pending)})</b>\n"
                f"{'═' * 40}\n\n"
            )
            
            keyboard = []
            for user in pending[:10]:
                user_id = user[0]
                username = user[1]
                text += f"👤 <code>{user_id}</code> | @{username or 'N/A'}\n"
                keyboard.append([
                    InlineKeyboardButton(f"✅ {user_id}", callback_data=f"approve_{user_id}"),
                    InlineKeyboardButton(f"❌ {user_id}", callback_data=f"reject_{user_id}")
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")])
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"خطأ في عرض المعلقين: {e}")
        await query.answer("❌ حدث خطأ", show_alert=True)

async def admin_blocked(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """المستخدمون المحظورون"""
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id != ADMIN_ID:
        await query.answer("⛔ صلاحيات الأدمن مطلوبة", show_alert=True)
        return
    
    try:
        blocked = db.get_blocked_users()
        
        text = (
            f"🚫 <b>المستخدمون المحظورون ({len(blocked)})</b>\n"
            f"{'═' * 40}\n\n"
        )
        
        if not blocked:
            text += "✅ لا يوجد مستخدمون محظورون"
        else:
            for user in blocked[:10]:
                user_id = user[0]
                username = user[1]
                text += f"🚫 <code>{user_id}</code> | @{username or 'N/A'}\n"
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_users")]]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"خطأ: {e}")
        await query.answer("❌ حدث خطأ", show_alert=True)

async def admin_upgrades(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """طلبات الترقية"""
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id != ADMIN_ID:
        await query.answer("⛔ صلاحيات الأدمن مطلوبة", show_alert=True)
        return
    
    try:
        upgrades = db.get_pending_upgrades()
        
        if not upgrades:
            text = (
                f"📤 <b>طلبات الترقية</b>\n"
                f"{'═' * 40}\n\n"
                f"✅ لا توجد طلبات معلقة"
            )
            keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]]
        else:
            text = (
                f"📤 <b>طلبات الترقية ({len(upgrades)})</b>\n"
                f"{'═' * 40}\n\n"
            )
            
            keyboard = []
            for req in upgrades[:10]:
                req_id = req[0]
                user_id = req[1]
                current_plan = req[2]
                requested_plan = req[3]
                
                current_emoji = PLANS.get(current_plan, {}).get('emoji', '📦')
                requested_emoji = PLANS.get(requested_plan, {}).get('emoji', '📦')
                
                text += f"#{req_id} | <code>{user_id}</code> | {current_emoji} → {requested_emoji}\n"
                keyboard.append([
                    InlineKeyboardButton(f"✅ #{req_id}", callback_data=f"approve_upgrade_{req_id}"),
                    InlineKeyboardButton(f"❌ #{req_id}", callback_data=f"reject_upgrade_{req_id}")
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")])
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"خطأ في عرض الترقيات: {e}")
        await query.answer("❌ حدث خطأ", show_alert=True)

async def admin_bots(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """إدارة البوتات"""
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id != ADMIN_ID:
        await query.answer("⛔ صلاحيات الأدمن مطلوبة", show_alert=True)
        return
    
    try:
        bots = db.get_all_bots()
        running = sum(1 for b in bots if b[4] == 'running')
        stopped = sum(1 for b in bots if b[4] == 'stopped')
        
        text = (
            f"🤖 <b>إدارة البوتات</b>\n"
            f"{'═' * 40}\n\n"
            f"📊 الإجمالي: <b>{len(bots)}</b>\n"
            f"🟢 نشطة: <b>{running}</b>\n"
            f"🔴 متوقفة: <b>{stopped}</b>\n\n"
        )
        
        for bot in bots[:10]:
            bot_id = bot[0]
            name = bot[3]
            status = bot[4]
            status_icon = "🟢" if status == "running" else "🔴"
            text += f"{status_icon} #{bot_id} | {safe_html_escape(name[:15])}\n"
        
        if len(bots) > 10:
            text += f"\n... و {len(bots) - 10} بوت آخر"
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"خطأ في عرض البوتات: {e}")
        await query.answer("❌ حدث خطأ", show_alert=True)

# ============================================================================
# إعدادات البوت والنسخ الاحتياطي
# ============================================================================

async def bot_backup(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """نسخ احتياطي للبوت"""
    query = update.callback_query
    await query.answer("⏳ جاري إنشاء النسخة الاحتياطية...")
    
    try:
        bot_id = get_bot_id_from_callback(query.data)
        if not bot_id:
            await query.answer("❌ خطأ", show_alert=True)
            return
        
        bot = db.get_bot(bot_id)
        if not bot:
            await query.answer("❌ البوت غير موجود", show_alert=True)
            return
        
        bot_path = Path(BOTS_DIR) / bot[5]
        
        if not bot_path.exists():
            await query.answer("❌ مجلد البوت غير موجود", show_alert=True)
            return
        
        # إنشاء ملف ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in bot_path.rglob('*'):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    arcname = file_path.relative_to(bot_path)
                    zip_file.write(file_path, arcname)
        
        zip_buffer.seek(0)
        
        # إرسال الملف
        zip_name = f"{bot[3]}_backup_{int(time.time())}.zip"
        await context.bot.send_document(
            chat_id=update.effective_user.id,
            document=InputFile(zip_buffer, filename=zip_name),
            caption=(
                f"📤 <b>نسخة احتياطية للبوت</b>\n"
                f"{'─' * 30}\n\n"
                f"🤖 البوت: <code>{safe_html_escape(bot[3])}</code>\n"
                f"📅 التاريخ: {get_current_time()[:10]}"
            ),
            parse_mode="HTML"
        )
        
        db.add_event_log(bot_id, "INFO", "📤 تم إنشاء نسخة احتياطية")
        await query.answer("✅ تم إرسال النسخة الاحتياطية")
        
    except Exception as e:
        logger.error(f"خطأ في النسخ الاحتياطي: {e}")
        await query.answer("❌ حدث خطأ", show_alert=True)

async def bot_settings(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """إعدادات البوت"""
    query = update.callback_query
    await query.answer()
    
    try:
        bot_id = get_bot_id_from_callback(query.data)
        if not bot_id:
            await query.answer("❌ خطأ", show_alert=True)
            return
        
        bot = db.get_bot(bot_id)
        if not bot:
            await query.edit_message_text("❌ البوت غير موجود")
            return
        
        auto_start = bot[28] if len(bot) > 28 else 0
        priority = bot[29] if len(bot) > 29 else 1
        
        text = (
            f"⚙️ <b>إعدادات البوت</b>\n"
            f"{'═' * 40}\n\n"
            f"🤖 البوت: <code>{safe_html_escape(bot[3])}</code>\n"
            f"📄 الملف الرئيسي: <code>{bot[6]}</code>\n\n"
            f"🔧 <b>الخيارات:</b>\n"
            f"   • التشغيل التلقائي: {'✅' if auto_start else '❌'}\n"
            f"   • الأولوية: {priority}\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔙 رجوع", callback_data=f"manage_{bot_id}")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"خطأ في إعدادات البوت: {e}")
        await query.answer("❌ حدث خطأ", show_alert=True)

async def clear_logs(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """مسح السجلات"""
    query = update.callback_query
    
    try:
        bot_id = get_bot_id_from_callback(query.data)
        if not bot_id:
            await query.answer("❌ خطأ", show_alert=True)
            return
        
        db.clear_bot_logs(bot_id)
        await query.answer("✅ تم مسح السجلات", show_alert=True)
        
        # إعادة عرض السجلات
        from handlers import view_logs
        await view_logs(update, context, db)
        
    except Exception as e:
        logger.error(f"خطأ في مسح السجلات: {e}")
        await query.answer("❌ حدث خطأ", show_alert=True)

# ============================================================================
# معالجات الإعدادات المتقدمة (مدمجة من advanced_handlers.py)
# ============================================================================

from settings_manager import settings_manager
from help_manager import help_manager
from formatters import MessageBuilder, TextFormatter, format_bold, format_code

async def admin_settings_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """لوحة إعدادات للأدمن (تحكم شامل)"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
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
    text += "═" * 40 + "\n\n"
    text += f"<code>{str(settings)}</code>\n\n"
    text += "<i>ملاحظة: يمكنك تعديل هذه الإعدادات في ملف settings.json</i>"

    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_settings_panel")]]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

# ============================================================================
# معالجات الإدارة المحسنة (مدمجة من enhanced_handlers.py)
# ============================================================================

async def admin_moderation_panel(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """لوحة الإشراف والإدارة المتقدمة 🛡️"""
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
        [InlineKeyboardButton("📊 إحصائيات الإشراف", callback_data="admin_moderation_stats")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel")]
    ]

    message = (
        "🛡️ <b>لوحة الإشراف والإدارة</b>\n"
        f"{'═' * 30}\n\n"
        "👇 اختر العملية المراد تنفيذها:\n\n"
        "🚫 <b>الحظر:</b> منع الوصول نهائياً\n"
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

    message = "🚫 <b>المستخدمون المحظورون</b>\n" + "═" * 30 + "\n\n"

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


async def admin_moderation_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """عرض إحصائيات الإشراف"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    blocked_users = db.get_blocked_users()
    pending_users = db.get_pending_users()

    message = (
        "📊 <b>إحصائيات الإشراف</b>\n"
        f"{'═' * 30}\n\n"
        f"🚫 المحظورون: {len(blocked_users)}\n"
        f"⏳ طلبات معلقة: {len(pending_users)}\n\n"
        f"{'─' * 30}\n"
        "⌚ آخر تحديث: الآن"
    )

    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="admin_moderation_panel")]]
    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

# ============================================================================
# معالجات الشراء والدفع (مدمجة من enhanced_handlers.py)
# ============================================================================

async def hosting_purchase_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """قائمة شراء وقت الاستضافة الإضافي 💳"""
    query = update.callback_query
    await query.answer()

    bot_id = context.user_data.get('selected_bot_id', 1)

    keyboard = [
        [InlineKeyboardButton("📅 أسبوع (7 أيام) - 5 ⭐", callback_data=f"buy_hosting_week_{bot_id}")],
        [InlineKeyboardButton("📆 شهر (30 يوم) - 15 ⭐", callback_data=f"buy_hosting_month_{bot_id}")],
        [InlineKeyboardButton("💝 تبرع", callback_data="donate_stars")],
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"manage_{bot_id}")]
    ]

    message = (
        "🕥 <b>شراء وقت استضافة إضافي</b>\n"
        f"{'═' * 30}\n\n"
        "⭐ اختر الباقة المناسبة:\n\n"
        "💡 <i>سيتم تحديث الوقت تلقائياً بعد الدفع</i>"
    )

    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )


async def donate_stars_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """معالج التبرعات بنجوم تلجرام 💝"""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("1 ⭐", callback_data="donate_amount_1")],
        [InlineKeyboardButton("5 ⭐", callback_data="donate_amount_5")],
        [InlineKeyboardButton("10 ⭐", callback_data="donate_amount_10")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]
    ]

    message = (
        "💝 <b>دعم المشروع بالتبرع</b>\n"
        f"{'═' * 30}\n\n"
        "❤️ ساهم في تطوير NeurHostX!\n\n"
        "كل نجم يساعد في:\n"
        "✨ تحسين الخدمات\n"
        "🚀 إضافة ميزات جديدة\n"
        "🛡️ تحسين الأمان"
    )

    await query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
