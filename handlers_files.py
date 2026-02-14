# ============================================================================
# معالجات إدارة الملفات - NeuroHost V8 Enhanced
# ============================================================================

import io
import zipfile
import shutil
import logging
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ContextTypes, ConversationHandler
from config import BOTS_DIR, MAX_FILE_SIZE_MB, MAX_EDIT_FILE_SIZE_MB, CONVERSATION_STATES
from helpers import (
    safe_html_escape, get_file_size, get_file_icon, 
    is_safe_path, get_bot_id_from_callback
)

logger = logging.getLogger(__name__)

# ============================================================================
# مدير الملفات الرئيسي
# ============================================================================

async def file_manager(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """مدير الملفات المحسن"""
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
        
        bot_path = Path(BOTS_DIR) / bot[5]
        
        if not bot_path.exists():
            await query.edit_message_text(
                "❌ مجلد البوت غير موجود",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 رجوع", callback_data=f"manage_{bot_id}")
                ]])
            )
            return
        
        # جمع معلومات الملفات
        items = []
        total_size = 0
        dir_count = 0
        file_count = 0
        
        try:
            for item in sorted(bot_path.iterdir()):
                if item.name.startswith('.') or item.name == '__pycache__':
                    continue
                
                if item.is_dir():
                    items.append((item.name, True, "", 0))
                    dir_count += 1
                else:
                    size_bytes = item.stat().st_size
                    size_str = get_file_size(item)
                    items.append((item.name, False, size_str, size_bytes))
                    total_size += size_bytes
                    file_count += 1
        except Exception as e:
            logger.error(f"خطأ قراءة مجلد البوت: {e}")
        
        # تنسيق الحجم الإجمالي
        if total_size < 1024:
            total_size_str = f"{total_size} B"
        elif total_size < 1024 * 1024:
            total_size_str = f"{total_size/1024:.1f} KB"
        else:
            total_size_str = f"{total_size/(1024*1024):.1f} MB"
        
        if not items:
            text = (
                f"📁 <b>مدير الملفات</b>\n"
                f"{'═' * 40}\n\n"
                f"🤖 البوت: <code>{safe_html_escape(bot[3])}</code>\n\n"
                f"📭 المجلد فارغ - لا توجد ملفات"
            )
            keyboard = [
                [InlineKeyboardButton("📤 رفع ملف", callback_data=f"upload_file_{bot_id}")],
                [InlineKeyboardButton("🔙 رجوع", callback_data=f"manage_{bot_id}")]
            ]
        else:
            text = (
                f"📁 <b>مدير الملفات</b>\n"
                f"{'═' * 40}\n\n"
                f"🤖 البوت: <code>{safe_html_escape(bot[3])}</code>\n"
                f"📊 الملفات: {file_count} | المجلدات: {dir_count}\n"
                f"💾 الحجم: {total_size_str}\n"
                f"{'─' * 40}\n\n"
            )
            
            keyboard = []
            
            # عرض الملفات
            for name, is_dir, size, _ in items[:15]:
                if is_dir:
                    text += f"📁 <code>{name}/</code>\n"
                else:
                    icon = get_file_icon(name)
                    text += f"{icon} <code>{name}</code> ({size})\n"
                    
                    # أزرار الملفات
                    if not is_dir:
                        row = []
                        short_name = name[:8] + "..." if len(name) > 10 else name
                        row.append(InlineKeyboardButton(f"👁️ {short_name}", callback_data=f"viewfile_{bot_id}_{name}"))
                        row.append(InlineKeyboardButton("✏️", callback_data=f"editfile_{bot_id}_{name}"))
                        row.append(InlineKeyboardButton("📥", callback_data=f"downloadfile_{bot_id}_{name}"))
                        row.append(InlineKeyboardButton("🗑️", callback_data=f"deletefile_{bot_id}_{name}"))
                        keyboard.append(row)
            
            if len(items) > 15:
                text += f"\n... و {len(items) - 15} عناصر إضافية"
            
            # أزرار التحكم
            keyboard.append([
                InlineKeyboardButton("📤 رفع ملف", callback_data=f"upload_file_{bot_id}"),
                InlineKeyboardButton("🔄 استبدال", callback_data=f"replace_file_{bot_id}")
            ])
            keyboard.append([
                InlineKeyboardButton("📥 تحميل الكل (ZIP)", callback_data=f"download_all_{bot_id}"),
                InlineKeyboardButton("🔄 تحديث", callback_data=f"files_{bot_id}")
            ])
            keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data=f"manage_{bot_id}")])
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"خطأ في مدير الملفات: {e}")
        await query.answer("❌ حدث خطأ", show_alert=True)

