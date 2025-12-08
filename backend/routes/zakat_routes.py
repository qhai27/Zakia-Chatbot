from flask import Blueprint, request, jsonify
from zakat_calculator import ZakatCalculator

zakat_bp = Blueprint('zakat', __name__)
calculator = ZakatCalculator()


@zakat_bp.route("/api/calculate-zakat", methods=["POST"])
def calculate_zakat():
    """Calculate zakat based on type (income_kaedah_a, income_kaedah_b, or savings)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Tiada data diterima'
            }), 400
        
        zakat_type = data.get('type', '').lower()
        year = data.get('year', '1447')
        year_type = data.get('year_type', 'H')
        
        # Validate required fields
        if not zakat_type:
            return jsonify({
                'success': False,
                'error': 'Jenis zakat tidak dinyatakan'
            }), 400
        
        if not year:
            return jsonify({
                'success': False,
                'error': 'Tahun tidak dinyatakan'
            }), 400
        
        # Route to appropriate calculation method
        result = None
        
        if zakat_type == 'income_kaedah_a':
            gross_income = data.get('gross_income')
            
            if gross_income is None:
                return jsonify({
                    'success': False,
                    'error': 'Pendapatan kasar tidak dinyatakan'
                }), 400
            
            try:
                gross_income = float(gross_income)
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'Nilai pendapatan tidak sah'
                }), 400
            
            result = calculator.calculate_income_zakat_kaedah_a(
                gross_income=gross_income,
                year=str(year),
                year_type=year_type
            )
            
        elif zakat_type == 'income_kaedah_b':
            annual_income = data.get('annual_income')
            annual_expenses = data.get('annual_expenses')
            
            if annual_income is None or annual_expenses is None:
                return jsonify({
                    'success': False,
                    'error': 'Pendapatan atau perbelanjaan tidak dinyatakan'
                }), 400
            
            try:
                annual_income = float(annual_income)
                annual_expenses = float(annual_expenses)
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'Nilai pendapatan atau perbelanjaan tidak sah'
                }), 400
            
            result = calculator.calculate_income_zakat_kaedah_b(
                annual_income=annual_income,
                annual_expenses=annual_expenses,
                year=str(year),
                year_type=year_type
            )
            
        elif zakat_type == 'income':
            # Legacy support for old 'income' type (treats as Kaedah B)
            annual_income = data.get('amount')
            annual_expenses = data.get('expenses', 0)
            
            if annual_income is None:
                return jsonify({
                    'success': False,
                    'error': 'Jumlah pendapatan tidak dinyatakan'
                }), 400
            
            try:
                annual_income = float(annual_income)
                annual_expenses = float(annual_expenses)
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'Nilai tidak sah'
                }), 400
            
            result = calculator.calculate_income_zakat_kaedah_b(
                annual_income=annual_income,
                annual_expenses=annual_expenses,
                year=str(year),
                year_type=year_type
            )
            
        elif zakat_type == 'savings':
            savings_amount = data.get('savings_amount')
            
            # Fallback to 'amount' for backward compatibility
            if savings_amount is None:
                savings_amount = data.get('amount')
            
            if savings_amount is None:
                return jsonify({
                    'success': False,
                    'error': 'Jumlah simpanan tidak dinyatakan'
                }), 400
            
            try:
                savings_amount = float(savings_amount)
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'Nilai simpanan tidak sah'
                }), 400
            
            result = calculator.calculate_savings_zakat(
                savings_amount=savings_amount,
                year=str(year),
                year_type=year_type
            )
            
        else:
            return jsonify({
                'success': False,
                'error': f'Jenis zakat tidak sah: {zakat_type}'
            }), 400
        
        # Check if calculation was successful
        if not result or not result.get('success'):
            return jsonify({
                'success': False,
                'error': result.get('error', 'Ralat pengiraan') if result else 'Ralat pengiraan'
            }), 400
        
        # Return successful result
        return jsonify({
            'success': True,
            'reply': result.get('message', ''),
            'data': {
                'zakat_amount': result.get('zakat_amount', 0),
                'zakatable_amount': result.get('zakatable_amount', 0),
                'reaches_nisab': result.get('reaches_nisab', False),
                'nisab_value': result.get('nisab_value', 0),
                'type': result.get('type', zakat_type),
                'year': result.get('year', year),
                'year_type': result.get('year_type', year_type),
                'details': result.get('details', {})
            }
        }), 200
        
    except Exception as e:
        print(f"Error in calculate_zakat route: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Ralat sistem. Sila cuba lagi.'
        }), 500


@zakat_bp.route("/api/zakat/nisab-info", methods=["GET"])
def nisab_info():
    """Get nisab information for a specific year"""
    try:
        year = request.args.get('year', '1447')
        year_type = request.args.get('type', 'H')
        
        if not year:
            return jsonify({
                'success': False,
                'error': 'Tahun tidak dinyatakan'
            }), 400
        
        result = calculator.get_nisab_info(year=str(year), year_type=year_type)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'reply': result.get('reply', ''),
                'data': result.get('data', {})
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Gagal mendapatkan maklumat nisab')
            }), 500
            
    except Exception as e:
        print(f"Error in nisab_info: {e}")
        return jsonify({
            'success': False,
            'error': 'Ralat sistem'
        }), 500


@zakat_bp.route('/api/zakat/years', methods=['GET'])
def get_years():
    """
    GET /api/zakat/years?type=H
    Returns list of years for Hijrah (H) or Masihi (M)
    """
    try:
        year_type = (request.args.get('type') or 'H').upper()
        
        if year_type not in ('H', 'M'):
            return jsonify({
                'success': False,
                'error': 'Invalid type parameter. Use H or M.'
            }), 400

        result = calculator.fetch_available_years(year_type)
        
        # result may not include 'year_type' key — be defensive
        years = result.get('years') if isinstance(result, dict) else None
        years = years or []
        year_type_label = 'Hijrah' if year_type == 'H' else 'Masihi'

        return jsonify({
            'success': bool(result.get('success', True)),
            'years': years,
            'year_type': year_type_label,
            'raw': result.get('raw') if isinstance(result, dict) else None,
            'error': result.get('error') if isinstance(result, dict) else None
        }), 200
        
    except Exception as e:
        print(f"Error in get_years: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500