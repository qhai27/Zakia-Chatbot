"""
Enhanced Zakat Calculator Routes for ZAKIA Chatbot
Handles zakat calculation with year selection
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
    Calculate zakat based on type and inputs with year selection
    
    Expected JSON input:
    {
        "type": "income|savings",
        "amount": number,
        "expenses": number (for income only),
        "year": string (e.g., "1447" or "2024"),
        "year_type": string ("H" or "M")
    }
    """
    try:
        data = request.json
        zakat_type = data.get('type', '').lower()
        year = data.get('year', '1447')
        year_type = data.get('year_type', 'H')
        
        if not zakat_type:
            return jsonify({
                'success': False,
                'error': 'Sila nyatakan jenis zakat (income atau savings)'
            }), 400
        
        if not year:
            return jsonify({
                'success': False,
                'error': 'Sila pilih tahun untuk pengiraan'
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
            
            result = calculator.calculate_income_zakat(amount, expenses, year, year_type)
            
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
            
            result = calculator.calculate_savings_zakat(amount, year, year_type)
            
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
                'error': 'Jenis zakat tidak sah. Gunakan: income atau savings'
            }), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Ralat sistem: {str(e)}'
        }), 500

@zakat_bp.route("/zakat/nisab-info", methods=["GET"])
def get_nisab_info():
    """Get nisab values for specific year"""
    try:
        year = request.args.get('year', '1447')
        year_type = request.args.get('type', 'H')
        
        result = calculator.get_nisab_info(year, year_type)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Ralat sistem: {str(e)}'
        }), 500

@zakat_bp.route("/zakat/years", methods=["GET"])
def get_available_years():
    """Get available years for zakat calculation"""
    try:
        year_type = request.args.get('type', 'H')
        
        result = calculator.fetch_available_years(year_type)
        
        if result['success']:
            # Extract years from API response
            years_data = result.get('years', [])
            
            # Handle different response formats
            if isinstance(years_data, list):
                # If it's already a list, use it
                years = years_data
            elif isinstance(years_data, dict):
                # If it's a dict, extract years from it
                years = list(years_data.keys()) if years_data else []
            else:
                # Fallback to default years
                years = ['1447', '1446', '1445', '1444', '1443'] if year_type == 'H' else ['2024', '2023', '2022', '2021', '2020']
            
            return jsonify({
                'success': True,
                'years': years,
                'year_type': 'Hijrah' if year_type == 'H' else 'Masihi'
            })
        else:
            # Return default years on error
            default_years = ['1447', '1446', '1445', '1444', '1443'] if year_type == 'H' else ['2024', '2023', '2022', '2021', '2020']
            return jsonify({
                'success': True,
                'years': default_years,
                'year_type': 'Hijrah' if year_type == 'H' else 'Masihi',
                'fallback': True
            })
    
    except Exception as e:
        # Return default years on exception
        year_type = request.args.get('type', 'H')
        default_years = ['1447', '1446', '1445', '1444', '1443'] if year_type == 'H' else ['2024', '2023', '2022', '2021', '2020']
        return jsonify({
            'success': True,
            'years': default_years,
            'year_type': 'Hijrah' if year_type == 'H' else 'Masihi',
            'fallback': True,
            'error': str(e)
        })

@zakat_bp.route("/zakat/help", methods=["GET"])
def get_zakat_help():
    """Get help information for zakat calculator"""
    help_message = (
        "💡 **Panduan Kalkulator Zakat**\n\n"
        "**Jenis Zakat yang boleh dikira:**\n\n"
        "1️⃣ **Zakat Pendapatan**\n"
        "   • Berdasarkan pendapatan tahunan\n"
        "   • Tolak perbelanjaan asas\n"
        "   • Pilih tahun Hijrah atau Masihi\n\n"
        "2️⃣ **Zakat Simpanan**\n"
        "   • Berdasarkan simpanan/wang tunai\n"
        "   • Pilih tahun Hijrah atau Masihi\n\n"
        "**Cara menggunakan:**\n"
        "1. Taip 'kira zakat' untuk mula\n"
        "2. Pilih jenis zakat\n"
        "3. Pilih jenis tahun (Hijrah/Masihi)\n"
        "4. Pilih tahun\n"
        "5. Masukkan jumlah mengikut arahan\n\n"
        "Untuk maklumat nisab, taip 'nisab'"
    )
    
    return jsonify({
        'success': True,
        'reply': help_message
    })