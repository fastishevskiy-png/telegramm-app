import PyPDF2
import openai
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

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
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                return text.strip()
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    def parse_bank_statement(self, raw_text: str) -> Dict[str, Any]:
        """Use OpenAI to parse bank statement and extract transactions"""
        
        system_prompt = """
        You are a bank statement parser. Extract transaction data from bank statements and return structured JSON.
        
        For each transaction, extract:
        - date (YYYY-MM-DD format)
        - description (clean merchant/transaction description)
        - amount (negative for debits, positive for credits)
        - balance (if available)
        - category (guess based on description: groceries, utilities, entertainment, transport, etc.)
        
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
                    "description": "GROCERY STORE PURCHASE",
                    "amount": -45.67,
                    "balance": 1234.56,
                    "category": "groceries"
                }
            ]
        }
        
        Only include actual transactions, not headers or summary information.
        """
        
        user_prompt = f"""
        Parse this bank statement and extract all transactions:
        
        {raw_text}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
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
