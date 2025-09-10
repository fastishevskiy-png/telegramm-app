#!/usr/bin/env python3
"""
Setup script for Bank Statement Analyzer Bot
"""

import os
import sys
from database import create_tables

def setup_environment():
    """Create .env file if it doesn't exist"""
    if not os.path.exists('.env'):
        env_content = """# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# OpenAI Configuration  
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DATABASE_URL=postgresql://bankbot_user:your_secure_password@localhost:5432/bankbot_db

# Application Configuration
DEBUG=True
PORT=8000
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file - please update with your credentials")
    else:
        print("✅ .env file already exists")

def setup_database():
    """Initialize database tables"""
    try:
        create_tables()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        print("Make sure PostgreSQL is running and DATABASE_URL is correct")
        return False
    return True

def main():
    """Run setup process"""
    print("🚀 Setting up Bank Statement Analyzer Bot...\n")
    
    # Create environment file
    setup_environment()
    
    # Create uploads directory
    os.makedirs('uploads', exist_ok=True)
    print("✅ Created uploads directory")
    
    # Setup database
    print("\n📊 Setting up database...")
    if not setup_database():
        print("\n❌ Setup failed. Please check your database configuration.")
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Update .env file with your bot token and OpenAI API key")
    print("2. Make sure PostgreSQL is running")
    print("3. Run: python bot.py")
    print("\nFor Docker deployment:")
    print("1. Update docker-compose.yml with your credentials")
    print("2. Run: docker-compose up -d")

if __name__ == "__main__":
    main()
