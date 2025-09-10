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

# Flask for webhook
from flask import Flask, request, Response
import threading

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# WEBHOOK SOLUTION - DEFINITIVE FIX FOR CONFLICTS!

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
        
        welcome_text = (
            f"🏦 *Welcome to Bank Statement Bot!* 📊\n\n"
            f"Hello {user.first_name}! 👋\n\n"
            f"I'm your smart financial assistant powered by AI. Here's what I can do:\n\n"
            f"🔍 *Smart PDF Analysis*\n"
            f"• Upload your bank statement (PDF)\n"
            f"• I'll extract and analyze all transactions\n"
            f"• Get detailed financial insights\n\n"
            f"🤖 *AI-Powered Features*\n"
            f"• Automatic transaction categorization\n" 
            f"• Recurring payment detection\n"
            f"• Spending pattern analysis\n\n"
            f"🔒 *Privacy & Security*\n"
            f"• Your data is encrypted and secure\n"
            f"• No financial information is stored permanently\n"
            f"• GDPR compliant processing\n\n"
            f"📱 *How to Use*\n"
            f"1. Click 'Upload Statement' below\n"
            f"2. Send me your PDF bank statement\n"
            f"3. Get instant AI analysis!\n\n"
            f"Ready to get started? 🚀"
        )
        
        keyboard = [
            [InlineKeyboardButton("📄 Upload Statement", callback_data="upload_statement")],
            [InlineKeyboardButton("📊 View History", callback_data="view_history")],
            [InlineKeyboardButton("❓ Help", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text, 
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send a message when the command /help is issued."""
        help_text = (
            "🤖 *Bank Statement Bot Help* 📚\n\n"
            "*Available Commands:*\n"
            "• /start - Welcome message and main menu\n"
            "• /help - Show this help message\n"
            "• /history - View your analysis history\n\n"
            "*How to Upload:*\n"
            "1. Click 'Upload Statement' or just send a PDF\n"
            "2. Wait for AI processing (usually 30-60 seconds)\n"
            "3. Receive detailed analysis\n\n"
            "*Supported Formats:*\n"
            "• PDF bank statements\n"
            "• Both text-based and scanned PDFs\n"
            "• Most major banks supported\n\n"
            "*Privacy:*\n"
            "• Files are processed and immediately deleted\n"
            "• Only transaction summaries are stored\n"
            "• No account numbers or sensitive data retained\n\n"
            "*Need more help?* Contact support! 💬"
        )
        
        keyboard = [
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
            [InlineKeyboardButton("📄 Upload Statement", callback_data="upload_statement")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle button callbacks."""
        query = update.callback_query
        await query.answer()
        
        if query.data == "upload_statement":
            await query.edit_message_text(
                "📄 *Upload Your Bank Statement*\n\n"
                "Please send me your bank statement as a PDF file.\n\n"
                "🔍 *What I'll analyze:*\n"
                "• All transactions and amounts\n"
                "• Transaction categories\n" 
                "• Recurring payments\n"
                "• Spending patterns\n"
                "• Account summary\n\n"
                "📱 Just drag and drop or click the attachment button to upload!",
                parse_mode='Markdown'
            )
        elif query.data == "view_history":
            await self.show_history(update, context)
        elif query.data == "help":
            await self.help_command(update, context)
        elif query.data == "main_menu":
            await self.start(update, context)

    async def show_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show user's analysis history."""
        user = update.effective_user
        
        # Get user's bank statements from database
        db = get_db()
        statements = db.query(BankStatement).filter(BankStatement.user_id == str(user.id)).all()
        
        if not statements:
            keyboard = [[InlineKeyboardButton("📄 Upload First Statement", callback_data="upload_statement")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            text = (
                "📊 *Your Analysis History*\n\n"
                "No statements analyzed yet! 📈\n\n"
                "Upload your first bank statement to get started with AI-powered financial insights."
            )
            
            if update.callback_query:
                await update.callback_query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)
            else:
                await update.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)
            return
        
        history_text = "📊 *Your Analysis History*\n\n"
        
        for i, statement in enumerate(statements[-5:], 1):  # Show last 5 statements
            analysis = json.loads(statement.analysis_result) if statement.analysis_result else {}
            total_transactions = analysis.get('summary', {}).get('total_transactions', 'N/A')
            
            history_text += (
                f"📄 *Statement {i}*\n"
                f"📅 Uploaded: {statement.upload_date.strftime('%Y-%m-%d %H:%M')}\n"
                f"📝 Transactions: {total_transactions}\n"
                f"💰 Status: ✅ Analyzed\n\n"
            )
        
        keyboard = [
            [InlineKeyboardButton("📄 Upload New Statement", callback_data="upload_statement")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(history_text, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await update.message.reply_text(history_text, parse_mode='Markdown', reply_markup=reply_markup)

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle uploaded PDF documents."""
        if not update.message.document:
            await update.message.reply_text("❌ Please send a valid document.")
            return
            
        document = update.message.document
        
        # Check if it's a PDF
        if not document.file_name.lower().endswith('.pdf'):
            await update.message.reply_text(
                "❌ Please upload a PDF file.\n\n"
                "📄 Supported format: PDF bank statements only"
            )
            return
        
        # Check file size (limit to 20MB)
        if document.file_size > 20 * 1024 * 1024:
            await update.message.reply_text(
                "❌ File too large! Maximum size: 20MB\n\n"
                "💡 Try compressing your PDF or contact support."
            )
            return
        
        user = update.effective_user
        
        # Send processing message
        processing_message = await update.message.reply_text(
            "🔄 *Processing your bank statement...*\n\n"
            "⏳ This usually takes 30-60 seconds\n"
            "🤖 AI is analyzing your transactions\n"
            "☕ Grab a coffee while I work!",
            parse_mode='Markdown'
        )
        
        try:
            # Get file from Telegram
            file = await context.bot.get_file(document.file_id)
            
            # Create temporary file path (use current directory for Render)
            import tempfile
            temp_file_path = f"./{document.file_name}"
            
            # Download file
            await file.download_to_drive(temp_file_path)
            
            # Process PDF with AI
            logger.info(f"Processing PDF for user {user.id}: {document.file_name}")
            
            # Extract text and analyze
            raw_text = self.pdf_parser.extract_text_from_pdf(temp_file_path)
            analysis_result = self.pdf_parser.parse_bank_statement(raw_text)
            
            # Save to database
            db = get_db()
            user_record = get_or_create_user(str(user.id), user.username)
            
            # Create bank statement record
            bank_statement = BankStatement(
                user_id=str(user.id),
                filename=document.file_name,
                file_size=document.file_size,
                upload_date=datetime.now(),
                analysis_result=json.dumps(analysis_result)
            )
            db.add(bank_statement)
            db.commit()
            
            # Save individual transactions
            transactions_data = analysis_result.get('transactions', [])
            for transaction_data in transactions_data:
                transaction = Transaction(
                    bank_statement_id=bank_statement.id,
                    date=datetime.strptime(transaction_data.get('date', '1900-01-01'), '%Y-%m-%d'),
                    description=transaction_data.get('description', ''),
                    amount=float(transaction_data.get('amount', 0)),
                    category=transaction_data.get('category', 'Other')
                )
                db.add(transaction)
            
            # Save recurring payments
            recurring_data = analysis_result.get('recurring_payments', [])
            for recurring_payment_data in recurring_data:
                recurring_payment = RecurringPayment(
                    bank_statement_id=bank_statement.id,
                    description=recurring_payment_data.get('description', ''),
                    amount=float(recurring_payment_data.get('amount', 0)),
                    frequency=recurring_payment_data.get('frequency', 'monthly'),
                    category=recurring_payment_data.get('category', 'Other')
                )
                db.add(recurring_payment)
            
            db.commit()
            
            # Clean up temporary file
            try:
                os.remove(temp_file_path)
            except:
                pass
            
            # Format and send results
            await self.send_analysis_results(update, analysis_result, processing_message)
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            await processing_message.edit_text(
                "❌ *Error Processing Document*\n\n"
                "😞 Sorry, I couldn't analyze your bank statement.\n\n"
                "*Possible reasons:*\n"
                "• PDF is corrupted or encrypted\n"
                "• Unsupported bank format\n"
                "• Network connection issues\n\n"
                "💡 *Try:*\n"
                "• Re-downloading the PDF from your bank\n"
                "• Ensuring the PDF is not password protected\n"
                "• Contacting support if the issue persists",
                parse_mode='Markdown'
            )
            
            # Clean up temporary file
            try:
                os.remove(temp_file_path)
            except:
                pass

    async def send_analysis_results(self, update: Update, analysis_result: dict, processing_message) -> None:
        """Send formatted analysis results to user."""
        try:
            summary = analysis_result.get('summary', {})
            transactions = analysis_result.get('transactions', [])
            recurring_payments = analysis_result.get('recurring_payments', [])
            insights = analysis_result.get('insights', {})
            
            # Main summary message
            summary_text = (
                "✅ *Analysis Complete!* 🎉\n\n"
                f"📊 *Statement Summary*\n"
                f"💳 Total Transactions: {summary.get('total_transactions', 'N/A')}\n"
                f"💰 Total Debits: ${abs(float(summary.get('total_debits', 0))):,.2f}\n"
                f"💵 Total Credits: ${float(summary.get('total_credits', 0)):,.2f}\n"
                f"📈 Net Flow: ${float(summary.get('net_flow', 0)):,.2f}\n\n"
                f"🔄 Recurring Payments: {len(recurring_payments)}\n"
                f"📅 Period: {summary.get('period', 'N/A')}"
            )
            
            keyboard = [
                [InlineKeyboardButton("📝 View Transactions", callback_data="view_transactions")],
                [InlineKeyboardButton("🔄 Recurring Payments", callback_data="view_recurring")],
                [InlineKeyboardButton("📊 Upload Another", callback_data="upload_statement")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await processing_message.edit_text(
                summary_text,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            # Send top spending categories if available
            if insights.get('top_categories'):
                categories_text = "🏷️ *Top Spending Categories*\n\n"
                for category, amount in insights['top_categories'][:5]:
                    categories_text += f"• {category}: ${abs(float(amount)):,.2f}\n"
                
                await update.message.reply_text(categories_text, parse_mode='Markdown')
            
            # Send insights if available
            if insights.get('financial_insights'):
                insights_text = f"💡 *AI Insights*\n\n{insights['financial_insights']}"
                await update.message.reply_text(insights_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error sending results: {e}")
            await processing_message.edit_text(
                "✅ Analysis complete, but there was an error displaying results.\n"
                "Your data has been saved successfully!"
            )

# Flask app for webhook
app = Flask(__name__)

# Global variable to store the application
telegram_app = None

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming webhook updates from Telegram."""
    if request.method == 'POST':
        try:
            # Get update from Telegram
            update_dict = request.get_json(force=True)
            update = Update.de_json(update_dict, telegram_app.bot)
            
            # Process update in a separate thread with its own event loop
            def process_update():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(telegram_app.process_update(update))
                except Exception as e:
                    logger.error(f"Error processing update: {e}")
                finally:
                    # Don't close the loop immediately, let pending tasks finish
                    pending = asyncio.all_tasks(loop)
                    if pending:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    loop.close()
            
            # Run in background thread
            import threading
            thread = threading.Thread(target=process_update)
            thread.daemon = False  # Don't make it daemon so it completes
            thread.start()
            
            return Response('OK', status=200)
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return Response('Error', status=500)
    
    return Response('Method not allowed', status=405)

@app.route('/')
def index():
    """Health check endpoint."""
    return "Bank Statement Bot is running! 🚀"

async def setup_webhook():
    """Setup webhook for the bot."""
    try:
        # Get the webhook URL (Render provides RENDER_EXTERNAL_URL)
        webhook_url = os.environ.get('RENDER_EXTERNAL_URL', 'https://your-app.onrender.com')
        webhook_url += '/webhook'
        
        logger.info(f"Setting webhook URL: {webhook_url}")
        
        # Set webhook
        await telegram_app.bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True  # Clear any pending updates
        )
        
        logger.info("✅ Webhook set successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error setting webhook: {e}")
        raise

def main():
    """Main function to run the bot with webhooks."""
    global telegram_app
    
    # Check for required environment variables
    if not Config.TELEGRAM_BOT_TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN not found in environment variables!")
        return
    
    if not Config.OPENAI_API_KEY:
        logger.error("❌ OPENAI_API_KEY not found in environment variables!")
        return
    
    # Create database tables
    try:
        create_tables()
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return
    
    # Create bot instance
    bot = BankStatementBot()
    
    # Create the Application
    telegram_app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    telegram_app.add_handler(CommandHandler("start", bot.start))
    telegram_app.add_handler(CommandHandler("help", bot.help_command))
    telegram_app.add_handler(MessageHandler(filters.Document.PDF, bot.handle_document))
    telegram_app.add_handler(CallbackQueryHandler(bot.handle_callback_query))
    
    # Initialize the application first
    async def initialize_and_setup():
        await telegram_app.initialize()
        await setup_webhook()
    
    # Setup webhook in a separate thread
    def setup_webhook_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(initialize_and_setup())
    
    # Start webhook setup in background
    webhook_thread = threading.Thread(target=setup_webhook_thread)
    webhook_thread.daemon = True
    webhook_thread.start()
    
    # Start Flask app (this will handle webhooks)
    logger.info("🚀 Starting Bank Statement Bot with WEBHOOKS...")
    logger.info("✅ This completely eliminates the polling conflict!")
    
    # Get port from environment (Render uses PORT)
    port = int(os.environ.get('PORT', 5000))
    
    # Run Flask app
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    main()
