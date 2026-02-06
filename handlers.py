# ============================================================================
# معالجات البوت الأساسية - NeuroHost V8 Enhanced
# ============================================================================

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import PLANS, ADMIN_ID, DEVELOPER_USERNAME
from helpers import (
    safe_html_escape, seconds_to_human, render_bar, get_current_time,
    format_bot_status, get_bot_id_from_callback
)
from database import Database

logger = logging.getLogger(__name__)

# ============================================================================
# أمر البداية والقائمة الرئيسية
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """أمر البداية - الواجهة الرئيسية"""
    user = update.effective_user
    db.add_user(user.id, user.username, user.first_name, ADMIN_ID)
    user_data = db.get_user(user.id)
    
    if not user_data:
        await update.message.reply_text("❌ خطأ في التسجيل. حاول مرة أخرى.")
        return
    
    status = user_data[4]
    
    # التحقق من حالة المستخدم
    if status == 'pending' and user.id != ADMIN_ID:
        await update.message.reply_text(
            "⏳ <b>طلبك تحت المراجعة</b>\n"
            f"{'─' * 35}\n\n"
            "سيتم إخطارك بمجرد الموافقة على طلبك.\n"
            "📬 شكراً لصبرك!",
            parse_mode="HTML"
        )
        
        # إخطار الأدمن
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"🔔 <b>طلب انضمام جديد</b>\n"
                    f"{'─' * 35}\n\n"
                    f"👤 المستخدم: @{user.username or 'N/A'}\n"
                    f"📝 الاسم: {safe_html_escape(user.first_name or 'N/A')}\n"
                    f"🆔 المعرّف: <code>{user.id}</code>\n"
                    f"📅 التاريخ: {get_current_time()[:10]}"
                ),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ قبول", callback_data=f"approve_{user.id}"),
                    InlineKeyboardButton("❌ رفض", callback_data=f"reject_{user.id}")
                ]]),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"فشل إخطار الأدمن: {e}")
        return
    
    if status == 'blocked':
        await update.message.reply_text(
            "🚫 <b>تم حظرك من استخدام هذه الخدمة</b>\n\n"
            f"للاستفسار: {DEVELOPER_USERNAME}",
            parse_mode="HTML"
        )
        return
    
    # عرض القائمة الرئيسية
    await _show_main_menu(update.message, user, db)

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """القائمة الرئيسية - callback"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    await _show_main_menu(query, user, db, edit=True)

async def _show_main_menu(target, user, db, edit=False):
    """عرض القائمة الرئيسية"""
    plan = db.get_user_plan(user.id, ADMIN_ID)
    plan_config = PLANS.get(plan, PLANS['free'])
    bots = db.get_user_bots(user.id)
    running_bots = sum(1 for b in bots if b[2] == 'running')
    total_remaining = sum(b[4] for b in bots if b[4])
    
    keyboard = [
        [
            InlineKeyboardButton("➕ إضافة بوت", callback_data="add_bot"),
            InlineKeyboardButton("📦 نشر ZIP", callback_data="deploy_zip")
        ],
        [InlineKeyboardButton(f"📂 بوتاتي ({len(bots)})", callback_data="my_bots")],
        [
            InlineKeyboardButton("💎 خطتي", callback_data="my_plan"),
            InlineKeyboardButton("ℹ️ مساعدة", callback_data="help")
        ],
        [
            InlineKeyboardButton("📊 إحصائياتي", callback_data="user_stats"),
            InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings")
        ]
    ]
    
    # أزرار الأدمن
    if user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("📊 حالة النظام", callback_data="sys_status")])
        keyboard.append([InlineKeyboardButton("👑 لوحة التحكم", callback_data="admin_panel")])
    
    text = (
        f"🚀 <b>NeuroHost V8 - نسخة المؤسسة</b>\n"
        f"{'═' * 40}\n\n"
        f"👋 مرحباً <b>{safe_html_escape(user.first_name or 'مستخدم')}</b>!\n\n"
        f"📦 <b>الخطة:</b> {plan_config['emoji']} {plan_config['name']}\n"
        f"🤖 <b>البوتات:</b> {len(bots)}/{plan_config['max_bots']} ({running_bots} نشط)\n"
        f"⏱️ <b>الوقت المتبقي:</b> {seconds_to_human(total_remaining)}\n"
        f"💻 <b>حد CPU:</b> {plan_config['cpu_limit']}%\n"
        f"🧠 <b>حد RAM:</b> {plan_config['mem_limit']} MB\n\n"
        f"💰 <b>السعر:</b> {plan_config['price']}"
    )
    
    if edit:
        await target.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    else:
        await target.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

# ============================================================================
# عرض وإدارة البوتات
# ============================================================================

async def my_bots(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """عرض بوتات المستخدم"""
    query = update.callback_query
    await query.answer()
    
    bots = db.get_user_bots(update.effective_user.id)
    
    if not bots:
        await query.edit_message_text(
            "📂 <b>لا توجد بوتات</b>\n"
            f"{'─' * 35}\n\n"
            "لم تضف أي بوتات بعد.\n"
            "ابدأ بإضافة بوتك الأول الآن! 🚀",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("➕ إضافة بوت", callback_data="add_bot"),
                    InlineKeyboardButton("📦 نشر ZIP", callback_data="deploy_zip")
                ],
                [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]
            ]),
            parse_mode="HTML"
        )
        return
    
    running_count = sum(1 for b in bots if b[2] == 'running')
    stopped_count = sum(1 for b in bots if b[2] == 'stopped')
    sleep_count = sum(1 for b in bots if b[6])
    total_time = sum(b[4] for b in bots if b[4])
    
    text = (
        f"📂 <b>بوتاتي ({len(bots)})</b>\n"
        f"{'═' * 40}\n\n"
        f"🟢 نشطة: <b>{running_count}</b>  |  "
        f"🔴 متوقفة: <b>{stopped_count}</b>  |  "
        f"😴 سكون: <b>{sleep_count}</b>\n"
        f"⏱️ إجمالي الوقت المتبقي: <b>{seconds_to_human(total_time)}</b>\n"
        f"{'─' * 40}\n\n"
    )
    
    keyboard = []
    
    for bot_id, name, status, pid, remaining, power, sleep_mode in bots:
        if status == "running":
            icon = "🟢"
        elif sleep_mode:
            icon = "😴"
        else:
            icon = "🔴"
        
        time_str = seconds_to_human(remaining) if remaining else "⏳ انتهى"
        display_name = name[:15] + "..." if len(name) > 15 else name
        label = f"{icon} {display_name} | {time_str}"
        keyboard.append([InlineKeyboardButton(label, callback_data=f"manage_{bot_id}")])
    
    keyboard.extend([
        [
            InlineKeyboardButton("➕ إضافة بوت", callback_data="add_bot"),
            InlineKeyboardButton("📦 نشر ZIP", callback_data="deploy_zip")
        ],
        [
            InlineKeyboardButton("🔄 تحديث", callback_data="my_bots"),
            InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")
        ]
    ])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def manage_bot(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """إدارة البوت"""
    query = update.callback_query
    await query.answer()
    
    bot_id = get_bot_id_from_callback(query.data)
    if not bot_id:
        await query.edit_message_text("❌ خطأ في البيانات")
        return
    
    bot = db.get_bot(bot_id)
    
    if not bot:
        await query.edit_message_text(
            "❌ البوت غير موجود أو تم حذفه",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 رجوع", callback_data="my_bots")
            ]])
        )
        return
    
    await _show_manage_bot(query, bot, db)

async def _show_manage_bot(query, bot, db):
    """عرض واجهة إدارة البوت"""
    bot_id = bot[0]
    name = bot[3]
    status = bot[4]
    remaining = bot[11]
    sleep_mode = bot[15]
    cpu = bot[21] or 0
    mem = bot[22] or 0
    restart_count = bot[17] or 0
    uptime = bot[25] or 0
    total_seconds = bot[10] or 1
    
    # حساب النسبة المئوية للوقت المتبقي
    time_percent = (remaining / total_seconds * 100) if total_seconds > 0 else 0
    
    status_icon, status_text = format_bot_status(status, sleep_mode)
    
    text = (
        f"🤖 <b>{safe_html_escape(name)}</b>\n"
        f"{'═' * 40}\n\n"
        f"🆔 <b>المعرّف:</b> <code>{bot_id}</code>\n"
        f"📡 <b>الحالة:</b> {status_icon} {status_text}\n\n"
        f"⏱️ <b>الوقت المتبقي:</b>\n"
        f"   {seconds_to_human(remaining)}\n"
        f"   {render_bar(time_percent)}\n\n"
    )
    
    if status == "running":
        text += (
            f"📊 <b>الاستخدام الحالي:</b>\n"
            f"   • CPU: {render_bar(cpu)}\n"
            f"   • RAM: {mem:.1f} MB\n"
            f"   • وقت التشغيل: {seconds_to_human(uptime)}\n"
            f"   • إعادة التشغيل: {restart_count}x\n\n"
        )
    
    if sleep_mode:
        text += "⚠️ <b>البوت في وضع السكون</b>\n   استخدم الاسترجاع لإيقاظه\n\n"
    
    if 0 < remaining < 3600:
        text += "⚠️ <b>تنبيه:</b> الوقت ينفد قريباً!\n\n"
    
    keyboard = []
    
    # أزرار التحكم الرئيسية
    if status == "stopped" and not sleep_mode:
        keyboard.append([InlineKeyboardButton("▶️ تشغيل", callback_data=f"start_{bot_id}")])
    elif status == "running":
        keyboard.append([
            InlineKeyboardButton("⏹️ إيقاف", callback_data=f"stop_{bot_id}"),
            InlineKeyboardButton("🔄 إعادة تشغيل", callback_data=f"restart_{bot_id}")
        ])
    
    if sleep_mode:
        keyboard.append([InlineKeyboardButton("✨ إيقاظ (استرجاع مجاني)", callback_data=f"recover_{bot_id}")])
    
    # أزرار الإدارة
    keyboard.extend([
        [
            InlineKeyboardButton("⏱️ الوقت", callback_data=f"time_{bot_id}"),
            InlineKeyboardButton("📊 إحصائيات", callback_data=f"stats_{bot_id}")
        ],
        [
            InlineKeyboardButton("📜 السجلات", callback_data=f"logs_{bot_id}"),
            InlineKeyboardButton("📁 الملفات", callback_data=f"files_{bot_id}")
        ],
        [
            InlineKeyboardButton("⚙️ إعدادات", callback_data=f"bot_settings_{bot_id}"),
            InlineKeyboardButton("📤 نسخ احتياطي", callback_data=f"backup_{bot_id}")
        ],
        [InlineKeyboardButton("🗑️ حذف البوت", callback_data=f"confirm_del_{bot_id}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="my_bots")]
    ])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

# ============================================================================
# تشغيل وإيقاف البوتات
# ============================================================================

async def start_bot_action(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, pm):
    """بدء البوت"""
    query = update.callback_query
    await query.answer("⏳ جاري بدء البوت...")
    
    try:
        bot_id = get_bot_id_from_callback(query.data)
        if not bot_id:
            await query.answer("❌ خطأ في البيانات", show_alert=True)
            return
        
        success, msg = await pm.start_bot(bot_id, context.application)
        
        await query.message.reply_text(msg, parse_mode="HTML")
        
        # إعادة عرض واجهة إدارة البوت
        bot = db.get_bot(bot_id)
        if bot:
            await _show_manage_bot(query, bot, db)
    except Exception as e:
        logger.error(f"خطأ في بدء البوت: {e}")
        await query.message.reply_text(f"❌ حدث خطأ: {str(e)[:50]}")

async def stop_bot_action(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, pm):
    """إيقاف البوت"""
    query = update.callback_query
    await query.answer("⏳ جاري إيقاف البوت...")
    
    try:
        bot_id = get_bot_id_from_callback(query.data)
        if not bot_id:
            await query.answer("❌ خطأ في البيانات", show_alert=True)
            return
        
        pm.stop_bot(bot_id)
        
        await query.message.reply_text("✅ تم إيقاف البوت بنجاح", parse_mode="HTML")
        
        # إعادة عرض واجهة إدارة البوت
        bot = db.get_bot(bot_id)
        if bot:
            await _show_manage_bot(query, bot, db)
    except Exception as e:
        logger.error(f"خطأ في إيقاف البوت: {e}")
        await query.message.reply_text(f"❌ حدث خطأ: {str(e)[:50]}")

async def restart_bot_action(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, pm):
    """إعادة تشغيل البوت"""
    query = update.callback_query
    await query.answer("⏳ جاري إعادة تشغيل البوت...")
    
    try:
        bot_id = get_bot_id_from_callback(query.data)
        if not bot_id:
            await query.answer("❌ خطأ في البيانات", show_alert=True)
            return
        
        success, msg = await pm.restart_bot(bot_id, context.application)
        
        if success:
            await query.message.reply_text("✅ تم إعادة تشغيل البوت بنجاح", parse_mode="HTML")
        else:
            await query.message.reply_text(msg, parse_mode="HTML")
        
        # إعادة عرض واجهة إدارة البوت
        bot = db.get_bot(bot_id)
        if bot:
            await _show_manage_bot(query, bot, db)
    except Exception as e:
        logger.error(f"خطأ في إعادة تشغيل البوت: {e}")
        await query.message.reply_text(f"❌ حدث خطأ: {str(e)[:50]}")

# ============================================================================
# إدارة الوقت
# ============================================================================

async def time_management(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """إدارة الوقت"""
    query = update.callback_query
    await query.answer()
    
    bot_id = get_bot_id_from_callback(query.data)
    if not bot_id:
        await query.answer("❌ خطأ", show_alert=True)
        return
    
    bot = db.get_bot(bot_id)
    if not bot:
        await query.edit_message_text("❌ البوت غير موجود")
        return
    
    await _show_time_management(query, bot, db)

async def _show_time_management(query, bot, db):
    """عرض واجهة إدارة الوقت"""
    bot_id = bot[0]
    user_id = bot[1]
    remaining = bot[11]
    total = bot[10]
    sleep_mode = bot[15]
    
    plan = db.get_user_plan(user_id, ADMIN_ID)
    plan_config = PLANS.get(plan, PLANS['free'])
    
    time_percent = (remaining / total * 100) if total > 0 else 0
    
    text = (
        f"⏱️ <b>إدارة الوقت</b>\n"
        f"{'═' * 40}\n\n"
        f"📦 <b>الخطة:</b> {plan_config['emoji']} {plan_config['name']}\n\n"
        f"⏳ <b>الوقت المتبقي:</b>\n"
        f"   {seconds_to_human(remaining)}\n"
        f"   {render_bar(time_percent)}\n\n"
        f"⏱️ <b>الوقت الإجمالي:</b> {seconds_to_human(total)}\n"
        f"🎯 <b>الحد الأقصى للخطة:</b> {seconds_to_human(plan_config['time'])}\n\n"
    )
    
    keyboard = []
    
    # أزرار إضافة الوقت
    if remaining < plan_config['time']:
        text += "📈 <b>إضافة وقت:</b>\n"
        keyboard.append([
            InlineKeyboardButton("➕ 1 ساعة", callback_data=f"addtime_{bot_id}_3600"),
            InlineKeyboardButton("➕ 3 ساعات", callback_data=f"addtime_{bot_id}_10800")
        ])
        keyboard.append([
            InlineKeyboardButton("➕ 6 ساعات", callback_data=f"addtime_{bot_id}_21600"),
            InlineKeyboardButton("➕ 12 ساعة", callback_data=f"addtime_{bot_id}_43200")
        ])
        keyboard.append([
            InlineKeyboardButton("➕ 24 ساعة", callback_data=f"addtime_{bot_id}_86400"),
            InlineKeyboardButton("➕ أقصى حد", callback_data=f"addtime_{bot_id}_max")
        ])
    else:
        text += "✅ <b>لقد وصلت إلى الحد الأقصى للوقت</b>\n\n"
    
    # استرجاع يومي
    if sleep_mode and db.can_user_recover(user_id):
        text += "\n✨ <b>الاسترجاع اليومي متاح!</b>\n   احصل على ساعتين مجاناً\n"
        keyboard.append([InlineKeyboardButton("🔧 استرجاع مجاني (+2 ساعة)", callback_data=f"recover_{bot_id}")])
    elif not db.can_user_recover(user_id):
        text += "\n⏳ <b>الاسترجاع اليومي:</b> مستخدم (يتجدد غداً)\n"
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data=f"manage_{bot_id}")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def add_time_action(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """إضافة وقت"""
    query = update.callback_query
    await query.answer()
    
    try:
        parts = query.data.split("_")
        bot_id = int(parts[1])
        time_value = parts[2]
        
        bot = db.get_bot(bot_id)
        if not bot:
            await query.edit_message_text("❌ البوت غير موجود")
            return
        
        user_id = bot[1]
        plan = db.get_user_plan(user_id, ADMIN_ID)
        plan_config = PLANS.get(plan, PLANS['free'])
        
        current_total = bot[10]
        current_remaining = bot[11]
        
        # حساب الوقت المضاف
        if time_value == "max":
            seconds = plan_config['time'] - current_total
        else:
            seconds = int(time_value)
        
        new_total = current_total + seconds
        
        # التحقق من عدم تجاوز الحد
        if new_total > plan_config['time']:
            await query.answer("⚠️ سيتجاوز هذا حد الخطة", show_alert=True)
            return
        
        new_remaining = current_remaining + seconds
        
        db.update_bot_resources(
            bot_id,
            total_seconds=new_total,
            remaining_seconds=new_remaining,
            warned_low=0
        )
        
        await query.message.reply_text(
            f"✅ <b>تم إضافة الوقت</b>\n"
            f"{'─' * 30}\n\n"
            f"⏱️ تمت إضافة: <b>{seconds_to_human(seconds)}</b>\n"
            f"⏱️ الوقت الجديد: <b>{seconds_to_human(new_remaining)}</b>",
            parse_mode="HTML"
        )
        
        db.add_event_log(bot_id, "INFO", f"✅ تمت إضافة {seconds_to_human(seconds)} من الوقت")
        
        # إعادة عرض واجهة إدارة الوقت
        bot = db.get_bot(bot_id)
        if bot:
            await _show_time_management(query, bot, db)
        
    except Exception as e:
        logger.error(f"خطأ في إضافة الوقت: {e}")
        await query.message.reply_text(f"❌ حدث خطأ: {str(e)[:50]}")

async def recover_bot(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, pm):
    """استرجاع البوت"""
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
        
        user_id = bot[1]
        
        if not db.can_user_recover(user_id):
            await query.answer("⚠️ تم استخدام الاسترجاع بالفعل اليوم", show_alert=True)
            return
        
        # استخدام الاسترجاع
        db.use_user_recovery(user_id)
        
        # إضافة ساعتين
        recovery_time = 7200
        db.update_bot_resources(
            bot_id,
            remaining_seconds=recovery_time,
            total_seconds=recovery_time
        )
        
        # إيقاظ البوت من السكون
        db.set_sleep_mode(bot_id, False)
        db.add_event_log(bot_id, "INFO", "🔧 تم استخدام الاسترجاع اليومي (+2 ساعة)")
        
        # محاولة تشغيل البوت
        success, msg = await pm.start_bot(bot_id, context.application)
        
        result_text = (
            "✅ <b>الاسترجاع نجح!</b>\n"
            f"{'─' * 30}\n\n"
            "📝 <b>التفاصيل:</b>\n"
            "   ✓ تمت إضافة ساعتين\n"
            "   ✓ تم إيقاظ البوت من السكون\n"
        )
        
        if success:
            result_text += "   ✓ البوت يعمل الآن\n"
        else:
            result_text += f"   ⚠️ {msg}\n"
        
        result_text += "\n⏰ الاسترجاع التالي متاح غداً"
        
        await query.message.reply_text(result_text, parse_mode="HTML")
        
        # إعادة عرض واجهة إدارة البوت
        bot = db.get_bot(bot_id)
        if bot:
            await _show_manage_bot(query, bot, db)
        
    except Exception as e:
        logger.error(f"خطأ في استرجاع البوت: {e}")
        await query.message.reply_text(f"❌ حدث خطأ: {str(e)[:50]}")

# ============================================================================
# السجلات والإحصائيات
# ============================================================================

async def view_logs(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """عرض السجلات"""
    query = update.callback_query
    await query.answer()
    
    bot_id = get_bot_id_from_callback(query.data)
    if not bot_id:
        await query.answer("❌ خطأ", show_alert=True)
        return
    
    logs = db.get_bot_logs(bot_id, limit=25)
    
    text = f"📜 <b>سجلات البوت #{bot_id}</b>\n{'═' * 40}\n\n"
    
    if not logs:
        text += "📭 لا توجد أحداث مسجلة بعد"
    else:
        for event_type, message, timestamp in logs:
            icon = {
                'INFO': 'ℹ️',
                'WARNING': '⚠️',
                'ERROR': '❌',
                'CRITICAL': '🔴',
                'DEBUG': '🔍'
            }.get(event_type, '📝')
            
            date_str = timestamp[:16] if len(timestamp) > 16 else timestamp
            
            text += f"{icon} <code>{date_str}</code>\n"
            text += f"   {safe_html_escape(message[:70])}\n\n"
    
    keyboard = [
        [
            InlineKeyboardButton("🔄 تحديث", callback_data=f"logs_{bot_id}"),
            InlineKeyboardButton("🗑️ مسح السجلات", callback_data=f"clear_logs_{bot_id}")
        ],
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"manage_{bot_id}")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def bot_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """إحصائيات البوت"""
    query = update.callback_query
    await query.answer()
    
    bot_id = get_bot_id_from_callback(query.data)
    if not bot_id:
        await query.answer("❌ خطأ", show_alert=True)
        return
    
    bot = db.get_bot(bot_id)
    if not bot:
        await query.edit_message_text("❌ البوت غير موجود")
        return
    
    logs = db.get_bot_logs(bot_id, limit=100)
    
    info_count = sum(1 for l in logs if l[0] == 'INFO')
    warning_count = sum(1 for l in logs if l[0] == 'WARNING')
    error_count = sum(1 for l in logs if l[0] == 'ERROR')
    critical_count = sum(1 for l in logs if l[0] == 'CRITICAL')
    
    uptime = bot[25] or 0
    restart_count = bot[17] or 0
    cpu = bot[21] or 0
    mem = bot[22] or 0
    remaining = bot[11] or 0
    total_time = bot[10] or 0
    
    usage_percent = ((total_time - remaining) / total_time * 100) if total_time > 0 else 0
    stability_score = max(0, 100 - (error_count * 5) - (critical_count * 10) - (restart_count * 3))
    
    text = (
        f"📊 <b>إحصائيات البوت</b>\n"
        f"{'═' * 40}\n\n"
        f"📝 <b>المعلومات الأساسية:</b>\n"
        f"   • الاسم: <code>{safe_html_escape(bot[3])}</code>\n"
        f"   • المعرّف: <code>{bot_id}</code>\n"
        f"   • تاريخ الإنشاء: {bot[8][:10] if bot[8] else 'غير معروف'}\n\n"
        f"⏱️ <b>استخدام الوقت:</b>\n"
        f"   • التشغيل الحالي: {seconds_to_human(uptime)}\n"
        f"   • الوقت المتبقي: {seconds_to_human(remaining)}\n"
        f"   • الوقت الإجمالي: {seconds_to_human(total_time)}\n"
        f"   • نسبة الاستخدام: {usage_percent:.1f}%\n"
        f"   {render_bar(usage_percent)}\n\n"
        f"🔄 <b>الأداء والاستقرار:</b>\n"
        f"   • إعادة التشغيل: {restart_count} مرة\n"
        f"   • CPU: {cpu:.1f}%\n"
        f"   • RAM: {mem:.1f} MB\n"
        f"   • مؤشر الاستقرار: {stability_score}%\n"
        f"   {render_bar(stability_score)}\n\n"
        f"📜 <b>ملخص السجلات:</b>\n"
        f"   • ℹ️ معلومات: {info_count}\n"
        f"   • ⚠️ تحذيرات: {warning_count}\n"
        f"   • ❌ أخطاء: {error_count}\n"
        f"   • 🔴 حرجة: {critical_count}"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🔄 تحديث", callback_data=f"stats_{bot_id}"),
            InlineKeyboardButton("📜 السجلات", callback_data=f"logs_{bot_id}")
        ],
        [InlineKeyboardButton("🔙 رجوع", callback_data=f"manage_{bot_id}")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

# ============================================================================
# الخطط والترقيات
# ============================================================================

async def my_plan(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """خطتي"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    plan = db.get_user_plan(user_id, ADMIN_ID)
    plan_config = PLANS.get(plan, PLANS['free'])
    
    bots = db.get_user_bots(user_id)
    running_bots = sum(1 for b in bots if b[2] == 'running')
    total_time_used = sum(b[10] - b[4] for b in bots if b[10] and b[4])
    
    time_display = "♾️ لا نهائي" if plan_config['time'] > 999999 else seconds_to_human(plan_config['time'])
    bots_display = "∞" if plan_config['max_bots'] >= 50 else str(plan_config['max_bots'])
    
    text = (
        f"💎 <b>خطتي: {plan_config['emoji']} {plan_config['name']}</b>\n"
        f"{'═' * 45}\n\n"
        f"📊 <b>حدود الخطة:</b>\n"
        f"   ⏱️ وقت الاستضافة: <b>{time_display}</b>\n"
        f"   🤖 البوتات: <b>{len(bots)}/{bots_display}</b>\n"
        f"   💻 حد CPU: <b>{plan_config['cpu_limit']}%</b>\n"
        f"   🧠 حد RAM: <b>{plan_config['mem_limit']} MB</b>\n\n"
        f"📈 <b>الاستخدام:</b>\n"
        f"   • البوتات النشطة: {running_bots}\n"
        f"   • الوقت المستخدم: {seconds_to_human(total_time_used)}\n\n"
    )
    
    if 'features' in plan_config:
        text += "✨ <b>المميزات:</b>\n"
        for feature in plan_config['features']:
            text += f"   ✓ {feature}\n"
        text += "\n"
    
    text += f"💰 <b>السعر:</b> {plan_config['price']}"
    
    # عرض الخطط الأخرى المتاحة
    if plan != 'supreme':
        text += "\n\n🆙 <b>ترقية متاحة:</b>\n"
        for pkey, pconfig in PLANS.items():
            if pkey != plan and pkey != 'free':
                text += f"   • {pconfig['emoji']} {pconfig['name']}: {pconfig['price']}\n"
    
    keyboard = []
    
    if plan != 'supreme':
        keyboard.append([InlineKeyboardButton("📤 طلب ترقية", callback_data="request_upgrade")])
    
    keyboard.extend([
        [InlineKeyboardButton("📜 سجل الطلبات", callback_data="upgrade_history")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]
    ])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def upgrade_history(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """سجل طلبات الترقية"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    history = db.get_user_upgrade_history(user_id)
    
    text = f"📜 <b>سجل طلبات الترقية</b>\n{'═' * 40}\n\n"
    
    if not history:
        text += "📭 لا توجد طلبات سابقة"
    else:
        for req in history[:10]:
            req_id = req[0]
            current_plan = req[2]
            requested_plan = req[3]
            status = req[4]
            created_at = req[5][:10] if req[5] else "N/A"
            
            status_icon = {
                'pending': '⏳',
                'approved': '✅',
                'rejected': '❌'
            }.get(status, '❓')
            
            text += (
                f"{status_icon} #{req_id} | {PLANS.get(current_plan, {}).get('emoji', '📦')} → "
                f"{PLANS.get(requested_plan, {}).get('emoji', '📦')}\n"
                f"   📅 {created_at} | {status}\n\n"
            )
    
    keyboard = [
        [InlineKeyboardButton("🔙 رجوع", callback_data="my_plan")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

# ============================================================================
# المساعدة والإعدادات
# ============================================================================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر المساعدة"""
    query = update.callback_query
    if query:
        await query.answer()
    
    text = (
        "ℹ️ <b>مساعدة NeuroHost V8</b>\n"
        f"{'═' * 40}\n\n"
        "<b>🚀 البدء السريع:</b>\n"
        "1️⃣ أضف بوت جديد (ملف .py أو ZIP)\n"
        "2️⃣ سيتم اكتشاف التوكن تلقائياً\n"
        "3️⃣ أدر البوت من قائمة 'بوتاتي'\n"
        "4️⃣ راقب الأداء والسجلات\n\n"
        "<b>📁 مدير الملفات:</b>\n"
        "• 👁️ عرض محتوى الملفات\n"
        "• ✏️ تعديل الملفات مباشرة\n"
        "• 📤 رفع ملفات جديدة\n"
        "• 📥 تحميل الملفات\n"
        "• 🔄 استبدال الملفات\n\n"
        "<b>💎 الخطط المتاحة:</b>\n"
        "• 🔵 مجاني: 2 بوتات، 24 ساعة\n"
        "• 🟢 احترافي: 5 بوتات، أسبوع\n"
        "• 🟣 فائق: 10 بوتات، شهر\n"
        "• 👑 أسطوري: غير محدود\n\n"
        "<b>✨ مميزات خاصة:</b>\n"
        "• 🔧 استرجاع يومي مجاني (2 ساعة)\n"
        "• 📊 مراقبة الأداء المباشر\n"
        "• 🔄 إعادة تشغيل تلقائية\n"
        "• 📤 نسخ احتياطي للبوتات\n\n"
        f"💬 <b>الدعم:</b> {DEVELOPER_USERNAME}"
    )
    
    keyboard = [
        [InlineKeyboardButton("📚 دليل مفصل", callback_data="detailed_guide")],
        [InlineKeyboardButton("❓ الأسئلة الشائعة", callback_data="faq")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]
    ]
    
    if query:
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )

