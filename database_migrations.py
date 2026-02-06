# ============================================================================
# تحديث قاعدة البيانات - جداول الدفع والفواتير
# ============================================================================
"""
تحديثات قاعدة البيانات لدعم نظام الدفع بنجوم تيليجرام
"""

import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseMigration:
    """فئة معالجة الترقيات والتحديثات"""

    @staticmethod
    def add_payment_tables(db_file: str) -> bool:
        """إضافة جداول الدفع والفواتير

        Args:
            db_file: مسار ملف قاعدة البيانات

        Returns:
            نجح؟
        """
        try:
            conn = sqlite3.connect(db_file)
            c = conn.cursor()

            # جدول الفواتير
            c.execute('''
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    plan TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    currency TEXT DEFAULT 'XTR',
                    status TEXT DEFAULT 'pending',
                    payload TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    transaction_id TEXT UNIQUE,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')

            # جدول المعاملات (Transactions)
            c.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    invoice_id INTEGER,
                    plan TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    status TEXT DEFAULT 'pending',
                    payment_method TEXT DEFAULT 'telegram_stars',
                    telegram_charge_id TEXT UNIQUE,
                    telegram_payment_id TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id)
                )
            ''')

            # جدول سجل الأسعار (للإحصائيات)
            c.execute('''
                CREATE TABLE IF NOT EXISTS revenue_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    count INTEGER DEFAULT 1,
                    date DATE DEFAULT CURRENT_DATE,
                    total_revenue INTEGER,
                    UNIQUE(plan, date)
                )
            ''')

            # جدول قسائم الخصم (Coupons)
            c.execute('''
                CREATE TABLE IF NOT EXISTS coupons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    discount_percent REAL NOT NULL,
                    discount_amount INTEGER,
                    max_uses INTEGER,
                    uses_count INTEGER DEFAULT 0,
                    valid_from DATE NOT NULL,
                    valid_until DATE NOT NULL,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER
                )
            ''')

            # جدول استخدام القسائم
            c.execute('''
                CREATE TABLE IF NOT EXISTS coupon_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    coupon_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (coupon_id) REFERENCES coupons(id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')

            conn.commit()
            conn.close()

            logger.info("✅ تم إضافة جداول الدفع بنجاح")
            return True

        except sqlite3.OperationalError as e:
            if "already exists" in str(e):
                logger.info("ℹ️ جداول الدفع موجودة بالفعل")
                return True
            logger.error(f"❌ خطأ في إضافة جداول الدفع: {e}")
            return False

    @staticmethod
    def add_security_columns(db_file: str) -> bool:
        """إضافة أعمدة الأمان

        Args:
            db_file: مسار ملف قاعدة البيانات

        Returns:
            نجح؟
        """
        try:
            conn = sqlite3.connect(db_file)
            c = conn.cursor()

            # إضافة أعمدة أمان للبوتات
            columns_to_add = {
                'bots': [
                    ('security_hash TEXT', 'security_hash'),
                    ('last_security_check TIMESTAMP', 'last_security_check'),
                    ('security_warnings TEXT', 'security_warnings'),
                    ('is_verified INTEGER DEFAULT 0', 'is_verified'),
                ]
            }

            for table, columns in columns_to_add.items():
                for col_def, col_name in columns:
                    try:
                        c.execute(f'ALTER TABLE {table} ADD COLUMN {col_def}')
                        logger.info(f"✅ تم إضافة العمود {col_name} إلى {table}")
                    except sqlite3.OperationalError:
                        pass  # العمود موجود بالفعل

            conn.commit()
            conn.close()

            logger.info("✅ تم إضافة أعمدة الأمان")
            return True

        except Exception as e:
            logger.error(f"❌ خطأ في إضافة أعمدة الأمان: {e}")
            return False

    @staticmethod
    def create_indexes(db_file: str) -> bool:
        """إنشاء فهارس لتحسين الأداء"""
        try:
            conn = sqlite3.connect(db_file)
            c = conn.cursor()

            indexes = [
                'CREATE INDEX IF NOT EXISTS idx_invoices_user ON invoices(user_id)',
                'CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status)',
                'CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id)',
                'CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status)',
                'CREATE INDEX IF NOT EXISTS idx_coupons_code ON coupons(code)',
                'CREATE INDEX IF NOT EXISTS idx_revenue_date ON revenue_logs(date)',
            ]

            for index_sql in indexes:
                c.execute(index_sql)

            conn.commit()
            conn.close()

            logger.info("✅ تم إنشاء الفهارس")
            return True

        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء الفهارس: {e}")
            return False


# توسيعات لفئة Database
def add_payment_methods_to_database():
    """إضافة دوال الدفع إلى فئة Database"""

    def add_invoice(self, user_id: int, plan: str, amount: int, payload: str) -> bool:
        """إضافة فاتورة جديدة"""
        try:
            conn = self._get_connection()
            c = conn.cursor()

            c.execute('''
                INSERT INTO invoices (user_id, plan, amount, currency, payload)
                VALUES (?, ?, ?, 'XTR', ?)
            ''', (user_id, plan, amount, payload))

            conn.commit()
            conn.close()

            logger.info(f"✅ تم إضافة فاتورة: المستخدم {user_id}, الخطة {plan}")
            return True

        except Exception as e:
            logger.error(f"❌ خطأ في إضافة الفاتورة: {e}")
            return False

    def get_invoices(self, user_id: int, limit: int = 10) -> list:
        """الحصول على الفواتير"""
        try:
            conn = self._get_connection()
            c = conn.cursor()

            c.execute('''
                SELECT * FROM invoices
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))

            return c.fetchall()

        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على الفواتير: {e}")
            return []

    def add_transaction(self, user_id: int, plan: str, amount: int,
                       status: str = 'pending', invoice_id: int = None) -> int:
        """إضافة معاملة جديدة"""
        try:
            conn = self._get_connection()
            c = conn.cursor()

            c.execute('''
                INSERT INTO transactions (user_id, invoice_id, plan, amount, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, invoice_id, plan, amount, status))

            transaction_id = c.lastrowid
            conn.commit()
            conn.close()

            return transaction_id

        except Exception as e:
            logger.error(f"❌ خطأ في إضافة المعاملة: {e}")
            return 0

    def update_transaction_status(self, transaction_id: int, status: str,
                                 charge_id: str = None) -> bool:
        """تحديث حالة المعاملة"""
        try:
            conn = self._get_connection()
            c = conn.cursor()

            c.execute('''
                UPDATE transactions
                SET status = ?, completed_at = CURRENT_TIMESTAMP, telegram_charge_id = ?
                WHERE id = ?
            ''', (status, charge_id, transaction_id))

            conn.commit()
            conn.close()

            logger.info(f"✅ تم تحديث المعاملة {transaction_id} إلى {status}")
            return True

        except Exception as e:
            logger.error(f"❌ خطأ في تحديث المعاملة: {e}")
            return False

    def get_revenue_stats(self, days: int = 30) -> dict:
        """الحصول على إحصائيات الإيرادات"""
        try:
            conn = self._get_connection()
            c = conn.cursor()

            c.execute('''
                SELECT
                    COUNT(*) as total_sales,
                    SUM(amount) as total_revenue,
                    AVG(amount) as avg_transaction
                FROM transactions
                WHERE status = 'completed'
                AND completed_at >= datetime('now', ? || ' days')
            ''', (f'-{days}',))

            result = c.fetchone()
            conn.close()

            return {
                'total_sales': result[0] or 0,
                'total_revenue': result[1] or 0,
                'avg_transaction': result[2] or 0,
            }

        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على إحصائيات الإيرادات: {e}")
            return {'total_sales': 0, 'total_revenue': 0, 'avg_transaction': 0}

    # إضافة الدوال إلى الفئة
    return {
        'add_invoice': add_invoice,
        'get_invoices': get_invoices,
        'add_transaction': add_transaction,
        'update_transaction_status': update_transaction_status,
        'get_revenue_stats': get_revenue_stats,
    }


# دالة تهيئة شاملة
def initialize_payment_system(db_file: str) -> bool:
    """تهيئة نظام الدفع بالكامل

    Args:
        db_file: مسار ملف قاعدة البيانات

    Returns:
        نجح؟
    """
    print("🔧 تهيئة نظام الدفع...")

    steps = [
        ("إضافة جداول الدفع", DatabaseMigration.add_payment_tables),
        ("إضافة أعمدة الأمان", DatabaseMigration.add_security_columns),
        ("إنشاء الفهارس", DatabaseMigration.create_indexes),
    ]

    for step_name, step_func in steps:
        print(f"  ⚙️ {step_name}...")
        if not step_func(db_file):
            print(f"  ❌ فشل {step_name}")
            return False
        print(f"  ✅ {step_name}")

    print("✅ تم تهيئة نظام الدفع بنجاح!")
    return True
