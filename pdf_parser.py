import openai
import json
import base64
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pdf2image import convert_from_path
from PIL import Image

from config import Config

# Initialize OpenAI client
openai.api_key = Config.OPENAI_API_KEY

@dataclass
class ParsedTransaction:
    date: datetime
    description: str
    amount: float
    balance: Optional[float] = None
    category: Optional[str] = None

class PDFParser:
    def __init__(self):
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
    
    def convert_pdf_to_images(self, pdf_path: str) -> List[Image.Image]:
        """Convert PDF pages to images for OpenAI Vision processing"""
        try:
            # Convert PDF to images (300 DPI for good quality)
            images = convert_from_path(pdf_path, dpi=300)
            return images
        except Exception as e:
            raise Exception(f"Error converting PDF to images: {str(e)}")
    
    def encode_image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string for OpenAI API"""
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def analyze_page_with_vision(self, image: Image.Image, page_num: int) -> str:
        """Use OpenAI Vision to analyze a single page"""
        try:
            base64_image = self.encode_image_to_base64(image)
            
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Use GPT-4 with vision
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text", 
                                "text": f"""This is page {page_num} of a bank statement. Please extract ALL text content from this page exactly as it appears. 
                                
Pay special attention to:
- Account activity sections starting with "ACCOUNT ACTIVITY"
- Transaction data with columns: date, merchant/description, amount
- Any line starting with "TOTAL interest for this period"
                                
