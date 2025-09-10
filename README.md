# Bank Statement Analyzer Telegram Bot

A powerful Telegram bot that analyzes PDF bank statements using OpenAI GPT-4 to extract transactions and identify recurring payments. Built with Python, PostgreSQL, and modern deployment tools.

## ✨ Key Features

### 📄 **Smart PDF Processing**
- Upload bank statement PDFs directly in Telegram (up to 50MB)
- OpenAI Vision API converts PDF pages to images for analysis
- Supports both text-based and scanned PDF statements
- Automatic file cleanup after processing for privacy

### 🤖 **AI-Powered Visual Analysis**
- Uses OpenAI GPT-4o Vision API for direct PDF image processing
- No text extraction needed - analyzes PDF pages as images
- Intelligent transaction extraction from ACCOUNT ACTIVITY sections
- Automatic categorization (groceries, utilities, entertainment, etc.)
- Handles scanned PDFs and various bank statement formats

### 📊 **Recurring Payment Detection**
- Identifies subscription services, utilities, and recurring charges
- Calculates frequency patterns (monthly, weekly, etc.)
- Groups similar transactions by merchant
- Provides spending insights and summaries

### 💾 **Secure Data Management**
- PostgreSQL database for reliable transaction storage
- User isolation by Telegram ID
- Encrypted data storage (when using managed DB services)
- Complete transaction history and analysis tracking

### 🔒 **Privacy & Security**
- Files deleted immediately after processing
- No sensitive data logged
- Secure environment variable configuration
- User data completely isolated

## 🛠️ Bot Commands & Usage

### Available Commands
- `/start` - Welcome message and bot introduction
- `/help` - Detailed help and instructions
- `/history` - View your uploaded statements (coming soon)

### Interactive Features
- **📊 View Summary** - Detailed recurring payments analysis
- **📋 View Transactions** - List of recent transactions (last 20)
- **⬅️ Back** - Navigation between different views

### How to Use
1. Start a conversation with your bot on Telegram
2. Send `/start` to begin
3. Upload a PDF bank statement
4. Wait for processing (30-60 seconds)
5. Click "📊 View Summary" to see recurring payments analysis
6. Use "📋 View Transactions" to see individual transaction details

## 📋 Prerequisites

- **Python 3.11** - Specified in runtime.txt (3.13+ has compatibility issues)
- **PostgreSQL database** - For transaction storage
- **Telegram Bot Token** - Get from @BotFather on Telegram
- **OpenAI API Key** - For GPT-4 transaction analysis

## Quick Start with Docker

1. **Clone and setup**:
   ```bash
   git clone <your-repo>
   cd SuperApp
   ```

2. **Create environment file**:
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` with your credentials**:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   OPENAI_API_KEY=your_openai_api_key
   ```

4. **Start with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

## Manual Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup PostgreSQL**:
   ```bash
   # Create database
   createdb bankbot_db
   
   # Update DATABASE_URL in config.py or .env
   ```

3. **Run the bot**:
   ```bash
   python bot.py
   ```

## Usage

1. Start a conversation with your bot on Telegram
2. Send `/start` to begin
3. Upload a PDF bank statement
4. Wait for processing (30-60 seconds)
5. Click "📊 View Summary" to see recurring payments analysis

## Deployment Options

### Recommended: Railway/Render/Heroku

For production deployment, I recommend using:

- **Railway**: Easy PostgreSQL + app deployment
- **Render**: Free tier with PostgreSQL addon
- **Heroku**: Classic PaaS with PostgreSQL addon

### Render Deployment (Recommended)

1. **Create PostgreSQL Database**:
   - Go to https://dashboard.render.com/new/postgres
   - Create a new database (free tier available)
   - Copy the **Internal Database URL**

2. **Create Web Service**:
   - Go to https://dashboard.render.com/new/web
   - Connect your GitHub repository
   - Use these settings:
     ```
     Runtime: Python
     Build Command: pip install -r requirements.txt
     Start Command: python bot.py
     ```

