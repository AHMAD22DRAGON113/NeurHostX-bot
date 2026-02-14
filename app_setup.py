# ============================================================================
# ملف الإدارة الرئيسي - NeuroHost V8 Enhanced
# ============================================================================

import os
import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

from telegram.ext import ApplicationBuilder
from config import (
    TOKEN, ADMIN_ID, DB_FILE, BOTS_DIR, LOG_DIR,
    ERROR_LOG_FILE, BACKUP_DIR, VERSION, VERSION_NAME,
    validate_credentials
)
from settings_manager import settings_manager

def setup_logging():
    """إعداد نظام التسجيل المحسن"""
    # إنشاء المجلدات الضرورية
    Path(LOG_DIR).mkdir(exist_ok=True)
    Path(BOTS_DIR).mkdir(exist_ok=True)
    Path(BACKUP_DIR).mkdir(exist_ok=True)
    
    # إعداد التسجيل الأساسي
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # إعداد تسجيل الأخطاء في ملف
    try:
        fh = RotatingFileHandler(
            ERROR_LOG_FILE,
            maxBytes=10*1024*1024,    # 10 MB
            backupCount=5,
            encoding="utf-8"
        )
        fh.setLevel(logging.ERROR)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        ))
        logging.getLogger().addHandler(fh)
    except Exception as e:
        logger.warning(f"فشل إعداد سجلات الملفات: {e}")
    
    # تقليل مستوى التسجيل للمكتبات الخارجية
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    
    return logger

def check_requirements():
    """التحقق من المتطلبات والإعدادات"""
    # التحقق من بيانات الاعتماد
    try:
        validate_credentials()
    except ValueError as e:
        print("\n" + "="*50)
        print(e)
        print("\n💡 تأكد من إعداد ملف .env بشكل صحيح")
        print("   TELEGRAM_BOT_TOKEN=your_token_here")
        print("   ADMIN_ID=your_telegram_id")
        print("="*50 + "\n")
        sys.exit(1)

    # التحقق من الإعدادات
    if not settings_manager.load_settings():
        print("⚠️ تحذير: لم يتم العثور على ملف الإعدادات settings.json")
        print("سيتم استخدام الإعدادات الافتراضية")

    # إنشاء المجلدات
    Path(BOTS_DIR).mkdir(exist_ok=True)
    Path(LOG_DIR).mkdir(exist_ok=True)
    Path(BACKUP_DIR).mkdir(exist_ok=True)

    # إنشاء مجلد مؤقت للتحميلات
    Path("temp").mkdir(exist_ok=True)
    Path("uploads").mkdir(exist_ok=True)

def create_app():
    """إنشاء تطبيق البوت"""
    try:
        app = ApplicationBuilder().token(TOKEN).build()
        return app
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"❌ فشل إنشاء التطبيق: {e}")
        print(f"❌ خطأ حرج: {e}")
        sys.exit(1)

def print_startup_banner():
    """طباعة بيان البداية المحسن"""
    banner = f"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ███╗   ██╗███████╗██╗   ██╗██████╗  ██████╗ ██╗  ██╗ ██████╗  ║
║   ████╗  ██║██╔════╝██║   ██║██╔══██╗██╔═══██╗██║  ██║██╔═══██╗ ║
║   ██╔██╗ ██║█████╗  ██║   ██║██████╔╝██║   ██║███████║██║   ██║ ║
║   ██║╚██╗██║██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══██║██║   ██║ ║
║   ██║ ╚████║███████╗╚██████╔╝██║  ██║╚██████╔╝██║  ██║╚██████╔╝ ║
║   ╚═╝  ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝  ║
║                                                                  ║
║   ═══════════════════════════════════════════════════════════   ║
║              🚀 NeuroHost V{VERSION} - {VERSION_NAME}             ║
║   ═══════════════════════════════════════════════════════════   ║
║                                                                  ║
║   📦 نظام استضافة بوتات تيليجرام المتكامل                        ║
║   👑 لوحة تحكم متقدمة للأدمن                                      ║
║   📁 مدير ملفات مدمج                                              ║
║   📊 مراقبة الأداء في الوقت الحقيقي                               ║
║   🔄 إعادة تشغيل تلقائية                                          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(banner)
