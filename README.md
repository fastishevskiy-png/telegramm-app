# Bank Statement Analyzer Telegram Bot

A powerful Telegram bot that analyzes PDF bank statements using OpenAI GPT-4 to extract transactions and identify recurring payments.

## Features

- 📄 **PDF Upload**: Upload bank statement PDFs directly in Telegram
- 🤖 **AI-Powered Analysis**: Uses OpenAI GPT-4 to extract and categorize transactions
- 📊 **Recurring Payment Detection**: Automatically identifies subscription services, utilities, and other recurring charges
- 💾 **Secure Storage**: PostgreSQL database for transaction history
- 🔒 **Privacy-Focused**: Files are deleted after processing

## Prerequisites

- Python 3.11+
- PostgreSQL database
- Telegram Bot Token (from @BotFather)
- OpenAI API Key

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

### Railway Deployment

1. **Connect your GitHub repo to Railway**
2. **Add PostgreSQL database service**
3. **Set environment variables**:
   - `TELEGRAM_BOT_TOKEN`
   - `OPENAI_API_KEY`
   - `DATABASE_URL` (auto-provided by Railway)
4. **Deploy**

### Environment Variables

```bash
TELEGRAM_BOT_TOKEN=your_bot_token
OPENAI_API_KEY=your_openai_key
DATABASE_URL=postgresql://user:pass@host:port/db
DEBUG=False
PORT=8000
```

## Database Schema

The bot uses these main tables:

- **users**: Telegram user information
- **bank_statements**: Uploaded PDF metadata
- **transactions**: Individual transaction records
- **recurring_payments**: Identified recurring payment patterns

## API Costs

- OpenAI GPT-4 usage: ~$0.10-0.50 per bank statement
- Processing time: 30-60 seconds per statement

## Security Features

- Files deleted immediately after processing
- No sensitive data logged
- Database encryption at rest (when using managed DB services)
- User data isolated by Telegram ID

## Limitations

- PDF must contain readable text (not image-only scans)
- Supports most major bank statement formats
- Maximum file size: 50MB
- Requires internet connection for OpenAI API

## Troubleshooting

### Common Issues

1. **"Error extracting text from PDF"**
   - Ensure PDF contains readable text
   - Try a different statement format

2. **"Error parsing with OpenAI"**
   - Check OpenAI API key
   - Verify API quota/billing

3. **Database connection errors**
   - Verify DATABASE_URL format
   - Check PostgreSQL service status

### Support

For issues or questions:
1. Check the logs: `docker-compose logs bot`
2. Verify environment variables
3. Test with a sample bank statement

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