3. **Set Environment Variables**:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
   OPENAI_API_KEY=your_openai_api_key
   DATABASE_URL=internal_postgres_url_from_step_1
   ```

4. **Deploy**

### Railway Deployment

1. **Connect your GitHub repo to Railway**
2. **Add PostgreSQL database service**
3. **Set environment variables**:
   - `TELEGRAM_BOT_TOKEN`
   - `OPENAI_API_KEY`
   - `DATABASE_URL` (auto-provided by Railway)
4. **Deploy**

### Environment Variables

Required environment variables for the bot:

```bash
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather

# OpenAI Configuration  
OPENAI_API_KEY=your_openai_api_key

# Database Configuration
DATABASE_URL=postgresql://user:pass@host:port/db

# Application Configuration
DEBUG=False
PORT=8000
```

## 🏗️ Technical Architecture

### Core Components

#### **Bot Handler (bot.py)**
- Main application entry point
- Telegram bot message handlers
- User interaction management
- File upload processing workflow

#### **PDF Parser (pdf_parser.py)**
- PDF to image conversion using pdf2image
- OpenAI GPT-4o Vision API for direct image analysis
- Specialized parsing for ACCOUNT ACTIVITY sections
- Smart categorization and transaction extraction

#### **Database Layer (database.py)**
- SQLAlchemy ORM models
- PostgreSQL connection management
- User, BankStatement, Transaction, and RecurringPayment models
- Session management and cleanup

#### **Configuration (config.py)**
- Environment variable management
- Security and file upload settings
- Database connection configuration

### Deployment Tools

The project includes several automation scripts for easy deployment:

- **`docker-compose.yml`** - Complete Docker setup with PostgreSQL
- **`Dockerfile`** - Production-ready container configuration  
- **`runtime.txt`** - Python version specification for Render/Heroku
- **`.python-version`** - Python version for pyenv and other tools
- **`deploy.ps1`** - PowerShell deployment automation
- **`github_push.bat`** - Git automation for Windows
- **`quick_push.cmd`** - Fast commit and push workflow

### Compatibility Notes

- **Python 3.11** specified in runtime.txt (3.13+ has dependency issues)
- **SQLAlchemy 2.0.35+** required for modern Python compatibility
- **pdf2image + Pillow** for PDF to image conversion
- **OpenAI GPT-4o Vision API** for direct PDF image analysis
- **psycopg2-binary** used instead of asyncpg for reliability
- **All dependencies tested** with Python 3.11 and modern deployment platforms

## 💾 Database Schema

### Core Tables

#### **users**
- `id` - Primary key
- `telegram_id` - Unique Telegram user identifier
- `username` - Telegram username (optional)
- `created_at` - Registration timestamp
- `is_active` - User status flag

#### **bank_statements**  
- `id` - Primary key
- `user_id` - References telegram user
- `filename` - Original PDF filename
- `upload_date` - Processing timestamp
- `processed` - Processing status flag
- `raw_text` - Extracted PDF text
- `parsed_data` - JSON structured data

#### **transactions**
- `id` - Primary key
- `statement_id` - Links to bank statement
- `date` - Transaction date
- `description` - Transaction description
- `amount` - Transaction amount (negative for debits)
- `balance` - Account balance after transaction
- `category` - AI-assigned category
- `is_recurring` - Recurring payment flag

#### **recurring_payments**
- `id` - Primary key
- `user_id` - User identifier
- `merchant_name` - Merchant/service name
- `category` - Payment category
- `average_amount` - Average payment amount
- `frequency` - Payment frequency (monthly, weekly, etc.)
- `last_payment_date` - Most recent payment
- `transaction_count` - Number of occurrences

## 💰 API Costs & Performance

### OpenAI Usage
- **Cost per statement**: ~$0.10-0.50 (depending on statement size)
- **Processing time**: 30-60 seconds per statement
- **Model used**: GPT-4 for optimal accuracy
- **Token usage**: ~2000-8000 tokens per statement

### Performance Optimizations
- Efficient PDF text extraction
- Optimized prompts for faster processing
- Database connection pooling
- Async message handling

## 🔒 Security & Privacy Features

### Data Protection
- **Immediate file deletion** after processing
- **No sensitive data logging** in application logs
- **Database encryption at rest** (when using managed DB services)
- **User data isolation** by Telegram ID
- **Secure environment variables** for API keys

### Privacy Compliance
- Only transaction metadata stored (no account numbers)
- Raw PDF text discarded after analysis
- User can request data deletion
- No cross-user data sharing

## ⚠️ Limitations & Requirements

### PDF Requirements
- **Both text-based and scanned PDFs** supported (thanks to Vision API)
- **Maximum file size**: 50MB
- **Valid PDF format** (corrupted files will be rejected)
- **Clear, readable statements** (avoid blurry or low-quality scans)
- **Standard bank statement format** with ACCOUNT ACTIVITY section
- **Language**: English statements work best

### Technical Requirements
- **Internet connection** required for OpenAI API
- **PostgreSQL database** for data storage
- **Valid API keys** for Telegram and OpenAI
- **Python 3.11** runtime environment (specified in runtime.txt)

## 🔧 Troubleshooting

### Common Issues

1. **"Error extracting text from PDF"**
   - ✅ Ensure PDF contains readable text (not scanned images)
   - ✅ Try a different statement format or bank
   - ✅ Check if PDF is password protected (remove password first)
   - ✅ Verify file is not corrupted or incomplete
   - ✅ Re-download PDF from your bank if issues persist

2. **"Error parsing with OpenAI"**
   - ✅ Check OpenAI API key validity
   - ✅ Verify API quota and billing status
   - ✅ Ensure sufficient credits in OpenAI account
   - ✅ Check internet connectivity

3. **Database connection errors**
   - ✅ Verify DATABASE_URL format is correct
   - ✅ Check PostgreSQL service status
   - ✅ Ensure database credentials are valid
   - ✅ Test database connectivity manually

4. **Bot not responding**
   - ✅ Verify TELEGRAM_BOT_TOKEN is correct
   - ✅ Check bot permissions with @BotFather
   - ✅ Ensure bot is not stopped or rate-limited
   - ✅ Check application logs for errors

5. **Deployment build failures**
   - ✅ Ensure Python 3.11 is specified in runtime.txt and .python-version
   - ✅ Check dependency compatibility in requirements.txt
   - ✅ Use SQLAlchemy 2.0.35+ for Python 3.13 compatibility
   - ✅ Avoid Python 3.13+ due to various dependency compatibility issues
   - ✅ Use psycopg2-binary instead of asyncpg for PostgreSQL

### Debug Commands

```bash
# Check bot logs
docker-compose logs bot

# Check database logs  
docker-compose logs postgres

# Test database connection
docker-compose exec postgres psql -U bankbot_user -d bankbot_db

# View application status
docker-compose ps
```

### Support & Development

For issues or questions:
1. 📊 **Check logs**: `docker-compose logs bot`
2. 🔧 **Verify environment variables** in `.env` file
3. 🧪 **Test with sample bank statement** 
4. 📚 **Review documentation** and error messages
5. 🐛 **Open GitHub issue** for bugs or feature requests

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and test thoroughly
4. **Update documentation** (including this README)
5. **Commit changes**: `git commit -m 'Add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Submit a pull request**

### Development Guidelines
- Follow Python PEP 8 style guidelines
- Add docstrings to all functions
- Include unit tests for new features
- Update README.md for any functionality changes

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 Links

- **GitHub Repository**: https://github.com/fastishevskiy-png/telegramm-app
- **Telegram Bot API**: https://core.telegram.org/bots/api
- **OpenAI API**: https://openai.com/api/
- **PostgreSQL**: https://www.postgresql.org/
