"""
Zakat Calculator Routes for ZAKIA Chatbot
Handles zakat calculation endpoints
"""

from flask import Blueprint, request, jsonify
import sys
import os

# Add parent directory to path to import zakat_calculator
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from zakat_calculator import ZakatCalculator

# Create blueprint
zakat_bp = Blueprint('zakat', __name__)

# Initialize calculator
calculator = ZakatCalculator()

@zakat_bp.route("/calculate-zakat", methods=["POST"])
def calculate_zakat():
    """
    Calculate zakat based on type and inputs
    
    Expected JSON input:
    {
        "type": "income|savings|gold",
        "amount": number,
        "expenses": number (for income only),
        "gold_price": number (for gold, optional)
    }
    """
    try:
        data = request.json
        zakat_type = data.get('type', '').lower()
        
        if not zakat_type:
            return jsonify({
                'success': False,
                'error': 'Sila nyatakan jenis zakat (income, savings, atau gold)'
            }), 400
        
        # Income zakat calculation
        if zakat_type == 'income':
            amount = data.get('amount')
            expenses = data.get('expenses')
            
            if amount is None or expenses is None:
                return jsonify({
                    'success': False,
                    'error': 'Sila masukkan jumlah pendapatan dan perbelanjaan'
                }), 400
            
            result = calculator.calculate_income_zakat(amount, expenses)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'reply': result['message'],
                    'data': result
                })
            else:
                return jsonify(result), 400
        
        # Savings zakat calculation
        elif zakat_type == 'savings':
            amount = data.get('amount')
            
            if amount is None:
                return jsonify({
                    'success': False,
                    'error': 'Sila masukkan jumlah simpanan'
                }), 400
            
            result = calculator.calculate_savings_zakat(amount)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'reply': result['message'],
                    'data': result
                })
            else:
                return jsonify(result), 400
        
        # Gold zakat calculation
        elif zakat_type == 'gold':
            amount = data.get('amount')  # weight in grams
            gold_price = data.get('gold_price')  # optional
            
            if amount is None:
                return jsonify({
                    'success': False,
                    'error': 'Sila masukkan berat emas (dalam gram)'
                }), 400
            
            result = calculator.calculate_gold_zakat(amount, gold_price)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'reply': result['message'],
                    'data': result
                })
            else:
                return jsonify(result), 400
        
        else:
            return jsonify({
                'success': False,
                'error': 'Jenis zakat tidak sah. Gunakan: income, savings, atau gold'
            }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Ralat sistem: {str(e)}'
        }), 500

@zakat_bp.route("/zakat/nisab-info", methods=["GET"])
def get_nisab_info():
    """Get current nisab values and rates"""
    try:
        info = calculator.get_nisab_info()
        
        message = (
            f"📊 **Maklumat Nisab Semasa**\n\n"
            f"**Nisab Pendapatan/Simpanan:**\n"
            f"• RM{info['income']:,.2f} setahun\n\n"
            f"**Nisab Emas:**\n"
            f"• {info['gold_grams']}g emas\n"
            f"• Nilai semasa: RM{info['gold_value']:,.2f}\n"
            f"• Harga emas: RM{info['gold_price_per_gram']:,.2f}/g\n\n"
            f"**Kadar Zakat:**\n"
            f"• {info['zakat_rate'] * 100}% (2.5%)"
        )
        
        return jsonify({
            'success': True,
            'reply': message,
            'data': info
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Ralat sistem: {str(e)}'
        }), 500

@zakat_bp.route("/zakat/help", methods=["GET"])
def get_zakat_help():
    """Get help information for zakat calculator"""
    help_message = (
        "💡 **Panduan Kalkulator Zakat**\n\n"
        "**Jenis Zakat yang boleh dikira:**\n\n"
        "1️⃣ **Zakat Pendapatan**\n"
        "   • Berdasarkan pendapatan tahunan\n"
        "   • Tolak perbelanjaan asas\n"
        "   • Nisab: RM22,000\n\n"
        "2️⃣ **Zakat Simpanan**\n"
        "   • Berdasarkan simpanan/wang tunai\n"
        "   • Nisab: RM22,000\n\n"
        "3️⃣ **Zakat Emas**\n"
        "   • Berdasarkan berat emas (gram)\n"
        "   • Nisab: 85 gram\n\n"
        "**Cara menggunakan:**\n"
        "Taip 'kira zakat pendapatan', 'kira zakat simpanan', atau 'kira zakat emas'\n\n"
        "Untuk maklumat nisab, taip 'nisab'"
    )
    
    return jsonify({
        'success': True,
        'reply': help_message
    })