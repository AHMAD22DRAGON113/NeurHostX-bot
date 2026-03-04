# ============================================================================
# تحسينات تجربة المستخدم - NeurHostX V9.2
# ============================================================================
"""
ميزات صغيرة تحسن تجربة المستخدم:
- أوامر سريعة (/ping, /status, /bots)
- إحصائيات سريعة
- health_check للأدمن
"""

import logging
import time as time_module
from datetime import datetime, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import ADMIN_ID, PLANS
from database import Database
from helpers import seconds_to_human, safe_html_escape, render_bar

logger = logging.getLogger(__name__)
DIVIDER = "════════════════════════════"
SUBDIV  = "─" * 28

# وقت بدء تشغيل البوت
_start_time = time_module.time()


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /ping - اختبار سرعة الاستجابة"""
    t0 = time_module.time()
    msg = await update.message.reply_text("🏓 جاري القياس...")
    elapsed = round((time_module.time() - t0) * 1000, 1)
    await msg.edit_text(
        f"{DIVIDER}\n🏓 <b>Pong!</b>\n{DIVIDER}\n\n"
        f"⚡ زمن الاستجابة: <b>{elapsed} ms</b>",
        parse_mode="HTML"
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """أمر /status - حالة سريعة"""
    user_id = update.effective_user.id
    plan = db.get_user_plan(user_id, ADMIN_ID)
    plan_config = PLANS.get(plan, PLANS['free'])

    bots = db.get_user_bots(user_id)
    running = sum(1 for b in bots if b[2] == 'running')

    uptime = int(time_module.time() - _start_time)

    await update.message.reply_text(
        f"{DIVIDER}\n📡 <b>حالة حسابك</b>\n{DIVIDER}\n\n"
        f"{plan_config['emoji']} الخطة: <b>{plan_config['name']}</b>\n"
        f"🤖 البوتات: <b>{running}/{len(bots)}</b> نشط\n"
        f"🕐 وقت تشغيل البوت: <b>{seconds_to_human(uptime)}</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 تفاصيل أكثر", callback_data="user_stats")],
            [InlineKeyboardButton("🏠 القائمة", callback_data="main_menu")]
        ])
    )


async def my_bots_command(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """أمر /bots - قائمة البوتات السريعة"""
    user_id = update.effective_user.id
    bots = db.get_user_bots(user_id)

    if not bots:
        await update.message.reply_text(
            f"{DIVIDER}\n🤖 <b>لا توجد بوتات</b>\n{DIVIDER}\n\n"
            f"ابدأ بإضافة بوتك الأول!",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ إضافة بوت", callback_data="add_bot")]
            ])
        )
        return

    text = f"{DIVIDER}\n🤖 <b>بوتاتي ({len(bots)})</b>\n{DIVIDER}\n\n"
    keyboard = []
    for bot in bots[:10]:
        icon = "🟢" if bot[2] == 'running' else ("😴" if bot[6] else "🔴")
        time_left = seconds_to_human(bot[4] or 0) if bot[4] else "⏳ انتهى"
        text += f"{icon} <b>{safe_html_escape(bot[1])}</b> — {time_left}\n"
        keyboard.append([InlineKeyboardButton(
            f"{icon} {bot[1][:20]}",
            callback_data=f"manage_{bot[0]}"
        )])

    keyboard.append([InlineKeyboardButton("🏠 القائمة", callback_data="main_menu")])

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def uptime_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض وقت تشغيل البوت - يعمل كأمر وكـ callback"""
    if update.callback_query:
        await update.callback_query.answer()
    elapsed = int(time_module.time() - _start_time)
    d, rem = divmod(elapsed, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)

    send_fn = update.callback_query.message.reply_text if update.callback_query else update.message.reply_text
    await send_fn(
        f"{DIVIDER}\n⏱️ <b>وقت التشغيل</b>\n{DIVIDER}\n\n"
        f"🕐 <b>{d}ي {h:02d}س {m:02d}د {s:02d}ث</b>\n\n"
        f"📅 يعمل منذ:\n"
        f"   {datetime.fromtimestamp(_start_time).strftime('%Y-%m-%d %H:%M')}",
        parse_mode="HTML"
    )


async def quick_restart_all(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """أمر /restartall - إعادة تشغيل جميع البوتات"""
    user_id = update.effective_user.id
    bots = db.get_user_bots(user_id)
    running_bots = [b for b in bots if b[2] == 'running']

    if not running_bots:
        await update.message.reply_text(
            f"{DIVIDER}\n⚠️ <b>لا توجد بوتات تعمل</b>\n{DIVIDER}",
            parse_mode="HTML"
        )
        return

    await update.message.reply_text(
        f"{DIVIDER}\n🔄 <b>إعادة تشغيل الكل</b>\n{DIVIDER}\n\n"
        f"سيتم إعادة تشغيل {len(running_bots)} بوت.\n\n"
        f"تأكيد؟",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ نعم، أعد الكل", callback_data="bulk_restart_all")],
            [InlineKeyboardButton("❌ إلغاء", callback_data="bulk_bot_operations")]
        ])
    )


async def health_check(update: Update, context: ContextTypes.DEFAULT_TYPE, db: Database):
    """فحص صحة النظام - يعمل كأمر وكـ callback"""
    if update.callback_query:
        await update.callback_query.answer()
    if update.effective_user.id != ADMIN_ID:
        await (update.callback_query.message.reply_text if update.callback_query else update.message.reply_text)("⛔ هذا الأمر للأدمن فقط")
        return

    import os
    import psutil

    try:
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # فحص قاعدة البيانات
        try:
            stats = db.get_system_stats()
            db_ok = True
        except Exception:
            db_ok = False

        # فحص مجلد البوتات
        from config import BOTS_DIRECTORY
        bots_dir_ok = os.path.exists(BOTS_DIRECTORY)

        cpu_bar = render_bar(cpu)
        mem_bar = render_bar(mem.percent)
        disk_bar = render_bar(disk.percent)

        await update.message.reply_text(
            f"{DIVIDER}\n🏥 <b>فحص صحة النظام</b>\n{DIVIDER}\n\n"
            f"💻 <b>الموارد:</b>\n"
            f"   CPU: {cpu_bar} {cpu:.1f}%\n"
            f"   RAM: {mem_bar} {mem.percent:.1f}%\n"
            f"   Disk: {disk_bar} {disk.percent:.1f}%\n\n"
            f"{SUBDIV}\n"
            f"✅ قاعدة البيانات: {'سليمة' if db_ok else '❌ خطأ'}\n"
            f"✅ مجلد البوتات: {'موجود' if bots_dir_ok else '❌ مفقود'}\n\n"
            f"📊 البوتات النشطة: <b>{stats.get('running_bots', 0)}</b>\n"
            f"👥 المستخدمون: <b>{stats.get('total_users', 0)}</b>",
            parse_mode="HTML"
        )
    except ImportError:
        await update.message.reply_text(
            f"{DIVIDER}\n🏥 <b>فحص صحة النظام</b>\n{DIVIDER}\n\n"
            f"⚠️ psutil غير مثبّت\n"
            f"ثبّته بـ: pip install psutil",
            parse_mode="HTML"
        )
