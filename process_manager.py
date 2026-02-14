# ============================================================================
# مدير العمليات - NeuroHost V8 Enhanced
# ============================================================================

import os
import sys
import time
import signal
import asyncio
import logging
from pathlib import Path
from config import (
    BOTS_DIR, RESTART_COOLDOWN, RESTART_TIME_COST, 
    MAX_RESTARTS, MONITOR_CHECK_INTERVAL, WARNING_COOLDOWN
)
from helpers import seconds_to_human, get_current_time, safe_html_escape

try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)

class ProcessManager:
    """مدير العمليات المحسن"""
    
    def __init__(self, db):
        self.db = db
        self.processes = {}
        self.monitor_tasks = {}
        self.restart_cooldown = RESTART_COOLDOWN
        self.restart_time_cost = RESTART_TIME_COST
        self.max_restarts = MAX_RESTARTS

    async def start_bot(self, bot_id, application):
        """بدء البوت مع معالجة أخطاء محسّنة"""
        bot = self.db.get_bot(bot_id)
        if not bot:
            return False, "❌ البوت غير موجود"
        
        # استخراج البيانات من الـ tuple
        user_id = bot[1]
        token = bot[2]
        name = bot[3]
        status = bot[4]
        folder = bot[5]
        main_file = bot[6]
        pid = bot[7]
        total_seconds = bot[10]
        remaining_seconds = bot[11]
        sleep_mode = bot[15]
        
        # التحقق من الحالات
        if sleep_mode:
            self.db.add_event_log(bot_id, "WARNING", "⚠️ البوت في وضع السكون")
            return False, "⚠️ البوت في وضع السكون. استخدم الاسترجاع اليومي لإيقاظه."
        
        if remaining_seconds <= 0:
            self.db.add_event_log(bot_id, "WARNING", "⚠️ انتهت فترة الاستضافة")
            return False, "⚠️ انتهت فترة الاستضافة. أضف وقتاً جديداً."
        
        # التحقق من مسار البوت
        bot_path = Path(BOTS_DIR) / folder
        if not bot_path.exists():
            self.db.add_event_log(bot_id, "ERROR", "❌ مجلد البوت غير موجود")
            return False, "❌ مجلد البوت غير موجود"
        
        main_file_path = bot_path / main_file
        if not main_file_path.exists():
            self.db.add_event_log(bot_id, "ERROR", f"❌ الملف {main_file} غير موجود")
            return False, f"❌ الملف الرئيسي ({main_file}) غير موجود"
        
        # قتل العملية القديمة إذا كانت موجودة
        if pid:
            try:
                if os.name != 'nt':
                    os.killpg(os.getpgid(pid), signal.SIGKILL)
                else:
                    os.kill(pid, signal.SIGKILL)
                logger.info(f"تم قتل العملية القديمة: {pid}")
            except Exception as e:
                logger.warning(f"فشل قتل العملية القديمة: {e}")
        
        # تثبيت المتطلبات إذا وجدت
        req_file = bot_path / "requirements.txt"
        if req_file.exists():
            try:
                logger.info(f"🔧 جاري تثبيت متطلبات البوت {bot_id}...")
                process = await asyncio.create_subprocess_exec(
                    sys.executable, "-m", "pip", "install", "-q", "-r", str(req_file),
                    cwd=str(bot_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await asyncio.wait_for(process.wait(), timeout=120)
                self.db.add_event_log(bot_id, "INFO", "✅ تم تثبيت المتطلبات بنجاح")
                logger.info(f"✅ تم تثبيت المتطلبات للبوت {bot_id}")
            except asyncio.TimeoutError:
                logger.warning(f"انتهت مهلة تثبيت المتطلبات: {bot_id}")
                self.db.add_event_log(bot_id, "WARNING", "⚠️ انتهت مهلة تثبيت المتطلبات")
            except Exception as e:
                logger.warning(f"فشل تثبيت المتطلبات: {e}")
                self.db.add_event_log(bot_id, "WARNING", f"⚠️ فشل تثبيت المتطلبات")
        
        # إنشاء مجلد السجلات
        logs_dir = bot_path / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # تحضير البيئة
        env = os.environ.copy()
        if token:
            env["BOT_TOKEN"] = token
        
        # بدء البوت
        try:
            stdout_file = open(logs_dir / "stdout.log", "a", encoding="utf-8")
            stderr_file = open(logs_dir / "stderr.log", "a", encoding="utf-8")
            
            process = await asyncio.create_subprocess_exec(
                sys.executable, main_file,
                cwd=str(bot_path),
                env=env,
                stdout=stdout_file,
                stderr=stderr_file,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            self.processes[bot_id] = {
                'process': process,
                'stdout': stdout_file,
                'stderr': stderr_file,
                'started_at': time.time()
            }
            
            # تحديث قاعدة البيانات
            now_timestamp = int(time.time())
            self.db.update_bot_status(bot_id, "running", process.pid)
            self.db.update_bot_resources(
                bot_id,
                start_time=get_current_time(),
                restart_count=0,
                started_at_timestamp=now_timestamp,
                uptime_seconds=0
            )
            
            # بدء المراقبة
            if bot_id in self.monitor_tasks:
                self.monitor_tasks[bot_id].cancel()
            
            self.monitor_tasks[bot_id] = application.create_task(
                self._monitor_bot(bot_id, user_id, application)
            )
            
            self.db.add_event_log(bot_id, "INFO", "✅ تم بدء البوت بنجاح")
            logger.info(f"✅ تم بدء البوت {bot_id} بنجاح مع PID {process.pid}")
            return True, f"✅ تم بدء البوت بنجاح\n🆔 PID: {process.pid}"
            
        except Exception as e:
            logger.exception(f"فشل بدء البوت {bot_id}: {e}")
            self.db.add_event_log(bot_id, "CRITICAL", f"❌ فشل البدء: {str(e)[:80]}")
            return False, f"❌ فشل بدء البوت: {str(e)[:50]}"

    def stop_bot(self, bot_id):
        """إيقاف البوت"""
        if bot_id in self.processes:
            proc_data = self.processes[bot_id]
            process = proc_data['process']
            
            try:
                if os.name != 'nt':
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    process.terminate()
                
                # إغلاق ملفات السجل
                try:
                    proc_data['stdout'].close()
                    proc_data['stderr'].close()
                except:
                    pass
                
            except Exception as e:
                logger.warning(f"خطأ في إيقاف البوت {bot_id}: {e}")
            
            del self.processes[bot_id]
        
        # إلغاء مهمة المراقبة
        if bot_id in self.monitor_tasks:
            self.monitor_tasks[bot_id].cancel()
            del self.monitor_tasks[bot_id]
        
        # تحديث قاعدة البيانات
        self.db.update_bot_status(bot_id, "stopped", None)
        self.db.add_event_log(bot_id, "INFO", "⏹ تم إيقاف البوت")
        return True

    async def restart_bot(self, bot_id, application):
        """إعادة تشغيل البوت"""
        self.stop_bot(bot_id)
        await asyncio.sleep(2)
        return await self.start_bot(bot_id, application)

    async def _monitor_bot(self, bot_id, user_id, application):
        """مراقبة البوت بشكل مستمر"""
        last_warning_time = 0
        
        while bot_id in self.processes:
            try:
                await asyncio.sleep(MONITOR_CHECK_INTERVAL)
                
                bot = self.db.get_bot(bot_id)
                if not bot:
                    break
                
                proc_data = self.processes.get(bot_id)
                if not proc_data:
                    break
                
                process = proc_data['process']
                
                # التحقق من توقف العملية
                if process.returncode is not None:
                    self.db.add_event_log(
                        bot_id,
                        "WARNING",
                        f"⚠️ توقف البوت برمز: {process.returncode}"
                    )
                    await self._handle_unexpected_stop(bot_id, user_id, application)
                    break
                
                # الحصول على استخدام الموارد
                cpu, mem = self.get_bot_usage(bot_id)
                
                # حساب وقت التشغيل الدقيق
                started_at = bot[26]  # started_at_timestamp
                if started_at:
                    now_timestamp = int(time.time())
                    actual_uptime = now_timestamp - started_at
                else:
                    actual_uptime = 0
                
                # حساب الوقت المتبقي
                initial_time = bot[10]  # total_seconds
                remaining = max(0, initial_time - actual_uptime)
                
                self.db.update_bot_resources(
                    bot_id,
                    remaining_seconds=remaining,
                    cpu_usage=cpu,
                    mem_usage=mem,
                    uptime_seconds=actual_uptime
                )
                
                # تحذير الوقت المنخفض
                current_time = time.time()
                if remaining > 0 and remaining <= 600 and (current_time - last_warning_time) > WARNING_COOLDOWN:
                    try:
                        await application.bot.send_message(
                            chat_id=user_id,
                            text=(
                                f"⚠️ <b>تحذير الوقت</b>\n"
                                f"{'─' * 30}\n\n"
                                f"🤖 البوت: <code>{safe_html_escape(bot[3])}</code>\n"
                                f"⏰ الوقت المتبقي: <b>{seconds_to_human(remaining)}</b>\n\n"
                                f"💡 أضف وقتاً إضافياً لتجنب دخول وضع السكون"
                            ),
                            parse_mode="HTML"
                        )
                        last_warning_time = current_time
                    except Exception as e:
                        logger.warning(f"فشل إرسال التحذير: {e}")
                
                # وضع السكون عند انتهاء الوقت
                if remaining <= 0:
                    self.db.set_sleep_mode(bot_id, True, "انتهت فترة الاستضافة")
                    self.stop_bot(bot_id)
                    self.db.add_event_log(bot_id, "INFO", "😴 دخل وضع السكون")
                    
                    try:
                        await application.bot.send_message(
                            chat_id=user_id,
                            text=(
                                f"😴 <b>وضع السكون</b>\n"
                                f"{'─' * 30}\n\n"
                                f"🤖 البوت: <code>{safe_html_escape(bot[3])}</code>\n\n"
                                f"انتهى وقت الاستضافة ودخل البوت وضع السكون.\n\n"
                                f"✨ استخدم <b>الاسترجاع اليومي</b> للحصول على ساعتين مجاناً!"
                            ),
                            parse_mode="HTML"
                        )
                    except Exception:
                        pass
                    
                    break
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"خطأ في حلقة المراقبة للبوت {bot_id}: {e}")

    async def _handle_unexpected_stop(self, bot_id, user_id, application):
        """معالجة التوقف المفاجئ"""
        bot = self.db.get_bot(bot_id)
        if not bot:
            return
        
        restart_count = bot[17]  # restart_count
        
        # إذا تجاوز الحد الأقصى لإعادة التشغيل
        if restart_count >= self.max_restarts:
            self.db.set_sleep_mode(bot_id, True, "تجاوز عدد إعادة التشغيل")
            try:
                await application.bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"⚠️ <b>توقف البوت نهائياً</b>\n"
                        f"{'─' * 30}\n\n"
                        f"🤖 البوت: <code>{safe_html_escape(bot[3])}</code>\n\n"
                        f"توقف البوت بشكل متكرر وتم إدخاله في وضع السكون.\n"
                        f"تحقق من الأخطاء في السجلات."
                    ),
                    parse_mode="HTML"
                )
            except Exception:
                pass
            self.db.add_event_log(bot_id, "CRITICAL", "❌ توقف نهائي - تجاوز حد إعادة التشغيل")
            return
        
        # خصم وقت من إعادة التشغيل
        new_time = max(0, bot[11] - self.restart_time_cost)
        
        self.db.update_bot_resources(
            bot_id,
            remaining_seconds=new_time,
            restart_count=restart_count + 1,
            last_restart_at=get_current_time()
        )
        
        # انتظار قبل إعادة التشغيل
        await asyncio.sleep(5)
        
        # إعادة التشغيل التلقائي
        success, msg = await self.start_bot(bot_id, application)
        
        if success:
            try:
                await application.bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"♻️ <b>إعادة تشغيل تلقائية</b>\n"
                        f"{'─' * 30}\n\n"
                        f"🤖 البوت: <code>{safe_html_escape(bot[3])}</code>\n\n"
                        f"تم اكتشاف توقف غير متوقع وإعادة تشغيل البوت تلقائياً.\n"
                        f"📊 عدد إعادات التشغيل: {restart_count + 1}/{self.max_restarts}"
                    ),
                    parse_mode="HTML"
                )
            except Exception:
                pass
            self.db.add_event_log(bot_id, "INFO", f"✅ إعادة تشغيل تلقائية #{restart_count + 1}")
        else:
            self.db.add_event_log(bot_id, "ERROR", f"❌ فشل إعادة التشغيل التلقائية: {msg}")

    def get_bot_usage(self, bot_id):
        """الحصول على استخدام الموارد"""
        if not psutil:
            return 0.0, 0.0
        
        proc_data = self.processes.get(bot_id)
        if not proc_data:
            return 0.0, 0.0
        
        try:
            process = psutil.Process(proc_data['process'].pid)
            cpu = process.cpu_percent(interval=0.1)
            mem = process.memory_info().rss / (1024 * 1024)
            return cpu, mem
        except:
            return 0.0, 0.0

    def is_bot_running(self, bot_id):
        """التحقق من حالة تشغيل البوت"""
        if bot_id not in self.processes:
            return False
        
        proc_data = self.processes.get(bot_id)
        if not proc_data:
            return False
        
        return proc_data['process'].returncode is None

    def get_all_running_bots(self):
        """الحصول على قائمة البوتات العاملة"""
        return list(self.processes.keys())

    async def stop_all_bots(self):
        """إيقاف جميع البوتات"""
        bot_ids = list(self.processes.keys())
        for bot_id in bot_ids:
            self.stop_bot(bot_id)
        logger.info(f"تم إيقاف {len(bot_ids)} بوت")