async def detailed_guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دليل مفصل"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "📚 <b>الدليل المفصل</b>\n"
        f"{'═' * 40}\n\n"
        "<b>🤖 إضافة بوت:</b>\n"
        "1. اضغط على 'إضافة بوت'\n"
        "2. أرسل ملف .py أو .zip\n"
        "3. سيتم اكتشاف التوكن تلقائياً\n"
        "4. إذا لم يتم الاكتشاف، أدخله يدوياً\n\n"
        "<b>📦 نشر ZIP:</b>\n"
        "• يجب أن يحتوي على main.py أو bot.py\n"
        "• أضف requirements.txt للمتطلبات\n"
        "• الحد الأقصى: 50MB\n\n"
        "<b>⏱️ إدارة الوقت:</b>\n"
        "• لكل خطة حد أقصى للوقت\n"
        "• عند انتهاء الوقت، يدخل البوت السكون\n"
        "• استخدم الاسترجاع اليومي لإيقاظه\n\n"
        "<b>🔄 إعادة التشغيل التلقائية:</b>\n"
        "• عند تعطل البوت، يعاد تشغيله تلقائياً\n"
        "• كل إعادة تشغيل تخصم 5 دقائق\n"
        "• الحد الأقصى: 5 محاولات\n\n"
        "<b>📁 إدارة الملفات:</b>\n"
        "• يمكنك رفع وتعديل وحذف الملفات\n"
        "• الملف الرئيسي لا يمكن حذفه\n"
        "• تحميل كـ ZIP متاح"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="help")]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الأسئلة الشائعة"""
    query = update.callback_query
    await query.answer()
    
    text = (
        "❓ <b>الأسئلة الشائعة</b>\n"
        f"{'═' * 40}\n\n"
        "<b>س: كيف أضيف بوت؟</b>\n"
        "ج: اضغط 'إضافة بوت' وأرسل ملف .py أو .zip\n\n"
        "<b>س: لماذا دخل بوتي السكون؟</b>\n"
        "ج: انتهى وقت الاستضافة. استخدم الاسترجاع اليومي.\n\n"
        "<b>س: كيف أحصل على وقت أكثر؟</b>\n"
        "ج: ترقية الخطة أو استخدام الاسترجاع اليومي.\n\n"
        "<b>س: ما هو الاسترجاع اليومي؟</b>\n"
        "ج: ساعتان مجانيتان يومياً لإيقاظ البوتات.\n\n"
        "<b>س: هل بياناتي آمنة؟</b>\n"
        "ج: نعم، نستخدم أحدث تقنيات الحماية.\n\n"
        "<b>س: كيف أتواصل مع الدعم؟</b>\n"
        f"ج: راسل {DEVELOPER_USERNAME}"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="help")]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """إحصائيات المستخدم"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    bots = db.get_user_bots(user_id)
    plan = db.get_user_plan(user_id, ADMIN_ID)
    plan_config = PLANS.get(plan, PLANS['free'])
    
    running = sum(1 for b in bots if b[2] == 'running')
    stopped = sum(1 for b in bots if b[2] == 'stopped')
    sleeping = sum(1 for b in bots if b[6])
    total_time = sum(b[4] for b in bots if b[4])
    total_used = sum(b[10] - b[4] for b in bots if b[10] and b[4])
    
    joined_date = user_data[9][:10] if user_data and len(user_data) > 9 and user_data[9] else "غير معروف"
    
    text = (
        f"📊 <b>إحصائياتي</b>\n"
        f"{'═' * 40}\n\n"
        f"👤 <b>معلومات الحساب:</b>\n"
        f"   • المعرّف: <code>{user_id}</code>\n"
        f"   • الخطة: {plan_config['emoji']} {plan_config['name']}\n"
        f"   • تاريخ الانضمام: {joined_date}\n\n"
        f"🤖 <b>البوتات:</b>\n"
        f"   • الإجمالي: {len(bots)}/{plan_config['max_bots']}\n"
        f"   • 🟢 نشطة: {running}\n"
        f"   • 🔴 متوقفة: {stopped}\n"
        f"   • 😴 سكون: {sleeping}\n\n"
        f"⏱️ <b>استخدام الوقت:</b>\n"
        f"   • المتبقي: {seconds_to_human(total_time)}\n"
        f"   • المستخدم: {seconds_to_human(total_used)}\n\n"
    )
    
    if db.can_user_recover(user_id):
        text += "✨ <b>الاسترجاع اليومي:</b> متاح ✓\n"
    else:
        text += "⏳ <b>الاسترجاع اليومي:</b> مستخدم (يتجدد غداً)\n"
    
    keyboard = [
        [InlineKeyboardButton("🔄 تحديث", callback_data="user_stats")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """إعدادات المستخدم"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    
    notifications_enabled = user_data[11] if user_data and len(user_data) > 11 else 1
    
    text = (
        f"⚙️ <b>الإعدادات</b>\n"
        f"{'═' * 40}\n\n"
        f"🔔 <b>الإشعارات:</b>\n"
        f"   الحالة: {'✅ مفعّلة' if notifications_enabled else '❌ معطّلة'}\n\n"
        f"🌐 <b>اللغة:</b> العربية 🇸🇦\n\n"
        f"📱 <b>الجهاز:</b> Telegram\n"
    )
    
    notif_text = "🔕 إيقاف الإشعارات" if notifications_enabled else "🔔 تفعيل الإشعارات"
    
    keyboard = [
        [InlineKeyboardButton(notif_text, callback_data="toggle_notifications")],
        [InlineKeyboardButton("🗑️ حذف حسابي", callback_data="delete_account_confirm")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def toggle_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """تبديل الإشعارات"""
    query = update.callback_query
    
    user_id = update.effective_user.id
    new_value = db.toggle_notifications(user_id)
    
    await query.answer(
        "✅ تم تفعيل الإشعارات" if new_value else "❌ تم إيقاف الإشعارات",
        show_alert=True
    )
    
    # إعادة عرض الإعدادات
    await settings(update, context, db)

async def delete_account_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """تأكيد حذف الحساب"""
    query = update.callback_query
    await query.answer()
    
    text = (
        f"⚠️ <b>تأكيد حذف الحساب</b>\n"
        f"{'═' * 40}\n\n"
        f"❗ <b>تحذير:</b>\n"
        f"• سيتم حذف جميع بوتاتك\n"
        f"• سيتم حذف جميع ملفاتك\n"
        f"• سيتم حذف جميع بياناتك\n"
        f"• <b>لا يمكن التراجع!</b>\n\n"
        f"هل أنت متأكد؟"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("✅ نعم، احذف", callback_data="delete_account_final"),
            InlineKeyboardButton("❌ إلغاء", callback_data="settings")
        ]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def delete_account_final(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database, pm):
    """حذف الحساب نهائياً"""
    query = update.callback_query
    await query.answer("⏳ جاري حذف الحساب...")
    
    user_id = update.effective_user.id
    
    # إيقاف جميع بوتات المستخدم
    bots = db.get_user_bots(user_id)
    for bot in bots:
        pm.stop_bot(bot[0])
    
    # حذف الحساب
    db.delete_user(user_id)
    
    await query.edit_message_text(
        "✅ <b>تم حذف حسابك بنجاح</b>\n\n"
        "شكراً لاستخدامك NeuroHost.\n"
        "يمكنك التسجيل مجدداً في أي وقت.",
        parse_mode="HTML"
    )
