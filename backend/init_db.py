#!/usr/bin/env python3
"""
Initialize database with all tables
"""

import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine
from app.auth.models import Base, User, APIKey, PredictionHistory

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    
    # Create all tables defined in our models
    Base.metadata.create_all(bind=engine)
    
    print("Database tables created successfully!")
    print("Tables created:")
    print("- users")
    print("- api_keys") 
    print("- prediction_history")

if __name__ == "__main__":
    create_tables()