# ============================================================================
# نظام النسخ الاحتياطية - NeurHostX V9.0
# ============================================================================
"""
نظام نسخ احتياطي كامل يشمل:
- تحميل نسخة احتياطية (كل ملفات البوتات + قاعدة البيانات)
- رفع واستعادة نسخة
- تشفير بكلمة مرور
- نسخ احتياطي تلقائي يومي
"""

import io
import os
import zipfile
import logging
import asyncio
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class BackupSystem:
    """نظام النسخ الاحتياطية"""

    # ═══════════════════════════════════════════════════════════════════════
    # إنشاء نسخة احتياطية كاملة
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def create_full_backup(bots_dir: str, db_file: str, password: Optional[str] = None) -> io.BytesIO:
        """
        إنشاء نسخة احتياطية كاملة في الذاكرة

        Args:
            bots_dir: مجلد البوتات
            db_file: ملف قاعدة البيانات
            password: كلمة مرور التشفير (اختياري)

        Returns:
            BytesIO يحتوي على ملف ZIP
        """
        buf = io.BytesIO()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        zip_kwargs = {}
        if password:
            # ملاحظة: zipfile الأساسي لا يدعم AES - نستخدم pyzipper إذا متاح
            try:
                import pyzipper
                with pyzipper.AESZipFile(buf, 'w', compression=pyzipper.ZIP_DEFLATED,
                                          encryption=pyzipper.WZ_AES) as zf:
                    zf.setpassword(password.encode('utf-8'))
                    BackupSystem._add_files_to_zip(zf, bots_dir, db_file, timestamp)
                buf.seek(0)
                return buf
            except ImportError:
                logger.warning("pyzipper غير متاح - سيتم إنشاء نسخة بدون تشفير")

        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            BackupSystem._add_files_to_zip(zf, bots_dir, db_file, timestamp)

        buf.seek(0)
        return buf

    @staticmethod
    def _add_files_to_zip(zf, bots_dir: str, db_file: str, timestamp: str):
        """إضافة الملفات إلى ZIP"""
        # معلومات الـ backup
        meta = {
            "version": "9.0",
            "timestamp": timestamp,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "type": "full_backup"
        }
        zf.writestr("backup_meta.json", json.dumps(meta, ensure_ascii=False, indent=2))

        # إضافة قاعدة البيانات
        db_path = Path(db_file)
        if db_path.exists():
            zf.write(str(db_path), f"database/{db_path.name}")
            logger.info(f"✅ تمت إضافة قاعدة البيانات: {db_path.name}")

        # إضافة ملفات البوتات
        bots_path = Path(bots_dir)
        if bots_path.exists():
            file_count = 0
            for root, dirs, files in os.walk(bots_path):
                # تجاهل __pycache__ وملفات مؤقتة
                dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'venv', 'env', '.env']]
                for file in files:
                    if file.endswith(('.pyc', '.pyo', '.tmp')):
                        continue
                    file_path = Path(root) / file
                    arcname = str(file_path.relative_to(bots_path.parent))
                    try:
                        zf.write(str(file_path), arcname)
                        file_count += 1
                    except Exception as e:
                        logger.warning(f"تعذّر إضافة {file}: {e}")
            logger.info(f"✅ تمت إضافة {file_count} ملف بوت")
        else:
            logger.warning(f"⚠️ مجلد البوتات غير موجود: {bots_dir}")

    # ═══════════════════════════════════════════════════════════════════════
    # استعادة نسخة احتياطية
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def restore_backup(zip_content: bytes, bots_dir: str, db_file: str,
                        password: Optional[str] = None) -> tuple[bool, str]:
        """
        استعادة نسخة احتياطية

        Returns:
            (نجاح, رسالة)
        """
        try:
            buf = io.BytesIO(zip_content)

            # محاولة الفتح مع كلمة المرور إن وجدت
            if password:
                try:
                    import pyzipper
                    with pyzipper.AESZipFile(buf, 'r') as zf:
                        zf.setpassword(password.encode('utf-8'))
                        zf.extractall(path=".")
                    return True, "✅ تمت الاستعادة بنجاح"
                except ImportError:
                    pass

            with zipfile.ZipFile(buf, 'r') as zf:
                # التحقق من meta
                if 'backup_meta.json' in zf.namelist():
                    meta = json.loads(zf.read('backup_meta.json'))
                    logger.info(f"استعادة نسخة من: {meta.get('timestamp', 'غير معروف')}")

                # استخراج الملفات
                zf.extractall(path=".")

            return True, "✅ تمت الاستعادة بنجاح - أعد تشغيل البوت"

        except zipfile.BadZipFile:
            return False, "❌ ملف ZIP تالف أو غير صحيح"
        except RuntimeError as e:
            if "password" in str(e).lower():
                return False, "❌ كلمة المرور غير صحيحة"
            return False, f"❌ خطأ في الاستعادة: {str(e)[:100]}"
        except Exception as e:
            return False, f"❌ خطأ غير متوقع: {str(e)[:100]}"

    # ═══════════════════════════════════════════════════════════════════════
    # النسخ الاحتياطي التلقائي
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    async def send_auto_backup(bot, channel_id: str, bots_dir: str, db_file: str):
        """إرسال نسخة احتياطية تلقائية إلى القناة"""
        try:
            logger.info(f"🔄 بدء النسخ الاحتياطي التلقائي للقناة {channel_id}")
            buf = BackupSystem.create_full_backup(bots_dir, db_file)
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"

            buf.name = filename
            await bot.send_document(
                chat_id=channel_id,
                document=buf,
                caption=(
                    f"════════════════════════════\n"
                    f"💾 <b>نسخة احتياطية تلقائية</b>\n"
                    f"════════════════════════════\n\n"
                    f"⏰ التاريخ: {timestamp}\n"
                    f"🤖 NeurHostX V9.0\n\n"
                    f"✅ تم الحفظ التلقائي"
                ),
                parse_mode="HTML"
            )
            logger.info(f"✅ تم إرسال النسخة الاحتياطية إلى {channel_id}")
            return True
        except Exception as e:
            logger.error(f"❌ فشل النسخ الاحتياطي التلقائي: {e}")
            return False