Please provide the complete text content of this page."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4000,
                temperature=0.1
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Error analyzing page {page_num} with OpenAI Vision: {str(e)}")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using OpenAI Vision API"""
        try:
            # Convert PDF to images
            images = self.convert_pdf_to_images(pdf_path)
            
            if not images:
                raise Exception("No pages found in PDF")
            
            # Analyze each page with OpenAI Vision
            all_text = ""
            for i, image in enumerate(images, 1):
                page_text = self.analyze_page_with_vision(image, i)
                all_text += f"\n=== PAGE {i} ===\n{page_text}\n"
            
            return all_text.strip()
            
        except Exception as e:
            error_msg = str(e)
            if "poppler" in error_msg.lower():
                raise Exception("PDF processing error: poppler-utils not installed. Please contact support.")
            else:
                raise Exception(f"Error processing PDF with OpenAI Vision: {error_msg}")
    
    def parse_bank_statement(self, raw_text: str) -> Dict[str, Any]:
        """Use OpenAI to parse bank statement and extract transactions"""
        
        system_prompt = """
        You are a specialized bank statement parser. Extract transaction data from the provided bank statement text.
        
        IMPORTANT: Focus on data starting from page 3 with the line "ACCOUNT ACTIVITY".
        
        Transaction format to look for:
        - Each transaction has: date of transaction, merchant name/transaction description, $ amount
        - Transactions are listed line by line after "ACCOUNT ACTIVITY"
        - Stop processing when you reach a line starting with "TOTAL interest for this period"
        
        For each transaction, extract:
        - date (convert to YYYY-MM-DD format)
        - description (merchant name or transaction description exactly as shown)
        - amount (negative for debits/expenses, positive for credits/deposits)
        - category (categorize based on merchant: groceries, gas, dining, utilities, etc.)
        
        Return JSON in this exact format:
        {
            "account_info": {
                "account_number": "masked account number if found",
                "bank_name": "bank name if identifiable", 
                "statement_period": "date range if found"
            },
            "transactions": [
                {
                    "date": "2024-01-15",
                    "description": "MERCHANT NAME OR DESCRIPTION",
                    "amount": -45.67,
                    "category": "groceries"
                }
            ]
        }
        
        Rules:
        - Only extract transactions from the ACCOUNT ACTIVITY section starting from page 3
        - Stop at "TOTAL interest for this period"
        - Include ALL transactions found in that section
        - Use negative amounts for expenses/debits, positive for deposits/credits
        """
        
        user_prompt = f"""
        Parse this bank statement and extract all transactions:
        
        {raw_text}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Use GPT-4o for better understanding
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content
            
            # Clean the response to extract JSON
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = content[json_start:json_end]
                parsed_data = json.loads(json_str)
                return parsed_data
            else:
                raise Exception("No valid JSON found in OpenAI response")
                
        except Exception as e:
            raise Exception(f"Error parsing with OpenAI: {str(e)}")
    
    def analyze_recurring_payments(self, transactions: List[Dict]) -> Dict[str, Any]:
        """Analyze transactions to identify recurring payments"""
        
        # Prepare transaction data for analysis
        transaction_text = json.dumps(transactions, indent=2)
        
        system_prompt = """
        You are a financial analyst. Analyze bank transactions to identify recurring payments.
        
        Look for:
        - Similar merchant names or descriptions that appear multiple times
        - Regular payment amounts (exact or similar)
        - Consistent timing patterns (monthly, weekly, etc.)
        
        Group similar transactions and identify recurring patterns.
        
        Return JSON in this format:
        {
            "recurring_payments": [
                {
                    "merchant_name": "Netflix",
                    "category": "entertainment",
                    "average_amount": -15.99,
                    "frequency": "monthly",
                    "occurrences": 3,
                    "last_payment_date": "2024-01-15",
                    "confidence": "high"
                }
            ],
            "summary": {
                "total_recurring_amount": -150.50,
                "recurring_payment_count": 5,
                "largest_recurring_payment": "Rent - $1200.00"
            }
        }
        """
        
        user_prompt = f"""
        Analyze these transactions for recurring patterns:
        
        {transaction_text}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=3000
            )
            
            content = response.choices[0].message.content
            
            # Extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = content[json_start:json_end]
                analysis = json.loads(json_str)
                return analysis
            else:
                raise Exception("No valid JSON found in recurring payment analysis")
                
        except Exception as e:
            raise Exception(f"Error analyzing recurring payments: {str(e)}")
    
    def format_summary_message(self, analysis: Dict[str, Any]) -> str:
        """Format the recurring payments analysis into a readable message"""
        
        summary = analysis.get('summary', {})
        recurring_payments = analysis.get('recurring_payments', [])
        
        message = "📊 **Recurring Payments Summary**\n\n"
        
        # Overall summary
        message += f"💰 Total monthly recurring: ${abs(summary.get('total_recurring_amount', 0)):.2f}\n"
        message += f"📋 Number of recurring payments: {summary.get('recurring_payment_count', 0)}\n"
        
        if summary.get('largest_recurring_payment'):
            message += f"🏆 Largest payment: {summary.get('largest_recurring_payment')}\n"
        
        message += "\n" + "="*30 + "\n\n"
        
        # Individual recurring payments
        if recurring_payments:
            message += "📝 **Detailed Breakdown:**\n\n"
            
            for payment in recurring_payments:
                merchant = payment.get('merchant_name', 'Unknown')
                amount = abs(payment.get('average_amount', 0))
                frequency = payment.get('frequency', 'unknown')
                category = payment.get('category', 'uncategorized')
                occurrences = payment.get('occurrences', 0)
                
                # Category emoji
                category_emoji = {
                    'utilities': '⚡',
                    'entertainment': '🎬',
                    'groceries': '🛒',
                    'transport': '🚗',
                    'insurance': '🛡️',
                    'subscription': '📱',
                    'rent': '🏠',
                    'dining': '🍽️'
                }.get(category.lower(), '💳')
                
                message += f"{category_emoji} **{merchant}**\n"
                message += f"   Amount: ${amount:.2f} ({frequency})\n"
                message += f"   Category: {category.title()}\n"
                message += f"   Occurrences: {occurrences}\n\n"
        
        else:
            message += "No recurring payments detected in this statement.\n"
        
        return message
