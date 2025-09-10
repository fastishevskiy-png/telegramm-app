import logging
import os
import json
import asyncio
from datetime import datetime
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from config import Config
from database import (
    create_tables, 
    get_or_create_user, 
    BankStatement, 
    Transaction, 
    RecurringPayment,
    get_db
)
from pdf_parser import PDFParser

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Force new deployment - conflict resolution v2

class BankStatementBot:
    def __init__(self):
        self.pdf_parser = PDFParser()
        # Store user states for conversation flow
        self.user_states = {}
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /start is issued."""
        user = update.effective_user
        
        # Create or get user in database
        get_or_create_user(str(user.id), user.username)
        
        welcome_message = """
🏦 **Welcome to Bank Statement Analyzer Bot!**

I can help you analyze your bank statements and identify recurring payments.

**Features:**
📄 Upload PDF bank statements
🔍 Extract transaction data using AI
📊 Identify recurring payments
💡 Get insights about your spending patterns

**How to use:**
1. Send me a PDF of your bank statement
2. Wait for processing (usually 30-60 seconds)
3. Click "View Summary" to see recurring payments analysis

**Commands:**
/start - Show this message
/help - Get help
/history - View your uploaded statements

Let's get started! Send me a PDF bank statement to analyze.
        """
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""
        help_text = """
🔧 **Help & Instructions**

**Supported File Types:**
📄 PDF bank statements (up to 50MB)

**What I can analyze:**
• Transaction dates and amounts
• Merchant names and descriptions
• Recurring payment patterns
• Spending categories
• Monthly payment summaries

**Tips for best results:**
✅ Use clear, high-quality PDF statements
✅ Ensure text is readable (not image-only PDFs)
✅ Include statements with at least 1-2 months of data

**Privacy & Security:**
🔒 Your data is processed securely
🗑️ Files are deleted after processing
💾 Only transaction summaries are stored

Need help? Contact support or try /start to begin.
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle uploaded PDF documents."""
        user = update.effective_user
        document = update.message.document
        
        # Validate file type
        if not document.file_name.lower().endswith('.pdf'):
            await update.message.reply_text(
                "❌ Please send a PDF file only. Other file types are not supported."
            )
            return
        
        # Validate file size
        if document.file_size > Config.MAX_FILE_SIZE:
            await update.message.reply_text(
                f"❌ File too large. Maximum size is {Config.MAX_FILE_SIZE // (1024*1024)}MB."
            )
            return
        
        # Send processing message
        processing_msg = await update.message.reply_text(
            "📄 Processing your bank statement...\n"
            "⏳ This may take 30-60 seconds. Please wait."
        )
        
        try:
            # Download file
            file = await document.get_file()
            file_path = os.path.join(Config.UPLOAD_FOLDER, f"{user.id}_{document.file_name}")
            await file.download_to_drive(file_path)
            
            # Extract text from PDF
            await processing_msg.edit_text(
                "📄 Processing your bank statement...\n"
                "🔍 Extracting text from PDF..."
            )
            
            raw_text = self.pdf_parser.extract_text_from_pdf(file_path)
            
            # Parse transactions with OpenAI
            await processing_msg.edit_text(
                "📄 Processing your bank statement...\n"
                "🤖 Analyzing transactions with AI..."
            )
            
            parsed_data = self.pdf_parser.parse_bank_statement(raw_text)
            
            # Save to database
            db = get_db()
            try:
                # Create bank statement record
                statement = BankStatement(
                    user_id=int(user.id),
                    filename=document.file_name,
                    raw_text=raw_text,
                    parsed_data=json.dumps(parsed_data),
                    processed=True
                )
                db.add(statement)
                db.commit()
                db.refresh(statement)
                
                # Save individual transactions
                transactions = parsed_data.get('transactions', [])
                for tx_data in transactions:
                    try:
                        transaction = Transaction(
                            statement_id=statement.id,
                            date=datetime.strptime(tx_data['date'], '%Y-%m-%d'),
                            description=tx_data['description'],
                            amount=float(tx_data['amount']),
                            balance=float(tx_data.get('balance', 0)) if tx_data.get('balance') else None,
                            category=tx_data.get('category')
                        )
                        db.add(transaction)
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Skipping invalid transaction: {e}")
                        continue
                
                db.commit()
                
            finally:
                db.close()
            
            # Clean up file
            os.remove(file_path)
            
            # Create response with action buttons
            keyboard = [
                [InlineKeyboardButton("📊 View Summary", callback_data=f"summary_{statement.id}")],
                [InlineKeyboardButton("📋 View Transactions", callback_data=f"transactions_{statement.id}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            account_info = parsed_data.get('account_info', {})
            bank_name = account_info.get('bank_name', 'Your bank')
            statement_period = account_info.get('statement_period', 'Unknown period')
            transaction_count = len(transactions)
            
            success_message = f"""
