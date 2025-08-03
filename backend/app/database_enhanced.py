#!/usr/bin/env python3
"""
Enhanced database configuration with connection pooling and optimization
"""

import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, NullPool
from dotenv import load_dotenv
import logging

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration with environment-specific settings"""
    
    def __init__(self):
        self.DATABASE_URL = os.getenv("DATABASE_URL")
        self.ENV = os.getenv("ENV", "development")
        
        # Pool configuration
        self.POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
        self.MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        self.POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # 1 hour
        
        # Connection configuration
        self.CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", "10"))
        self.STATEMENT_TIMEOUT = int(os.getenv("DB_STATEMENT_TIMEOUT", "30000"))  # 30 seconds
        
        # SQLite fallback for development
        if not self.DATABASE_URL:
            self.DATABASE_URL = "sqlite:///./outscaled.db"
            logger.warning("No DATABASE_URL found, using SQLite for development")

db_config = DatabaseConfig()

def create_database_engine():
    """Create optimized database engine based on environment"""
    
    if db_config.DATABASE_URL.startswith("postgresql"):
        # PostgreSQL production configuration
        engine = create_engine(
            db_config.DATABASE_URL,
            poolclass=QueuePool,
            pool_size=db_config.POOL_SIZE,
            max_overflow=db_config.MAX_OVERFLOW,
            pool_timeout=db_config.POOL_TIMEOUT,
            pool_recycle=db_config.POOL_RECYCLE,
            pool_pre_ping=True,  # Verify connections before use
            echo=db_config.ENV == "development",
            connect_args={
                "connect_timeout": db_config.CONNECT_TIMEOUT,
                "options": f"-c statement_timeout={db_config.STATEMENT_TIMEOUT}ms"
            }
        )
        
        # PostgreSQL-specific optimizations
        @event.listens_for(engine, "connect")
        def set_postgresql_settings(dbapi_connection, connection_record):
            """Set PostgreSQL connection settings for performance"""
            with dbapi_connection.cursor() as cursor:
                # Enable prepared statements
                cursor.execute("SET plan_cache_mode = auto")
                # Optimize for OLTP workloads
                cursor.execute("SET random_page_cost = 1.1")
                # Enable parallel workers
                cursor.execute("SET max_parallel_workers_per_gather = 2")
                
        logger.info(f"Created PostgreSQL engine with pool_size={db_config.POOL_SIZE}")
        
    elif db_config.DATABASE_URL.startswith("mysql"):
        # MySQL configuration
        engine = create_engine(
            db_config.DATABASE_URL,
            poolclass=QueuePool,
            pool_size=db_config.POOL_SIZE,
            max_overflow=db_config.MAX_OVERFLOW,
            pool_timeout=db_config.POOL_TIMEOUT,
            pool_recycle=db_config.POOL_RECYCLE,
            pool_pre_ping=True,
            echo=db_config.ENV == "development",
            connect_args={
                "connect_timeout": db_config.CONNECT_TIMEOUT,
                "charset": "utf8mb4",
                "use_unicode": True
            }
        )
        
        logger.info(f"Created MySQL engine with pool_size={db_config.POOL_SIZE}")
        
    else:
        # SQLite development configuration
        engine = create_engine(
            db_config.DATABASE_URL,
            poolclass=NullPool,  # SQLite doesn't need connection pooling
            echo=db_config.ENV == "development",
            connect_args={
                "check_same_thread": False,
                "timeout": 20
            }
        )
        
        # SQLite optimizations
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set SQLite pragmas for performance"""
            cursor = dbapi_connection.cursor()
            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            # Synchronous mode for better performance
            cursor.execute("PRAGMA synchronous=NORMAL")
            # Increase cache size (10MB)
            cursor.execute("PRAGMA cache_size=10000")
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
            
        logger.info("Created SQLite engine with optimizations")
    
    return engine

# Create engine
engine = create_database_engine()

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # Keep objects accessible after commit
)

# Base class for models
Base = declarative_base()

class DatabaseManager:
    """Database management utilities"""
    
    @staticmethod
    def get_db_stats():
        """Get database connection pool statistics"""
        if hasattr(engine.pool, 'size'):
            return {
                "pool_size": engine.pool.size(),
                "checked_in": engine.pool.checkedin(),
                "checked_out": engine.pool.checkedout(),
                "overflow": engine.pool.overflow(),
                "invalid": engine.pool.invalid()
            }
        return {"type": "sqlite", "stats": "not_applicable"}
    
    @staticmethod
    def health_check() -> dict:
        """Perform database health check"""
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1")).fetchone()
                latency_start = time.time()
                connection.execute(text("SELECT 1")).fetchone()
                latency = (time.time() - latency_start) * 1000
                
                return {
                    "status": "healthy",
                    "latency_ms": round(latency, 2),
                    "connection_stats": DatabaseManager.get_db_stats()
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connection_stats": DatabaseManager.get_db_stats()
            }
    
    @staticmethod
    def create_tables():
        """Create all database tables"""
        from .auth.models import Base as AuthBase
        
        # Import all models to register them
        from .auth.models import User, APIKey, PredictionHistory
        
        # Create tables
        AuthBase.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

# Dependency for FastAPI
def get_db():
    """FastAPI dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        db.close()

# Database session context manager
class DatabaseSession:
    """Context manager for database sessions"""
    
    def __enter__(self) -> Session:
        self.db = SessionLocal()
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.db.rollback()
        self.db.close()

# Enhanced query utilities
class QueryOptimizer:
    """Query optimization utilities"""
    
    @staticmethod
    def batch_insert(db: Session, model_class, data_list: list, batch_size: int = 1000):
        """Optimized batch insert for large datasets"""
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]
            db.bulk_insert_mappings(model_class, batch)
            db.commit()
    
    @staticmethod
    def batch_update(db: Session, model_class, data_list: list, batch_size: int = 1000):
        """Optimized batch update for large datasets"""
        for i in range(0, len(data_list), batch_size):
            batch = data_list[i:i + batch_size]
            db.bulk_update_mappings(model_class, batch)
            db.commit()
    
    @staticmethod
    def explain_query(db: Session, query):
        """Explain query execution plan (PostgreSQL)"""
        if db_config.DATABASE_URL.startswith("postgresql"):
            explained = db.execute(text(f"EXPLAIN ANALYZE {query}")).fetchall()
            return [row[0] for row in explained]
        return ["Query explanation not available for this database type"]

# Index suggestions for common queries
RECOMMENDED_INDEXES = [
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email);",
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username ON users(username);",
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);",
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);",
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_prediction_history_user_id ON prediction_history(user_id);",
    "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_prediction_history_created_at ON prediction_history(created_at);",
]

def create_performance_indexes():
    """Create recommended indexes for performance"""
    if db_config.DATABASE_URL.startswith("postgresql"):
        with engine.connect() as connection:
            for index_sql in RECOMMENDED_INDEXES:
                try:
                    connection.execute(text(index_sql))
                    logger.info(f"Created index: {index_sql}")
                except Exception as e:
                    logger.warning(f"Index creation failed: {e}")
    else:
        logger.info("Performance indexes are PostgreSQL-specific")

if __name__ == "__main__":
    # Initialize database
    import time
    
    print("Initializing database...")
    DatabaseManager.create_tables()
    
    if db_config.ENV == "production":
        print("Creating performance indexes...")
        create_performance_indexes()
    
    print("Database health check...")
    health = DatabaseManager.health_check()
    print(f"Health: {health}")
    
    print("Database initialization complete!")