#!/usr/bin/env python3
"""
Security setup and migration script for Outscaled.GG
Run this script to set up enhanced security features
"""

import os
import sys
import secrets
import subprocess
from pathlib import Path

def generate_secret_key():
    """Generate a secure secret key"""
    return secrets.token_urlsafe(64)

def check_environment():
    """Check if environment is properly configured"""
    print("🔍 Checking environment configuration...")
    
    # Check for .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found")
        
        # Ask if user wants to create one
        response = input("Would you like to create a .env file from .env.example? (y/n): ")
        if response.lower() == 'y':
            create_env_file()
        else:
            print("Please create a .env file with required configuration")
            return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check critical settings
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key or secret_key == "your-secret-key-here-change-in-production":
        print("❌ SECRET_KEY not properly configured")
        
        # Generate new secret key
        new_key = generate_secret_key()
        print(f"✅ Generated new secret key: {new_key}")
        
        # Update .env file
        update_env_file("SECRET_KEY", new_key)
    else:
        print("✅ SECRET_KEY properly configured")
    
    return True

def create_env_file():
    """Create .env file from .env.example"""
    try:
        # Copy .env.example to .env
        with open(".env.example", "r") as example_file:
            content = example_file.read()
        
        # Generate secret key
        secret_key = generate_secret_key()
        content = content.replace("your-secret-key-here-change-in-production", secret_key)
        
        with open(".env", "w") as env_file:
            env_file.write(content)
        
        print("✅ Created .env file with generated secret key")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def update_env_file(key, value):
    """Update a value in the .env file"""
    try:
        # Read current .env file
        with open(".env", "r") as f:
            lines = f.readlines()
        
        # Update the key
        updated = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                updated = True
                break
        
        # If key not found, add it
        if not updated:
            lines.append(f"{key}={value}\n")
        
        # Write back to file
        with open(".env", "w") as f:
            f.writelines(lines)
        
        print(f"✅ Updated {key} in .env file")
        return True
    except Exception as e:
        print(f"❌ Failed to update .env file: {e}")
        return False

def install_dependencies():
    """Install security dependencies"""
    print("📦 Installing security dependencies...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "-r", "requirements_security.txt"
        ], check=True)
        print("✅ Security dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_database():
    """Set up database with security enhancements"""
    print("🗄️ Setting up database...")
    
    try:
        # Import database modules
        from app.database_enhanced import DatabaseManager
        from app.auth.models import Base
        
        # Create tables
        DatabaseManager.create_tables()
        print("✅ Database tables created")
        
        # Create performance indexes if PostgreSQL
        database_url = os.getenv("DATABASE_URL", "")
        if database_url.startswith("postgresql"):
            from app.database_enhanced import create_performance_indexes
            create_performance_indexes()
            print("✅ Performance indexes created")
        
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def run_security_tests():
    """Run security test suite"""
    print("🧪 Running security tests...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/security/", "-v"
        ], check=True)
        print("✅ Security tests passed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Security tests failed: {e}")
        return False

def check_redis_connection():
    """Check Redis connection for rate limiting"""
    print("🔴 Checking Redis connection...")
    
    try:
        import redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        r.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"⚠️ Redis connection failed: {e}")
        print("   Rate limiting will use in-memory fallback")
        return False

def security_health_check():
    """Perform comprehensive security health check"""
    print("\n🔒 Security Health Check")
    print("=" * 50)
    
    checks = [
        ("Environment Configuration", check_environment),
        ("Redis Connection", check_redis_connection),
        ("Database Setup", setup_database),
        ("Security Tests", run_security_tests),
    ]
    
    results = {}
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}...")
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"❌ {check_name} failed: {e}")
            results[check_name] = False
    
    # Summary
    print("\n📊 Security Setup Summary")
    print("=" * 50)
    
    all_passed = True
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All security checks passed!")
        print("   Your Outscaled.GG installation is secure and ready for production.")
    else:
        print("\n⚠️ Some security checks failed.")
        print("   Please review the errors above and fix them before deployment.")
    
    return all_passed

def generate_api_key_for_testing():
    """Generate an API key for testing"""
    print("\n🔑 Generating test API key...")
    
    try:
        from app.auth.security_enhanced import SecureAPIKeyManager
        
        api_key, key_hash = SecureAPIKeyManager.generate_api_key()
        
        print(f"✅ Test API Key: {api_key}")
        print(f"   (Hash: {key_hash[:50]}...)")
        print("   ⚠️ Save this key - it won't be shown again!")
        
        return api_key
    except Exception as e:
        print(f"❌ Failed to generate API key: {e}")
        return None

def main():
    """Main setup function"""
    print("🚀 Outscaled.GG Security Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("app").exists():
        print("❌ Please run this script from the backend directory")
        sys.exit(1)
    
    # Install dependencies first
    if not install_dependencies():
        print("❌ Setup failed at dependency installation")
        sys.exit(1)
    
    # Run security health check
    if security_health_check():
        # Generate test API key
        generate_api_key_for_testing()
        
        print("\n🎯 Next Steps:")
        print("1. Update your .env file with production settings")
        print("2. Set up PostgreSQL and Redis for production")
        print("3. Configure OAuth providers (Google/Discord)")
        print("4. Set up monitoring and alerting")
        print("5. Run: python -m uvicorn app.main:app --reload")
        
        print("\n📚 Documentation:")
        print("- Security features: ./docs/SECURITY.md")
        print("- API documentation: http://localhost:8000/docs")
        print("- Rate limiting: ./docs/RATE_LIMITING.md")
    else:
        print("\n❌ Setup incomplete. Please fix the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()