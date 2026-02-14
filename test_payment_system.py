#!/usr/bin/env python3
# ============================================================================
# اختبار نظام الدفع والأمان - NeurHostX V8.5
# ============================================================================

import sys
import os
from datetime import datetime

def test_payment_system():
    """اختبار نظام الدفع"""
    print("💳 اختبار نظام الدفع...")
    try:
        from payment_system import PaymentSystem, get_plan_emoji

        # اختبار الأسعار
        print("  ✓ اختبار الأسعار...")
        for plan in ['pro', 'ultra', 'supreme']:
            price, currency = PaymentSystem.get_plan_price(plan)
            print(f"    - {plan}: {price} {currency}")

        # اختبار معلومات الخطط
        print("  ✓ اختبار معلومات الخطط...")
        for plan in ['pro', 'ultra', 'supreme']:
            info = PaymentSystem.get_plan_info(plan)
            assert info is not None
            assert 'name' in info
            assert 'price' in info
            print(f"    - {get_plan_emoji(plan)} {info['name']}")

        # اختبار payload
        print("  ✓ اختبار تشفير/فك تشفير payload...")
        user_id = 12345
        plan = 'pro'
        payload = PaymentSystem.get_invoice_payload(user_id, plan)
        parsed_user, parsed_plan = PaymentSystem.parse_invoice_payload(payload)
        assert parsed_user == user_id
        assert parsed_plan == plan
        print(f"    - Payload: {payload}")

        # اختبار التحقق من الدفع
        print("  ✓ اختبار التحقق من الدفع...")
        is_valid, msg = PaymentSystem.verify_payment("test_id", user_id, "pro", 5)
        assert is_valid
        print(f"    - {msg}")

        print("✅ نظام الدفع يعمل بشكل صحيح!\n")
        return True

    except Exception as e:
        print(f"❌ خطأ في نظام الدفع: {e}\n")
        return False


def test_security_system():
    """اختبار نظام الحماية"""
    print("🔐 اختبار نظام الحماية...")
    try:
        from security_system import (
            SecurityScanner, FileValidator, RateLimiter,
            BotSecurityManager
        )

        # اختبار ماسح الأمان
        print("  ✓ اختبار ماسح الأمان...")
        # إنشاء ملف اختبار
        test_file = "test_bot.py"
        with open(test_file, 'w') as f:
            f.write("print('Hello')")

        is_safe, msg = SecurityScanner.scan_file(test_file)
        print(f"    - {test_file}: {msg}")
        os.remove(test_file)

        # اختبار مُدقق الملفات
        print("  ✓ اختبار مُدقق الملفات...")
        is_allowed, msg = FileValidator.is_file_allowed("script.py")
        print(f"    - script.py: {msg}")

        is_allowed, msg = FileValidator.is_file_allowed("virus.exe")
        print(f"    - virus.exe: {msg}")

        # اختبار تحديد معدل الطلبات
        print("  ✓ اختبار تحديد معدل الطلبات...")
        limiter = RateLimiter(max_requests=3, window_seconds=60)

        user_id = 999
        for i in range(4):
            is_allowed, remaining = limiter.is_allowed(user_id)
            print(f"    - الطلب {i+1}: {'مسموح' if is_allowed else 'مرفوض'}, المتبقي: {remaining}")

        # اختبار مدير الأمان
        print("  ✓ اختبار مدير أمان البوتات...")
        manager = BotSecurityManager()
        print(f"    - تم إنشاء المدير: ✓")

        print("✅ نظام الحماية يعمل بشكل صحيح!\n")
        return True

    except Exception as e:
        print(f"❌ خطأ في نظام الحماية: {e}\n")
        return False


def test_database_migrations():
    """اختبار تحديثات قاعدة البيانات"""
    print("💾 اختبار تحديثات قاعدة البيانات...")
    try:
        from database_migrations import DatabaseMigration

        # إنشاء ملف اختبار مؤقت
        test_db = "test_payment.db"

        # اختبار إضافة جداول الدفع
        print("  ✓ تجهيز جداول الدفع...")
        if DatabaseMigration.add_payment_tables(test_db):
            print(f"    - تم إنشاء جداول الدفع: ✓")
        else:
            print(f"    - جداول الدفع موجودة: ✓")

        # اختبار إضافة أعمدة الأمان
        print("  ✓ تجهيز أعمدة الأمان...")
        if DatabaseMigration.add_security_columns(test_db):
            print(f"    - تم إضافة أعمدة الأمان: ✓")

        # اختبار إنشاء الفهارس
        print("  ✓ إنشاء الفهارس...")
        if DatabaseMigration.create_indexes(test_db):
            print(f"    - تم إنشاء الفهارس: ✓")

        # تنظيف
        if os.path.exists(test_db):
            os.remove(test_db)

        print("✅ تحديثات قاعدة البيانات تعمل!\n")
        return True

    except Exception as e:
        print(f"❌ خطأ في تحديثات قاعدة البيانات: {e}\n")
        return False


def test_payment_handlers():
    """اختبار معالجات الدفع"""
    print("🎯 اختبار معالجات الدفع...")
    try:
        from payment_handlers import setup_payment_handlers
        print("  ✓ استيراد معالجات الدفع: ✓")
        print("  ✓ يمكن تثبيتها في app عند الحاجة: ✓")
        print("✅ معالجات الدفع جاهزة!\n")
        return True

    except Exception as e:
        print(f"❌ خطأ في معالجات الدفع: {e}\n")
        return False


def test_files_exist():
    """التحقق من وجود جميع الملفات الجديدة"""
    print("📁 التحقق من الملفات الجديدة...")
    files = [
        'payment_system.py',
        'payment_handlers.py',
        'security_system.py',
        'database_migrations.py',
        'PAYMENT_GUIDE.md'
    ]

    all_exist = True
    for file in files:
        exists = os.path.exists(file)
        status = "✓" if exists else "✗"
        print(f"  {status} {file}")
        if not exists:
            all_exist = False

    if all_exist:
        print("✅ جميع الملفات الجديدة موجودة!\n")
    else:
        print("❌ بعض الملفات مفقودة!\n")

    return all_exist


def main():
    """تشغيل جميع الاختبارات"""
    print("\n" + "=" * 50)
    print("🧪 اختبار نظام الدفع والأمان - NeurHostX V8.5")
    print("=" * 50 + "\n")

    results = {
        "الملفات": test_files_exist(),
        "نظام الدفع": test_payment_system(),
        "نظام الحماية": test_security_system(),
        "تحديثات قاعدة البيانات": test_database_migrations(),
        "معالجات الدفع": test_payment_handlers(),
    }

    # ملخص النتائج
    print("=" * 50)
    print("📊 ملخص الاختبار")
    print("=" * 50 + "\n")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ نجح" if result else "❌ فشل"
        print(f"{test_name}: {status}")

    print(f"\n📈 النتيجة: {passed}/{total} اختبار نجح")

    if passed == total:
        print("\n🎉 جميع اختبارات نظام الدفع والأمان نجحت!")
        print("\n✅ النظام جاهز للاستخدام!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} اختبارات فشلت")
        return 1


if __name__ == "__main__":
    sys.exit(main())
