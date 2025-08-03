#!/usr/bin/env python3
"""
Security rollback script for Outscaled.GG
Use this script to rollback security enhancements if needed
"""

import os
import sys
import shutil
from pathlib import Path

def backup_current_files():
    """Backup current enhanced security files"""
    print("📦 Creating backup of enhanced security files...")
    
    backup_dir = Path("security_backup")
    backup_dir.mkdir(exist_ok=True)
    
    files_to_backup = [
        "app/auth/security_enhanced.py",
        "app/auth/rate_limiter.py", 
        "app/auth/oauth.py",
        "app/auth/routes_enhanced.py",
        "app/auth/dependencies_enhanced.py",
        "app/database_enhanced.py",
        ".env"
    ]
    
    for file_path in files_to_backup:
        src = Path(file_path)
        if src.exists():
            dst = backup_dir / src.name
            shutil.copy2(src, dst)
            print(f"✅ Backed up {file_path}")
    
    print(f"📁 Backup created in {backup_dir}")

def restore_original_auth():
    """Restore original authentication system"""
    print("🔄 Restoring original authentication system...")
    
    # Update main.py to use original auth
    main_py_content = '''from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.auth.routes import router as auth_router

app = FastAPI(title="Outscaled.GG API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include original auth router
app.include_router(auth_router)

@app.get("/")
async def root():
    return {"message": "Outscaled.GG API"}
'''
    
    with open("app/main.py", "w") as f:
        f.write(main_py_content)
    
    print("✅ Restored original main.py")

def update_imports_to_original():
    """Update any files that import enhanced security to use original"""
    print("🔧 Updating imports to use original security...")
    
    files_to_update = [
        "app/auth/routes.py",
        "app/auth/dependencies.py"
    ]
    
    for file_path in files_to_update:
        if Path(file_path).exists():
            print(f"ℹ️ Please manually review {file_path} for enhanced imports")

def remove_enhanced_dependencies():
    """Remove enhanced security dependencies"""
    print("📦 Information about enhanced dependencies...")
    
    enhanced_deps = [
        "redis>=5.0.0",
        "argon2-cffi>=23.1.0", 
        "httpx>=0.25.0",
        "psycopg2-binary>=2.9.7",
        "sentry-sdk[fastapi]>=1.38.0"
    ]
    
    print("ℹ️ Enhanced dependencies that can be removed:")
    for dep in enhanced_deps:
        print(f"   - {dep}")
    
    print("💡 To remove: pip uninstall <package-name>")

def database_rollback_info():
    """Provide information about database rollback"""
    print("🗄️ Database rollback information...")
    
    print("""
📋 Manual database rollback steps:
    
1. Backup current database:
   pg_dump outscaled > backup_enhanced.sql
   
2. Remove enhanced columns (if they exist):
   ALTER TABLE api_keys DROP COLUMN IF EXISTS key_hash;
   ALTER TABLE api_keys DROP COLUMN IF EXISTS key_prefix;
   ALTER TABLE api_keys DROP COLUMN IF EXISTS allowed_ips;
   ALTER TABLE api_keys DROP COLUMN IF EXISTS permissions;
   
3. Remove performance indexes:
   DROP INDEX IF EXISTS idx_users_email;
   DROP INDEX IF EXISTS idx_users_username;
   DROP INDEX IF EXISTS idx_api_keys_user_id;
   DROP INDEX IF EXISTS idx_api_keys_key_hash;
   DROP INDEX IF EXISTS idx_prediction_history_user_id;
   DROP INDEX IF EXISTS idx_prediction_history_created_at;
   
4. Restore original api_keys.key column usage
   
⚠️ Warning: This will break any existing enhanced API keys!
""")

