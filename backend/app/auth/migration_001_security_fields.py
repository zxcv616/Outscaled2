#!/usr/bin/env python3
"""
Database migration script: Add security fields to User model
Migration 001: Security Enhancements
"""

from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

def upgrade_database(db: Session) -> bool:
    """
    Apply security field upgrades to the database
    Returns True if successful, False otherwise
    """
    try:
        logger.info("Starting database migration 001: Security fields")
        
        # Check if we're using SQLite or PostgreSQL/MySQL
        db_type = str(db.bind.url).split("://")[0]
        logger.info(f"Detected database type: {db_type}")
        
        migrations = [
            # Add security fields to users table
            "ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE",
            "ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN account_locked_until DATETIME",
            "ALTER TABLE users ADD COLUMN last_login DATETIME",
            "ALTER TABLE users ADD COLUMN password_changed_at DATETIME DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE users ADD COLUMN two_factor_enabled BOOLEAN DEFAULT FALSE",
            "ALTER TABLE users ADD COLUMN two_factor_secret VARCHAR(100)",
            
            # Update subscription_tier to use enum values consistently
            "UPDATE users SET subscription_tier = 'free' WHERE subscription_tier IS NULL OR subscription_tier = ''",
        ]
        
        # PostgreSQL specific adjustments
        if db_type == "postgresql":
            migrations = [
                # PostgreSQL uses TIMESTAMP instead of DATETIME
                migration.replace("DATETIME", "TIMESTAMP") 
                for migration in migrations
            ]
            migrations = [
                # PostgreSQL uses NOW() instead of CURRENT_TIMESTAMP for defaults
                migration.replace("DEFAULT CURRENT_TIMESTAMP", "DEFAULT NOW()") 
                for migration in migrations
            ]
        
        # Execute migrations
        for i, migration in enumerate(migrations, 1):
            try:
                logger.info(f"Executing migration step {i}: {migration}")
                db.execute(text(migration))
                db.commit()
                logger.info(f"Migration step {i} completed successfully")
                
            except SQLAlchemyError as e:
                # Check if error is because column already exists
                error_msg = str(e).lower()
                if "already exists" in error_msg or "duplicate column" in error_msg:
                    logger.warning(f"Column already exists in step {i}, skipping: {migration}")
                    db.rollback()
                    continue
                else:
                    logger.error(f"Migration step {i} failed: {e}")
                    db.rollback()
                    return False
        
        # Verify migrations by checking column existence
        verification_queries = [
            "SELECT email_verified FROM users LIMIT 1",
            "SELECT failed_login_attempts FROM users LIMIT 1", 
            "SELECT account_locked_until FROM users LIMIT 1"
        ]
        
        for query in verification_queries:
            try:
                db.execute(text(query))
                logger.info(f"Verification passed: {query}")
            except SQLAlchemyError as e:
                logger.error(f"Verification failed for {query}: {e}")
                return False
        
        logger.info("Database migration 001 completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed with unexpected error: {e}")
        db.rollback()
        return False

def downgrade_database(db: Session) -> bool:
    """
    Rollback security field migration
    WARNING: This will remove security data permanently
    """
    try:
        logger.warning("Rolling back database migration 001: Security fields")
        
        # Drop security columns (WARNING: Data loss)
        rollback_migrations = [
            "ALTER TABLE users DROP COLUMN email_verified",
            "ALTER TABLE users DROP COLUMN failed_login_attempts", 
            "ALTER TABLE users DROP COLUMN account_locked_until",
            "ALTER TABLE users DROP COLUMN last_login",
            "ALTER TABLE users DROP COLUMN password_changed_at",
            "ALTER TABLE users DROP COLUMN two_factor_enabled",
            "ALTER TABLE users DROP COLUMN two_factor_secret"
        ]
        
        for i, migration in enumerate(rollback_migrations, 1):
            try:
                logger.info(f"Executing rollback step {i}: {migration}")
                db.execute(text(migration))
                db.commit()
                
            except SQLAlchemyError as e:
                error_msg = str(e).lower()
                if "doesn't exist" in error_msg or "no such column" in error_msg:
                    logger.warning(f"Column doesn't exist in rollback step {i}, skipping")
                    db.rollback()
                    continue
                else:
                    logger.error(f"Rollback step {i} failed: {e}")
                    db.rollback()
                    return False
        
        logger.info("Database migration 001 rollback completed")
        return True
        
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        db.rollback()
        return False

def check_migration_status(db: Session) -> dict:
    """
    Check if security fields migration has been applied
    Returns status information
    """
    status = {
        "migration_applied": False,
        "missing_columns": [],
        "existing_columns": [],
        "database_type": str(db.bind.url).split("://")[0]
    }
    
    security_columns = [
        "email_verified",
        "failed_login_attempts", 
        "account_locked_until",
        "last_login",
        "password_changed_at",
        "two_factor_enabled",
        "two_factor_secret"
    ]
    
    for column in security_columns:
        try:
            db.execute(text(f"SELECT {column} FROM users LIMIT 1"))
            status["existing_columns"].append(column)
        except SQLAlchemyError:
            status["missing_columns"].append(column)
    
    status["migration_applied"] = len(status["missing_columns"]) == 0
    
    return status

if __name__ == "__main__":
    # Standalone migration runner
    import sys
    import os
    
    # Add parent directory to path for imports
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from database import get_db
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get database session
    db = next(get_db())
    
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "status":
            # Check migration status
            status = check_migration_status(db)
            print(f"\nMigration Status Report:")
            print(f"Database Type: {status['database_type']}")
            print(f"Migration Applied: {status['migration_applied']}")
            print(f"Existing Columns: {status['existing_columns']}")
            print(f"Missing Columns: {status['missing_columns']}")
            
        elif len(sys.argv) > 1 and sys.argv[1] == "downgrade":
            # Rollback migration
            if input("WARNING: This will permanently delete security data. Continue? (yes/no): ") == "yes":
                success = downgrade_database(db)
                print(f"Migration rollback: {'SUCCESS' if success else 'FAILED'}")
            else:
                print("Migration rollback cancelled")
                
        else:
            # Apply migration
            success = upgrade_database(db)
            print(f"Migration: {'SUCCESS' if success else 'FAILED'}")
            
            if success:
                print("\nSecurity fields added successfully!")
                print("- email_verified (BOOLEAN)")
                print("- failed_login_attempts (INTEGER)")
                print("- account_locked_until (DATETIME)")
                print("- last_login (DATETIME)")
                print("- password_changed_at (DATETIME)")
                print("- two_factor_enabled (BOOLEAN)")
                print("- two_factor_secret (VARCHAR)")
                
    except Exception as e:
        logger.error(f"Migration script failed: {e}")
        print(f"ERROR: {e}")
        
    finally:
        db.close()