✅ **Statement processed successfully!**

🏦 Bank: {bank_name}
📅 Period: {statement_period}
📊 Transactions found: {transaction_count}

What would you like to do next?
            """
            
            await processing_msg.edit_text(
                success_message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            await processing_msg.edit_text(
                f"❌ Error processing your statement: {str(e)}\n\n"
                "Please try again with a different PDF file or contact support."
            )
            
            # Clean up file if it exists
            if os.path.exists(file_path):
                os.remove(file_path)
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle button callback queries."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user_id = query.from_user.id
        
        if data.startswith('summary_'):
            statement_id = int(data.split('_')[1])
            await self.show_summary(query, statement_id, user_id)
            
        elif data.startswith('transactions_'):
            statement_id = int(data.split('_')[1])
            await self.show_transactions(query, statement_id, user_id)
    
    async def show_summary(self, query, statement_id: int, user_id: int) -> None:
        """Show recurring payments summary."""
        try:
            db = get_db()
            try:
                # Get statement
                statement = db.query(BankStatement).filter(
                    BankStatement.id == statement_id,
                    BankStatement.user_id == user_id
                ).first()
                
                if not statement:
                    await query.edit_message_text("❌ Statement not found.")
                    return
                
                # Get parsed data
                parsed_data = json.loads(statement.parsed_data)
                transactions = parsed_data.get('transactions', [])
                
                if not transactions:
                    await query.edit_message_text("❌ No transactions found in this statement.")
                    return
                
                # Analyze recurring payments
                analysis = self.pdf_parser.analyze_recurring_payments(transactions)
                
                # Format and send summary
                summary_message = self.pdf_parser.format_summary_message(analysis)
                
                # Add back button
                keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data=f"back_{statement_id}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    summary_message,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error showing summary: {e}")
            await query.edit_message_text(f"❌ Error generating summary: {str(e)}")
    
    async def show_transactions(self, query, statement_id: int, user_id: int) -> None:
        """Show list of transactions."""
        try:
            db = get_db()
            try:
                # Get transactions
                transactions = db.query(Transaction).filter(
                    Transaction.statement_id == statement_id
                ).order_by(Transaction.date.desc()).limit(20).all()
                
                if not transactions:
                    await query.edit_message_text("❌ No transactions found.")
                    return
                
                message = "📋 **Recent Transactions** (Last 20)\n\n"
                
                for tx in transactions:
                    date_str = tx.date.strftime('%Y-%m-%d')
                    amount_str = f"${abs(tx.amount):.2f}"
                    emoji = "💸" if tx.amount < 0 else "💰"
                    
                    # Truncate long descriptions
                    desc = tx.description[:30] + "..." if len(tx.description) > 30 else tx.description
                    
                    message += f"{emoji} **{date_str}**\n"
                    message += f"   {desc}\n"
                    message += f"   {amount_str}\n\n"
                
                # Add back button
                keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data=f"back_{statement_id}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    message,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error showing transactions: {e}")
            await query.edit_message_text(f"❌ Error loading transactions: {str(e)}")

def main() -> None:
    """Start the bot."""
    # Check required environment variables
    if not Config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable is not set!")
        return
    
    if not Config.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY environment variable is not set!")
        return
    
    # Create database tables with error handling
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        logger.error("Please check your DATABASE_URL environment variable")
        return
    
    # Create bot instance
    bot = BankStatementBot()
    
    # Create the Application with better error handling
    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # Clear any existing webhooks to prevent conflicts
    async def clear_webhook():
        try:
            await application.bot.delete_webhook(drop_pending_updates=True)
            logger.info("Webhook cleared successfully")
        except Exception as e:
            logger.warning(f"Could not clear webhook: {e}")
    
    import asyncio
    try:
        asyncio.run(clear_webhook())
    except Exception as e:
        logger.warning(f"Webhook clearing failed: {e}")
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(MessageHandler(filters.Document.PDF, bot.handle_document))
    application.add_handler(CallbackQueryHandler(bot.handle_callback_query))
    
    # Run the bot with error handling for conflicts
    try:
        logger.info("Starting Bank Statement Bot...")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,  # Drop any pending updates to avoid conflicts
            close_loop=False
        )
    except Exception as e:
        if "Conflict" in str(e):
            logger.error("Bot instance conflict detected. This usually resolves automatically in 1-2 minutes.")
            logger.error("If the issue persists, check if another bot instance is running.")
        else:
            logger.error(f"Error running bot: {e}")
        raise

if __name__ == '__main__':
    main()