def clean_enhanced_files():
    """Remove enhanced security files"""
    print("🧹 Cleaning enhanced security files...")
    
    files_to_remove = [
        "app/auth/security_enhanced.py",
        "app/auth/rate_limiter.py",
        "app/auth/oauth.py", 
        "app/auth/routes_enhanced.py",
        "app/auth/dependencies_enhanced.py",
        "app/database_enhanced.py",
        "requirements_security.txt",
        "setup_security.py",
        "tests/security/",
        "alembic/versions/001_add_enhanced_security.py"
    ]
    
    for file_path in files_to_remove:
        path = Path(file_path)
        if path.is_file():
            path.unlink()
            print(f"🗑️ Removed {file_path}")
        elif path.is_dir():
            shutil.rmtree(path)
            print(f"🗑️ Removed directory {file_path}")
        else:
            print(f"ℹ️ {file_path} not found (already removed?)")

def rollback_env_file():
    """Rollback .env file to simpler configuration"""
    print("⚙️ Simplifying .env file...")
    
    simple_env_content = '''# Outscaled.GG Basic Configuration
# Basic secret key (change in production)
SECRET_KEY=your-secret-key-here-change-in-production

# Database (SQLite for development)
# DATABASE_URL=sqlite:///./outscaled.db

# Basic JWT settings
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
'''
    
    # Backup current .env
    if Path(".env").exists():
        shutil.copy2(".env", ".env.enhanced.backup")
        print("📦 Backed up current .env to .env.enhanced.backup")
    
    with open(".env", "w") as f:
        f.write(simple_env_content)
    
    print("✅ Created simplified .env file")

def verify_rollback():
    """Verify that rollback was successful"""
    print("🔍 Verifying rollback...")
    
    # Check that enhanced files are gone
    enhanced_files = [
        "app/auth/security_enhanced.py",
        "app/auth/rate_limiter.py",
        "app/database_enhanced.py"
    ]
    
    all_removed = True
    for file_path in enhanced_files:
        if Path(file_path).exists():
            print(f"⚠️ Enhanced file still exists: {file_path}")
            all_removed = False
    
    if all_removed:
        print("✅ All enhanced security files removed")
    
    # Check that original files exist
    original_files = [
        "app/auth/security.py",
        "app/auth/routes.py", 
        "app/auth/dependencies.py",
        "app/database.py"
    ]
    
    all_present = True
    for file_path in original_files:
        if not Path(file_path).exists():
            print(f"❌ Original file missing: {file_path}")
            all_present = False
    
    if all_present:
        print("✅ All original files present")
    
    return all_removed and all_present

def main():
    """Main rollback function"""
    print("🔄 Outscaled.GG Security Rollback")
    print("=" * 50)
    
    # Confirmation
    response = input("⚠️ This will remove all enhanced security features. Continue? (y/N): ")
    if response.lower() != 'y':
        print("❌ Rollback cancelled")
        return
    
    # Check if we're in the right directory
    if not Path("app").exists():
        print("❌ Please run this script from the backend directory")
        sys.exit(1)
    
    try:
        # Step 1: Backup current files
        backup_current_files()
        
        # Step 2: Restore original authentication
        restore_original_auth()
        
        # Step 3: Update imports
        update_imports_to_original()
        
        # Step 4: Provide dependency removal info
        remove_enhanced_dependencies()
        
        # Step 5: Database rollback info
        database_rollback_info()
        
        # Step 6: Simplify environment
        rollback_env_file()
        
        # Step 7: Clean enhanced files
        clean_enhanced_files()
        
        # Step 8: Verify rollback
        if verify_rollback():
            print("\n✅ Rollback completed successfully!")
            print("\n📋 Manual steps required:")
            print("1. Review and update any custom code that used enhanced features")
            print("2. Run database rollback commands (see above)")
            print("3. Restart your application")
            print("4. Test basic authentication functionality")
            print("\n📦 Enhanced files backed up in ./security_backup/")
        else:
            print("\n⚠️ Rollback completed with warnings - please review above")
            
    except Exception as e:
        print(f"\n❌ Rollback failed: {e}")
        print("Please manually restore from backup if needed")
        sys.exit(1)

if __name__ == "__main__":
    main()