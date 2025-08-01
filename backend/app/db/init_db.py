"""
Database initialization script.
Run this script to initialize the PostgreSQL database with the required tables.
"""

import os
import sys
from sqlalchemy import text
from app.config import settings
from app.models.database import Base
from app.db.connection import engine


def test_connection():
    """Test the database connection before initializing tables."""
    try:
        print("Testing database connection...")
        print(f"DATABASE_URL: {settings.DATABASE_URL}")
        
        # Test basic connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed!")
        print(f"Full error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False


def init_db():
    """Initialize the database by creating all tables."""
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
        return True
    except Exception as e:
        print(f"Error creating database tables: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False


def main():
    """Main initialization function."""
    # Check if we're running in the correct directory
    if not os.path.exists("app"):
        print("Error: Run this script from the backend directory")
        print("Usage: python -m app.db.init_db")
        sys.exit(1)
    
    print(f"Using database configuration from: {settings.Config.env_file}")
    
    # First test the connection
    if not test_connection():
        print("\n💡 Troubleshooting suggestions:")
        print("1. Check if your database server is running")
        print("2. Verify the DATABASE_URL is correct")
        print("3. Check network connectivity")
        print("4. Try adding SSL parameters if needed")
        sys.exit(1)
    
    # Initialize the database
    success = init_db()
    if not success:
        print("Database initialization failed.")
        sys.exit(1)
    
    # Create a default user if needed
    # Uncomment this when user authentication is implemented
    # create_first_user()
    
    print("✅ Database initialization complete!")
    print("Now, go to Supabase dashboard or use Supabase API to create your first user if needed.")


if __name__ == "__main__":
    main() 