#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import asyncio
from pathlib import Path

def test_imports():
    print("🧪 اختبار الاستيرادات...")
    
    tests = []
    
    try:
        from config import TOKEN, ADMIN_ID, VERSION, PLANS
        tests.append(("✅ config.py", True))
    except Exception as e:
        tests.append((f"❌ config.py: {e}", False))
    
    try:
        from database import Database
        tests.append(("✅ database.py", True))
    except Exception as e:
        tests.append((f"❌ database.py: {e}", False))
    
    try:
        from process_manager import ProcessManager
        tests.append(("✅ process_manager.py", True))
    except Exception as e:
        tests.append((f"❌ process_manager.py: {e}", False))
    
    try:
        from helpers import seconds_to_human, extract_token_from_code, validate_token
        tests.append(("✅ helpers.py", True))
    except Exception as e:
        tests.append((f"❌ helpers.py: {e}", False))
    
    try:
        from payment_system import PaymentSystem
        tests.append(("✅ payment_system.py", True))
    except Exception as e:
        tests.append((f"❌ payment_system.py: {e}", False))
    
    try:
        from formatters import MessageBuilder
        tests.append(("✅ formatters.py", True))
    except Exception as e:
        tests.append((f"❌ formatters.py: {e}", False))
    
    for test, result in tests:
        print(f"  {test}")
    
    return all(r for _, r in tests)

def test_database_structure():
    print("\n🧪 اختبار قاعدة البيانات...")
    
    try:
        from database import Database
        from config import DB_FILE
        
        db = Database(":memory:")
        
        tests = []
        
        try:
            db.add_user(123, "test_user", "Test")
            tests.append(("✅ إضافة مستخدم", True))
        except Exception as e:
            tests.append((f"❌ إضافة مستخدم: {e}", False))
        
        try:
            user = db.get_user(123)
            if user:
                tests.append(("✅ الحصول على مستخدم", True))
            else:
                tests.append(("⚠️ المستخدم غير موجود", False))
        except Exception as e:
            tests.append((f"❌ الحصول على مستخدم: {e}", False))
        
        for test, result in tests:
            print(f"  {test}")
        
        return all(r for _, r in tests)
    except Exception as e:
        print(f"  ❌ خطأ في الاختبار: {e}")
        return False

def test_helpers():
    print("\n🧪 اختبار المساعدات...")
    
    try:
        from helpers import (
            seconds_to_human, safe_html_escape, validate_token,
            extract_token_from_code, get_file_size, format_size
        )
        
        tests = []
        
        try:
            result = seconds_to_human(3661)
            expected = "س" in result or "د" in result
            tests.append((f"✅ seconds_to_human: {result}", expected))
        except Exception as e:
            tests.append((f"❌ seconds_to_human: {e}", False))
        
        try:
            result = safe_html_escape("<script>alert('xss')</script>")
            tests.append(("✅ safe_html_escape", True))
        except Exception as e:
            tests.append((f"❌ safe_html_escape: {e}", False))
        
        try:
            result = format_size(1024 * 1024)
            tests.append((f"✅ format_size: {result}", True))
        except Exception as e:
            tests.append((f"❌ format_size: {e}", False))
        
        for test, result in tests:
            print(f"  {test}")
        
        return all(r for _, r in tests)
    except Exception as e:
        print(f"  ❌ خطأ في الاختبار: {e}")
        return False

def test_payment_system():
    print("\n🧪 اختبار نظام الدفع...")
    
    try:
        from payment_system import PaymentSystem, get_plan_emoji, get_plan_name
        
        tests = []
        
        try:
            price, currency = PaymentSystem.get_plan_price('pro')
            tests.append((f"✅ سعر الخطة Pro: {price} {currency}", True))
        except Exception as e:
            tests.append((f"❌ سعر الخطة: {e}", False))
        
        try:
            emoji = get_plan_emoji('ultra')
            tests.append((f"✅ emoji الخطة: {emoji}", True))
        except Exception as e:
            tests.append((f"❌ emoji الخطة: {e}", False))
        
        for test, result in tests:
            print(f"  {test}")
        
        return all(r for _, r in tests)
    except Exception as e:
        print(f"  ❌ خطأ في الاختبار: {e}")
        return False

def test_config():
    print("\n🧪 اختبار الإعدادات...")
    
    try:
        from config import PLANS, MESSAGES, UI_CONFIG, SECURITY_CONFIG
        
        tests = []
        
        if len(PLANS) > 0:
            tests.append((f"✅ عدد الخطط: {len(PLANS)}", True))
        else:
            tests.append(("❌ لا توجد خطط", False))
        
        if len(MESSAGES) > 0:
            tests.append((f"✅ عدد الرسائل: {len(MESSAGES)}", True))
        else:
            tests.append(("❌ لا توجد رسائل", False))
        
        if UI_CONFIG.get('bar_length', 0) > 0:
            tests.append(("✅ تكوين الواجهة", True))
        else:
            tests.append(("❌ تكوين الواجهة ناقص", False))
        
        for test, result in tests:
            print(f"  {test}")
        
        return all(r for _, r in tests)
    except Exception as e:
        print(f"  ❌ خطأ في الاختبار: {e}")
        return False

def main():
    print("="*50)
    print("🚀 اختبار شامل لـ NeurHostX Bot V8.5")
    print("="*50)
    
    results = []
    
    results.append(("الاستيرادات", test_imports()))
    results.append(("قاعدة البيانات", test_database_structure()))
    results.append(("المساعدات", test_helpers()))
    results.append(("نظام الدفع", test_payment_system()))
    results.append(("الإعدادات", test_config()))
    
    print("\n" + "="*50)
    print("📊 النتائج النهائية:")
    print("="*50)
    
    for test_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {test_name}")
    
    total = len(results)
    passed = sum(1 for _, r in results if r)
    
    print("\n" + "="*50)
    print(f"🎯 النتيجة: {passed}/{total} اختبارات ناجحة")
    
    if passed == total:
        print("✅ جميع الاختبارات نجحت! البوت جاهز للنشر!")
    else:
        print(f"⚠️ {total - passed} اختبار فشل. يرجى المراجعة.")
    
    print("="*50)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
