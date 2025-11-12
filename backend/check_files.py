"""
Diagnostic Script for ZAKIA Chatbot
Checks which files exist and their status
"""

import os
import sys

print("=" * 70)
print("🔍 ZAKIA CHATBOT - FILE DIAGNOSTIC CHECK")
print("=" * 70)

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

print(f"\n📁 Project Root: {project_root}")
print(f"📁 Backend Dir: {script_dir}")

# Define expected files
files_to_check = {
    "Core Files": [
        "app.py",
        "database.py",
        "reminder_model.py",
    ],
    "Route Files": [
        "routes/__init__.py",
        "routes/chat_routes.py",
        "routes/admin_routes.py",
        "routes/zakat_routes.py",
        "routes/reminder_routes.py",
        "routes/admin_reminder_routes.py",
    ],
    "Service Files": [
        "services/database_service.py",
        "services/nlp_service.py",
    ]
}

print("\n" + "=" * 70)
print("📊 FILE CHECK RESULTS")
print("=" * 70)

missing_files = []
existing_files = []

for category, files in files_to_check.items():
    print(f"\n📂 {category}:")
    for file_path in files:
        full_path = os.path.join(script_dir, file_path)
        exists = os.path.exists(full_path)
        
        if exists:
            size = os.path.getsize(full_path)
            status = f"✅ EXISTS ({size:,} bytes)"
            existing_files.append(file_path)
        else:
            status = "❌ MISSING"
            missing_files.append(file_path)
        
        print(f"   {file_path:<40} {status}")

# Check for reminder_bp in reminder_routes.py
print("\n" + "=" * 70)
print("🔎 BLUEPRINT CHECK")
print("=" * 70)

reminder_routes_path = os.path.join(script_dir, "routes", "reminder_routes.py")
if os.path.exists(reminder_routes_path):
    with open(reminder_routes_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    has_reminder_bp = 'reminder_bp' in content
    has_blueprint_creation = 'Blueprint(' in content and 'reminder' in content
    
    print(f"   reminder_routes.py exists: ✅")
    print(f"   Contains 'reminder_bp': {'✅ YES' if has_reminder_bp else '❌ NO'}")
    print(f"   Has Blueprint creation: {'✅ YES' if has_blueprint_creation else '❌ NO'}")
    
    if not has_reminder_bp:
        print(f"\n   ⚠️ WARNING: reminder_bp not found in reminder_routes.py!")
        print(f"   This is causing the ImportError.")
else:
    print(f"   ❌ reminder_routes.py does not exist")

# Summary
print("\n" + "=" * 70)
print("📊 SUMMARY")
print("=" * 70)
print(f"✅ Existing files: {len(existing_files)}")
print(f"❌ Missing files: {len(missing_files)}")

if missing_files:
    print(f"\n⚠️ Missing Files:")
    for file in missing_files:
        print(f"   - {file}")

# Recommendations
print("\n" + "=" * 70)
print("💡 RECOMMENDATIONS")
print("=" * 70)

if "routes/reminder_routes.py" in missing_files:
    print("1. ❌ Create routes/reminder_routes.py")
    print("   Use the 'fixed_reminder_routes' artifact")

elif "routes/reminder_routes.py" in existing_files:
    reminder_routes_path = os.path.join(script_dir, "routes", "reminder_routes.py")
    with open(reminder_routes_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if 'reminder_bp' not in content:
        print("1. ⚠️ Update routes/reminder_routes.py")
        print("   The file exists but doesn't export 'reminder_bp'")
        print("   Replace with the 'fixed_reminder_routes' artifact")
    else:
        print("1. ✅ routes/reminder_routes.py is OK")

if "routes/admin_reminder_routes.py" in missing_files:
    print("2. ❌ Create routes/admin_reminder_routes.py")
    print("   Use the 'complete_admin_reminder_routes' artifact")
else:
    print("2. ✅ routes/admin_reminder_routes.py exists")

if "reminder_model.py" in existing_files:
    print("3. ✅ reminder_model.py exists")
    print("   Consider updating to add get_by_id(), delete(), get_stats() methods")
else:
    print("3. ❌ Create reminder_model.py")

print("\n" + "=" * 70)
print("🚀 NEXT STEPS")
print("=" * 70)
print("""
1. Fix missing/incorrect files using the artifacts provided
2. Replace app.py with 'bulletproof_app_py' artifact
3. Run: python app.py
4. Check for "✅" messages indicating successful loading

The bulletproof_app_py version will work even if some files are missing!
""")

print("=" * 70)
print("✨ Diagnostic check complete!")
print("=" * 70)