# ============================================================================
# عرض الملفات
# ============================================================================

async def view_file(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """عرض محتوى الملف"""
    query = update.callback_query
    await query.answer()
    
    try:
        # استخراج bot_id واسم الملف
        parts = query.data.split("_", 2)
        if len(parts) < 3:
            await query.answer("❌ خطأ في البيانات", show_alert=True)
            return
        
        bot_id = int(parts[1])
        filename = parts[2]
        
        bot = db.get_bot(bot_id)
        if not bot:
            await query.edit_message_text("❌ البوت غير موجود")
            return
        
        bot_path = Path(BOTS_DIR) / bot[5]
        file_path = bot_path / filename
        
        # التحقق من الأمان
        if not is_safe_path(bot_path, file_path):
            await query.answer("⛔ الوصول مرفوض", show_alert=True)
            return
        
        if not file_path.exists() or file_path.is_dir():
            await query.edit_message_text(
                "❌ الملف غير موجود",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 رجوع", callback_data=f"files_{bot_id}")
                ]])
            )
            return
        
        file_size_bytes = file_path.stat().st_size
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        # التحقق من حجم الملف
        if file_size_mb > MAX_EDIT_FILE_SIZE_MB:
            await query.edit_message_text(
                f"❌ <b>الملف كبير جداً للعرض</b>\n\n"
                f"📄 الملف: <code>{safe_html_escape(filename)}</code>\n"
                f"💾 الحجم: {file_size_mb:.2f} MB\n"
                f"📏 الحد الأقصى: {MAX_EDIT_FILE_SIZE_MB} MB\n\n"
                f"💡 يمكنك تحميل الملف بدلاً من ذلك",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📥 تحميل", callback_data=f"downloadfile_{bot_id}_{filename}")],
                    [InlineKeyboardButton("🔙 رجوع", callback_data=f"files_{bot_id}")]
                ]),
                parse_mode="HTML"
            )
            return
        
        # قراءة الملف
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(3000)
        except Exception as e:
            await query.edit_message_text(
                f"❌ لا يمكن قراءة الملف\n\n"
                f"قد يكون ملفاً ثنائياً.\n"
                f"يمكنك تحميله بدلاً من ذلك.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📥 تحميل", callback_data=f"downloadfile_{bot_id}_{filename}")],
                    [InlineKeyboardButton("🔙 رجوع", callback_data=f"files_{bot_id}")]
                ])
            )
            return
        
        icon = get_file_icon(filename)
        
        # تقصير المحتوى إذا كان طويلاً
        display_content = content[:2000]
        if len(content) > 2000:
            display_content += "\n\n... (تم قص المحتوى)"
        
        text = (
            f"{icon} <b>{safe_html_escape(filename)}</b>\n"
            f"{'─' * 40}\n"
            f"💾 الحجم: {get_file_size(file_path)}\n"
            f"{'─' * 40}\n\n"
            f"<code>{safe_html_escape(display_content)}</code>"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("✏️ تعديل", callback_data=f"editfile_{bot_id}_{filename}"),
                InlineKeyboardButton("📥 تحميل", callback_data=f"downloadfile_{bot_id}_{filename}")
            ],
            [
                InlineKeyboardButton("🗑️ حذف", callback_data=f"deletefile_{bot_id}_{filename}"),
                InlineKeyboardButton("🔄 تحديث", callback_data=f"viewfile_{bot_id}_{filename}")
            ],
            [InlineKeyboardButton("🔙 رجوع", callback_data=f"files_{bot_id}")]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"خطأ في عرض الملف: {e}")
        await query.answer("❌ حدث خطأ", show_alert=True)

