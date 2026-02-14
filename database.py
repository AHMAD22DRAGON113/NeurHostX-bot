# ============================================================================
# مدير قاعدة البيانات - NeuroHost V8 Enhanced
# ============================================================================

import sqlite3
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from config import DB_FILE, PLANS

logger = logging.getLogger(__name__)

class Database:
    """مدير قاعدة البيانات المحسن"""
    
    def __init__(self, db_file=DB_FILE):
        self.db_file = db_file
        self.init_db()
        self._migrate_db()

    def _get_connection(self):
        """الحصول على اتصال قاعدة البيانات"""
        conn = sqlite3.connect(self.db_file, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """تهيئة قاعدة البيانات"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        # جدول المستخدمين
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                role TEXT DEFAULT 'user',
                status TEXT DEFAULT 'pending',
                plan TEXT DEFAULT 'free',
                plan_start_date TIMESTAMP DEFAULT NULL,
                plan_end_date TIMESTAMP DEFAULT NULL,
                last_recovery_date DATE DEFAULT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_running_time INTEGER DEFAULT 0,
                notifications_enabled INTEGER DEFAULT 1,
                custom_plan_end_date DATE DEFAULT NULL,
                language TEXT DEFAULT 'ar',
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول البوتات
        c.execute('''
            CREATE TABLE IF NOT EXISTS bots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                token TEXT UNIQUE,
                name TEXT,
                status TEXT DEFAULT 'stopped',
                folder TEXT,
                main_file TEXT DEFAULT 'main.py',
                pid INTEGER DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                start_time TIMESTAMP DEFAULT NULL,
                total_seconds INTEGER DEFAULT 0,
                remaining_seconds INTEGER DEFAULT 0,
                power_max REAL DEFAULT 100.0,
                power_remaining REAL DEFAULT 100.0,
                last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sleep_mode INTEGER DEFAULT 0,
                auto_recovery_used INTEGER DEFAULT 0,
                restart_count INTEGER DEFAULT 0,
                last_restart_at TIMESTAMP DEFAULT NULL,
                last_sleep_reason TEXT DEFAULT NULL,
                warned_low INTEGER DEFAULT 0,
                cpu_usage REAL DEFAULT 0,
                mem_usage REAL DEFAULT 0,
                total_restarts INTEGER DEFAULT 0,
                last_error TEXT DEFAULT NULL,
                uptime_seconds INTEGER DEFAULT 0,
                started_at_timestamp INTEGER DEFAULT NULL,
                description TEXT DEFAULT '',
                auto_start INTEGER DEFAULT 0,
                priority INTEGER DEFAULT 1,
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        
        # جدول السجلات
        c.execute('''
            CREATE TABLE IF NOT EXISTS event_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_id INTEGER,
                event_type TEXT,
                message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(bot_id) REFERENCES bots(id)
            )
        ''')
        
        # جدول طلبات الترقية
        c.execute('''
            CREATE TABLE IF NOT EXISTS upgrade_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                current_plan TEXT,
                requested_plan TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TIMESTAMP DEFAULT NULL,
                reviewed_by INTEGER DEFAULT NULL,
                notes TEXT DEFAULT '',
                FOREIGN KEY(user_id) REFERENCES users(user_id)
            )
        ''')
        
        # جدول التعليقات
        c.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                text TEXT,
                rating INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول النسخ الاحتياطية
        c.execute('''
            CREATE TABLE IF NOT EXISTS backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_id INTEGER,
                file_path TEXT,
                size INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(bot_id) REFERENCES bots(id)
            )
        ''')
        
        # جدول إعدادات النظام
        c.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # إنشاء الفهارس
        c.execute('CREATE INDEX IF NOT EXISTS idx_bots_user ON bots(user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_bots_status ON bots(status)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_logs_bot ON event_logs(bot_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)')
        
        conn.commit()
        conn.close()

    def _migrate_db(self):
        """ترحيل قاعدة البيانات للإصدارات الجديدة"""
        try:
            conn = sqlite3.connect(self.db_file)
            c = conn.cursor()
            
            new_columns = [
                ('users', 'language', 'TEXT DEFAULT "ar"'),
                ('users', 'last_active', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'),
                ('bots', 'description', 'TEXT DEFAULT ""'),
                ('bots', 'auto_start', 'INTEGER DEFAULT 0'),
                ('bots', 'priority', 'INTEGER DEFAULT 1'),
            ]
            
            for table, column, definition in new_columns:
                try:
                    c.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')
                except sqlite3.OperationalError:
                    pass
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"خطأ في الترحيل: {e}")

    # ═══════════════════════════════════════════════════════════════════════
    # إدارة المستخدمين
    # ═══════════════════════════════════════════════════════════════════════

    def add_user(self, user_id, username, first_name="", admin_id=0):
        """إضافة مستخدم جديد"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        role = 'admin' if user_id == admin_id else 'user'
        status = 'approved' if user_id == admin_id else 'pending'
        try:
            c.execute(
                "INSERT OR IGNORE INTO users (user_id, username, first_name, role, status) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, first_name, role, status)
            )
            c.execute(
                "UPDATE users SET last_active = CURRENT_TIMESTAMP, username = ?, first_name = ? WHERE user_id = ?",
                (username, first_name, user_id)
            )
            conn.commit()
        except Exception as e:
            logger.error(f"خطأ في إضافة المستخدم: {e}")
        finally:
            conn.close()

    def get_user(self, user_id):
        """الحصول على بيانات المستخدم"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        return row

    def get_all_users(self):
        """الحصول على جميع المستخدمين"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("SELECT * FROM users ORDER BY joined_at DESC")
        rows = c.fetchall()
        conn.close()
        return rows

    def get_pending_users(self):
        """الحصول على المستخدمين المعلقين"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE status = 'pending' ORDER BY joined_at ASC")
        rows = c.fetchall()
        conn.close()
        return rows

    def get_blocked_users(self):
        """الحصول على المستخدمين المحظورين"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE status = 'blocked' ORDER BY joined_at DESC")
        rows = c.fetchall()
        conn.close()
        return rows

    def update_user_status(self, user_id, status):
        """تحديث حالة المستخدم"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("UPDATE users SET status = ? WHERE user_id = ?", (status, user_id))
        conn.commit()
        conn.close()

    def set_user_plan(self, user_id, plan, duration_days=None):
        """تعيين خطة المستخدم"""
        from helpers import get_current_time
        
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        start_date = get_current_time()
        end_date = None
        if duration_days:
            end_date = (datetime.now(timezone.utc) + timedelta(days=duration_days)).isoformat()
        c.execute(
            "UPDATE users SET plan = ?, plan_start_date = ?, plan_end_date = ? WHERE user_id = ?",
            (plan, start_date, end_date, user_id)
        )
        conn.commit()
        conn.close()

    def get_user_role(self, user_id, admin_id=0):
        """الحصول على دور المستخدم"""
        if user_id == admin_id:
            return 'admin'
        user = self.get_user(user_id)
        if user:
            return user[3]
        return 'user'

    def set_user_role(self, user_id, role):
        """تعيين دور المستخدم"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, user_id))
        conn.commit()
        conn.close()

    def toggle_notifications(self, user_id):
        """تبديل الإشعارات"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("SELECT notifications_enabled FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        new_value = 0 if result and result[0] else 1
        c.execute("UPDATE users SET notifications_enabled = ? WHERE user_id = ?", (new_value, user_id))
        conn.commit()
        conn.close()
        return new_value

    def delete_user(self, user_id):
        """حذف حساب المستخدم"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        # حذف بوتات المستخدم أولاً
        c.execute("SELECT id FROM bots WHERE user_id = ?", (user_id,))
        bots = c.fetchall()
        for bot in bots:
            c.execute("DELETE FROM event_logs WHERE bot_id = ?", (bot[0],))
            c.execute("DELETE FROM backups WHERE bot_id = ?", (bot[0],))
        c.execute("DELETE FROM bots WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM upgrade_requests WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM feedback WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

    # ═══════════════════════════════════════════════════════════════════════
    # إدارة البوتات
    # ═══════════════════════════════════════════════════════════════════════

    def add_bot(self, user_id, token, name, folder, main_file='main.py'):
        """إضافة بوت جديد"""
        plan = self.get_user_plan(user_id)
        plan_config = PLANS.get(plan, PLANS['free'])
        
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        try:
            c.execute('''
                INSERT INTO bots (
                    user_id, token, name, folder, main_file,
                    total_seconds, remaining_seconds,
                    power_max, power_remaining
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, token, name, folder, main_file,
                plan_config['time'], plan_config['time'],
                plan_config['power'], plan_config['power']
            ))
            bot_id = c.lastrowid
            conn.commit()
            conn.close()
            return bot_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
        except Exception as e:
            logger.error(f"خطأ في إضافة البوت: {e}")
            conn.close()
            return None

    def get_user_bots(self, user_id):
        """الحصول على بوتات المستخدم"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute(
            "SELECT id, name, status, pid, remaining_seconds, power_remaining, sleep_mode FROM bots WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        rows = c.fetchall()
        conn.close()
        return rows

    def count_user_bots(self, user_id):
        """عد بوتات المستخدم"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM bots WHERE user_id = ?", (user_id,))
        count = c.fetchone()[0]
        conn.close()
        return count

    def get_bot(self, bot_id):
        """الحصول على بيانات البوت"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("SELECT * FROM bots WHERE id = ?", (bot_id,))
        row = c.fetchone()
        conn.close()
        return row

    def get_bot_by_token(self, token):
        """الحصول على البوت من خلال التوكن"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("SELECT * FROM bots WHERE token = ?", (token,))
        row = c.fetchone()
        conn.close()
        return row

    def get_all_bots(self):
        """الحصول على جميع البوتات"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("SELECT * FROM bots ORDER BY created_at DESC")
        rows = c.fetchall()
        conn.close()
        return rows

    def get_running_bots(self):
        """الحصول على البوتات العاملة"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("SELECT * FROM bots WHERE status = 'running' ORDER BY priority DESC")
        rows = c.fetchall()
        conn.close()
        return rows

    def update_bot_status(self, bot_id, status, pid=None):
        """تحديث حالة البوت"""
        from helpers import get_current_time
        
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        if pid is not None:
            c.execute(
                "UPDATE bots SET status = ?, pid = ?, last_checked = ? WHERE id = ?",
                (status, pid, get_current_time(), bot_id)
            )
        else:
            c.execute(
                "UPDATE bots SET status = ?, pid = NULL, last_checked = ? WHERE id = ?",
                (status, get_current_time(), bot_id)
            )
        conn.commit()
        conn.close()

    def update_bot_resources(self, bot_id, **kwargs):
        """تحديث موارد البوت"""
        from helpers import get_current_time
        
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        updates = []
        values = []
        
        for key, value in kwargs.items():
            if value is not None:
                updates.append(f"{key} = ?")
                values.append(value)
        
        if updates:
            values.append(get_current_time())
            updates.append("last_checked = ?")
            values.append(bot_id)
            query = f"UPDATE bots SET {', '.join(updates)} WHERE id = ?"
            c.execute(query, values)
            conn.commit()
        
        conn.close()

    def update_bot_name(self, bot_id, name):
        """تحديث اسم البوت"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("UPDATE bots SET name = ? WHERE id = ?", (name, bot_id))
        conn.commit()
        conn.close()

    def delete_bot(self, bot_id):
        """حذف البوت"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("DELETE FROM bots WHERE id = ?", (bot_id,))
        c.execute("DELETE FROM event_logs WHERE bot_id = ?", (bot_id,))
        c.execute("DELETE FROM backups WHERE bot_id = ?", (bot_id,))
        conn.commit()
        conn.close()

    def set_sleep_mode(self, bot_id, sleep_mode, reason=None):
        """تعيين وضع السكون"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute(
            "UPDATE bots SET sleep_mode = ?, last_sleep_reason = ? WHERE id = ?",
            (1 if sleep_mode else 0, reason, bot_id)
        )
        conn.commit()
        conn.close()

    # ═══════════════════════════════════════════════════════════════════════
    # سجلات الأحداث
    # ═══════════════════════════════════════════════════════════════════════

    def add_event_log(self, bot_id, event_type, message):
        """إضافة سجل حدث"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute(
            "INSERT INTO event_logs (bot_id, event_type, message) VALUES (?, ?, ?)",
            (bot_id, event_type, message[:1000])
        )
        conn.commit()
        conn.close()

    def get_bot_logs(self, bot_id, limit=50):
        """الحصول على سجلات البوت"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute(
            "SELECT event_type, message, timestamp FROM event_logs WHERE bot_id = ? ORDER BY timestamp DESC LIMIT ?",
            (bot_id, limit)
        )
        rows = c.fetchall()
        conn.close()
        return rows

    def clear_bot_logs(self, bot_id):
        """مسح سجلات البوت"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("DELETE FROM event_logs WHERE bot_id = ?", (bot_id,))
        conn.commit()
        conn.close()

    # ═══════════════════════════════════════════════════════════════════════
    # نظام الخطط
    # ═══════════════════════════════════════════════════════════════════════

    def get_user_plan(self, user_id, admin_id=0):
        """الحصول على خطة المستخدم"""
        if user_id == admin_id:
            return 'supreme'
        
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("SELECT plan, plan_end_date FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        conn.close()
        
        if not result:
            return 'free'
        
        plan, end_date = result
        
        if plan == 'supreme':
            return 'supreme'
        
        if end_date:
            try:
                exp_date = datetime.fromisoformat(end_date)
                if datetime.now(timezone.utc) > exp_date:
                    return 'free'
            except (ValueError, TypeError) as e:
                logger.warning(f"⚠️ خطأ في تحليل تاريخ انتهاء الخطة: {e}")
        
        return plan if plan else 'free'

    def can_user_recover(self, user_id):
        """التحقق من إمكانية الاسترجاع اليومي"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("SELECT last_recovery_date FROM users WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        conn.close()
        
        if not result or not result[0]:
            return True
        
        try:
            last_recovery = datetime.fromisoformat(result[0]).date()
            today = datetime.now(timezone.utc).date()
            return last_recovery < today
        except:
            return True

    def use_user_recovery(self, user_id):
        """استخدام الاسترجاع اليومي"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        today = datetime.now(timezone.utc).date().isoformat()
        c.execute("UPDATE users SET last_recovery_date = ? WHERE user_id = ?", (today, user_id))
        conn.commit()
        conn.close()

    # ═══════════════════════════════════════════════════════════════════════
    # طلبات الترقية
    # ═══════════════════════════════════════════════════════════════════════

    def add_upgrade_request(self, user_id, current_plan, requested_plan):
        """إضافة طلب ترقية"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute(
            "INSERT INTO upgrade_requests (user_id, current_plan, requested_plan) VALUES (?, ?, ?)",
            (user_id, current_plan, requested_plan)
        )
        request_id = c.lastrowid
        conn.commit()
        conn.close()
        return request_id

    def get_pending_upgrades(self):
        """الحصول على طلبات الترقية المعلقة"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("""
            SELECT ur.*, u.username, u.first_name 
            FROM upgrade_requests ur 
            JOIN users u ON ur.user_id = u.user_id 
            WHERE ur.status = 'pending' 
            ORDER BY ur.created_at ASC
        """)
        rows = c.fetchall()
        conn.close()
        return rows

    def get_upgrade_request(self, request_id):
        """الحصول على طلب ترقية محدد"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("SELECT * FROM upgrade_requests WHERE id = ?", (request_id,))
        row = c.fetchone()
        conn.close()
        return row

    def approve_upgrade(self, request_id):
        """الموافقة على طلب الترقية"""
        from helpers import get_current_time
        
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        # جلب بيانات الطلب
        c.execute("SELECT user_id, requested_plan FROM upgrade_requests WHERE id = ?", (request_id,))
        result = c.fetchone()
        
        if result:
            user_id, new_plan = result
            # تحديث خطة المستخدم
            c.execute("UPDATE users SET plan = ? WHERE user_id = ?", (new_plan, user_id))
            # تحديث حالة الطلب
            c.execute(
                "UPDATE upgrade_requests SET status = 'approved', reviewed_at = ? WHERE id = ?",
                (get_current_time(), request_id)
            )
        
        conn.commit()
        conn.close()

    def reject_upgrade(self, request_id):
        """رفض طلب الترقية"""
        from helpers import get_current_time
        
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute(
            "UPDATE upgrade_requests SET status = 'rejected', reviewed_at = ? WHERE id = ?",
            (get_current_time(), request_id)
        )
        conn.commit()
        conn.close()

    def get_user_upgrade_history(self, user_id):
        """الحصول على سجل ترقيات المستخدم"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute(
            "SELECT * FROM upgrade_requests WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        rows = c.fetchall()
        conn.close()
        return rows

    # ═══════════════════════════════════════════════════════════════════════
    # النسخ الاحتياطية
    # ═══════════════════════════════════════════════════════════════════════

    def add_backup(self, bot_id, file_path, size):
        """إضافة سجل نسخة احتياطية"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute(
            "INSERT INTO backups (bot_id, file_path, size) VALUES (?, ?, ?)",
            (bot_id, file_path, size)
        )
        conn.commit()
        conn.close()

    def get_bot_backups(self, bot_id):
        """الحصول على النسخ الاحتياطية للبوت"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute(
            "SELECT * FROM backups WHERE bot_id = ? ORDER BY created_at DESC",
            (bot_id,)
        )
        rows = c.fetchall()
        conn.close()
        return rows

    # ═══════════════════════════════════════════════════════════════════════
    # إعدادات النظام
    # ═══════════════════════════════════════════════════════════════════════

    def get_setting(self, key, default=None):
        """الحصول على إعداد"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute("SELECT value FROM system_settings WHERE key = ?", (key,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else default

    def set_setting(self, key, value):
        """تعيين إعداد"""
        from helpers import get_current_time
        
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO system_settings (key, value, updated_at) VALUES (?, ?, ?)",
            (key, value, get_current_time())
        )
        conn.commit()
        conn.close()

    # ═══════════════════════════════════════════════════════════════════════
    # إحصائيات
    # ═══════════════════════════════════════════════════════════════════════

    def get_system_stats(self):
        """الحصول على إحصائيات النظام"""
        conn = sqlite3.connect(self.db_file)
        c = conn.cursor()
        
        stats = {}
        
        # عدد المستخدمين
        c.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM users WHERE status = 'approved'")
        stats['approved_users'] = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM users WHERE status = 'pending'")
        stats['pending_users'] = c.fetchone()[0]
        
        # عدد البوتات
        c.execute("SELECT COUNT(*) FROM bots")
        stats['total_bots'] = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM bots WHERE status = 'running'")
        stats['running_bots'] = c.fetchone()[0]
        
        # توزيع الخطط
        for plan in PLANS.keys():
            c.execute("SELECT COUNT(*) FROM users WHERE plan = ?", (plan,))
            stats[f'plan_{plan}'] = c.fetchone()[0]
        
        # طلبات الترقية المعلقة
        c.execute("SELECT COUNT(*) FROM upgrade_requests WHERE status = 'pending'")
        stats['pending_upgrades'] = c.fetchone()[0]
        
        conn.close()
        return stats