# ============================================================================
# تحميل الملفات
# ============================================================================

async def download_file(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """تحميل ملف واحد"""
    query = update.callback_query
    await query.answer("⏳ جاري التحضير...")
    
    try:
        parts = query.data.split("_", 2)
        if len(parts) < 3:
            await query.answer("❌ خطأ", show_alert=True)
            return
        
        bot_id = int(parts[1])
        filename = parts[2]
        
        bot = db.get_bot(bot_id)
        if not bot:
            await query.answer("❌ البوت غير موجود", show_alert=True)
            return
        
        bot_path = Path(BOTS_DIR) / bot[5]
        file_path = bot_path / filename
        
        # التحقق من الأمان
        if not is_safe_path(bot_path, file_path):
            await query.answer("⛔ الوصول مرفوض", show_alert=True)
            return
        
        if not file_path.exists() or file_path.is_dir():
            await query.answer("❌ الملف غير موجود", show_alert=True)
            return
        
        await context.bot.send_document(
            chat_id=update.effective_user.id,
            document=InputFile(str(file_path), filename=filename),
            caption=f"📥 <b>تحميل ملف</b>\n\n📄 {safe_html_escape(filename)}\n💾 {get_file_size(file_path)}",
            parse_mode="HTML"
        )
        
        await query.answer("✅ تم إرسال الملف")
        
    except Exception as e:
        logger.error(f"خطأ في تحميل الملف: {e}")
        await query.answer(f"❌ خطأ", show_alert=True)

async def download_all(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """تحميل جميع الملفات كـ ZIP"""
    query = update.callback_query
    await query.answer("⏳ جاري إنشاء الأرشيف...")
    
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
        zip_name = f"{bot[3]}_files.zip"
        await context.bot.send_document(
            chat_id=update.effective_user.id,
            document=InputFile(zip_buffer, filename=zip_name),
            caption=f"📦 <b>جميع ملفات البوت</b>\n\n🤖 {safe_html_escape(bot[3])}",
            parse_mode="HTML"
        )
        
        await query.answer("✅ تم إرسال الأرشيف")
        
    except Exception as e:
        logger.error(f"خطأ في تحميل الكل: {e}")
        await query.answer("❌ حدث خطأ", show_alert=True)

# ============================================================================
# رفع الملفات
# ============================================================================

async def upload_file(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """بدء رفع ملف"""
    query = update.callback_query
    await query.answer()
    
    try:
        bot_id = get_bot_id_from_callback(query.data)
        if not bot_id:
            await query.answer("❌ خطأ", show_alert=True)
            return ConversationHandler.END
        
        bot = db.get_bot(bot_id)
        if not bot:
            await query.answer("❌ البوت غير موجود", show_alert=True)
            return ConversationHandler.END
        
        context.user_data['upload_bot_id'] = bot_id
        
        await query.message.reply_text(
            "📤 <b>رفع ملف جديد</b>\n"
            f"{'─' * 35}\n\n"
            "📎 أرسل الملف الذي تريد رفعه\n\n"
            f"📏 الحد الأقصى: {MAX_FILE_SIZE_MB} MB\n\n"
            "❌ للإلغاء أرسل /cancel",
            parse_mode="HTML"
        )
        
        return CONVERSATION_STATES['WAIT_FILE']
        
    except Exception as e:
        logger.error(f"خطأ في بدء الرفع: {e}")
        await query.answer("❌ حدث خطأ", show_alert=True)
        return ConversationHandler.END

# ============================================================================
# استبدال الملفات
# ============================================================================

async def replace_file(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """بدء استبدال ملف"""
    query = update.callback_query
    await query.answer()
    
    try:
        bot_id = get_bot_id_from_callback(query.data)
        if not bot_id:
            await query.answer("❌ خطأ", show_alert=True)
            return ConversationHandler.END
        
        bot = db.get_bot(bot_id)
        if not bot:
            await query.answer("❌ البوت غير موجود", show_alert=True)
            return ConversationHandler.END
        
        context.user_data['replace_bot_id'] = bot_id
        
        await query.message.reply_text(
            "🔄 <b>استبدال الملف الرئيسي</b>\n"
            f"{'─' * 35}\n\n"
            "📎 أرسل الملف الجديد\n\n"
            "💡 سيتم إنشاء نسخة احتياطية من الملف القديم\n\n"
            "❌ للإلغاء أرسل /cancel",
            parse_mode="HTML"
        )
        
        return CONVERSATION_STATES['WAIT_FILE']
        
    except Exception as e:
        logger.error(f"خطأ في بدء الاستبدال: {e}")
        await query.answer("❌ حدث خطأ", show_alert=True)
        return ConversationHandler.END

# ============================================================================
# تعديل الملفات
# ============================================================================

async def edit_file_start(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """بدء تعديل ملف"""
    query = update.callback_query
    await query.answer()
    
    try:
        parts = query.data.split("_", 2)
        if len(parts) < 3:
            await query.answer("❌ خطأ", show_alert=True)
            return ConversationHandler.END
        
        bot_id = int(parts[1])
        filename = parts[2]
        
        bot = db.get_bot(bot_id)
        if not bot:
            await query.edit_message_text("❌ البوت غير موجود")
            return ConversationHandler.END
        
        bot_path = Path(BOTS_DIR) / bot[5]
        file_path = bot_path / filename
        
        # التحقق من الأمان
        if not is_safe_path(bot_path, file_path):
            await query.answer("⛔ الوصول مرفوض", show_alert=True)
            return ConversationHandler.END
        
        if not file_path.exists() or file_path.is_dir():
            await query.edit_message_text("❌ الملف غير موجود")
            return ConversationHandler.END
        
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_EDIT_FILE_SIZE_MB:
            await query.edit_message_text(
                f"❌ <b>الملف كبير جداً للتعديل</b>\n\n"
                f"💾 الحجم: {file_size_mb:.2f} MB\n"
                f"📏 الحد الأقصى: {MAX_EDIT_FILE_SIZE_MB} MB",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 رجوع", callback_data=f"viewfile_{bot_id}_{filename}")
                ]]),
                parse_mode="HTML"
            )
            return ConversationHandler.END
        
        # حفظ بيانات التعديل
        context.user_data['edit_file'] = {
            'bot_id': bot_id,
            'filename': filename,
            'file_path': str(file_path)
        }
        
        await query.message.reply_text(
            f"✏️ <b>تعديل الملف</b>\n"
            f"{'─' * 35}\n\n"
            f"📄 الملف: <code>{safe_html_escape(filename)}</code>\n\n"
            "📝 أرسل المحتوى الجديد:\n"
            "• نص عادي للمحتوى الجديد\n"
            "• أو ملف بالمحتوى الجديد\n\n"
            "❌ للإلغاء أرسل /cancel",
            parse_mode="HTML"
        )
        
        return CONVERSATION_STATES['WAIT_FILE_EDIT']
        
    except Exception as e:
        logger.error(f"خطأ في بدء التعديل: {e}")
        await query.answer("❌ حدث خطأ", show_alert=True)
        return ConversationHandler.END

async def handle_file_edit(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """معالجة تعديل الملف"""
    edit_file_data = context.user_data.get('edit_file')
    if not edit_file_data:
        await update.message.reply_text("❌ خطأ. حاول مرة أخرى.")
        return ConversationHandler.END
    
    try:
        # الحصول على المحتوى الجديد
        if update.message.document:
            file = await context.bot.get_file(update.message.document.file_id)
            file_bytes = await file.download_as_bytearray()
            content = file_bytes.decode('utf-8')
        else:
            content = update.message.text
        
        file_path = edit_file_data['file_path']
        
        # إنشاء نسخة احتياطية
        backup_path = f"{file_path}.bak"
        shutil.copy2(file_path, backup_path)
        
        # كتابة المحتوى الجديد
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        bot_id = edit_file_data['bot_id']
        db.add_event_log(bot_id, "INFO", f"✏️ تم تعديل الملف: {edit_file_data['filename']}")
        
        await update.message.reply_text(
            f"✅ <b>تم تحديث الملف</b>\n"
            f"{'─' * 35}\n\n"
            f"📄 الملف: <code>{safe_html_escape(edit_file_data['filename'])}</code>\n"
            f"💾 نسخة احتياطية: <code>{edit_file_data['filename']}.bak</code>",
            parse_mode="HTML"
        )
        
        context.user_data.pop('edit_file', None)
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"خطأ في تعديل الملف: {e}")
        await update.message.reply_text(f"❌ خطأ: {str(e)[:50]}")
        return CONVERSATION_STATES['WAIT_FILE_EDIT']

# ============================================================================
# حذف الملفات
# ============================================================================

async def delete_file(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """حذف ملف"""
    query = update.callback_query
    await query.answer()
    
    try:
        parts = query.data.split("_", 2)
        if len(parts) < 3:
            await query.answer("❌ خطأ", show_alert=True)
            return
        
        bot_id = int(parts[1])
        filename = parts[2]
        
        bot = db.get_bot(bot_id)
        if not bot:
            await query.answer("❌ البوت غير موجود", show_alert=True)
            return
        
        bot_path = Path(BOTS_DIR) / bot[5]
        file_path = bot_path / filename
        
        # التحقق من الأمان
        if not is_safe_path(bot_path, file_path):
            await query.answer("⛔ الوصول مرفوض", show_alert=True)
            return
        
        # التحقق من أنه ليس الملف الرئيسي
        if filename == bot[6]:
            await query.answer("⚠️ لا يمكن حذف الملف الرئيسي", show_alert=True)
            return
        
        text = (
            f"⚠️ <b>تأكيد حذف الملف</b>\n"
            f"{'─' * 35}\n\n"
            f"📄 الملف: <code>{safe_html_escape(filename)}</code>\n\n"
            f"❗ لا يمكن التراجع عن هذا الإجراء"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("✅ حذف", callback_data=f"confirmdelfile_{bot_id}_{filename}"),
                InlineKeyboardButton("❌ إلغاء", callback_data=f"files_{bot_id}")
            ]
        ]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"خطأ في طلب حذف الملف: {e}")
        await query.answer("❌ حدث خطأ", show_alert=True)

async def confirm_delete_file(update: Update, context: ContextTypes.DEFAULT_TYPE, db):
    """تأكيد حذف الملف"""
    query = update.callback_query
    await query.answer("⏳ جاري الحذف...")
    
    try:
        parts = query.data.split("_", 2)
        if len(parts) < 3:
            await query.answer("❌ خطأ", show_alert=True)
            return
        
        bot_id = int(parts[1])
        filename = parts[2]
        
        bot = db.get_bot(bot_id)
        if not bot:
            await query.answer("❌ البوت غير موجود", show_alert=True)
            return
        
        bot_path = Path(BOTS_DIR) / bot[5]
        file_path = bot_path / filename
        
        if file_path.exists():
            file_path.unlink()
        
        db.add_event_log(bot_id, "INFO", f"🗑️ تم حذف الملف: {filename}")
        
        await query.answer("✅ تم حذف الملف", show_alert=True)
        
        # العودة لمدير الملفات
        await file_manager(update, context, db)
        
    except Exception as e:
        logger.error(f"خطأ في حذف الملف: {e}")
        await query.answer("❌ حدث خطأ", show_alert=True)
