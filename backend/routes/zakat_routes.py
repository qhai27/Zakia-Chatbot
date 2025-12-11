"""
Zakat Routes - Handles API endpoints for zakat calculations
"""

from flask import Blueprint, request, jsonify, current_app
from zakat_calculator import ZakatCalculator

# Create blueprint - export as zakat_bp for app.py compatibility
zakat_bp = Blueprint('zakat', __name__)
zakat_extended_bp = zakat_bp  # Alias for backward compatibility
calculator = ZakatCalculator()


@zakat_bp.route("/api/calculate-zakat", methods=["POST"])
def calculate_zakat():
    """Main zakat calculation endpoint for income and savings"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Tiada data diterima'
            }), 400
        
        zakat_type = data.get('type')
        year = data.get('year', '1447')
        year_type = data.get('year_type', 'H')
        
        result = None
        
        # Handle different zakat types
        if zakat_type == 'income_kaedah_a':
            gross_income = data.get('gross_income')
            if gross_income is None:
                return jsonify({
                    'success': False,
                    'error': 'Jumlah pendapatan kasar diperlukan'
                }), 400
            try:
                gross_income = float(gross_income)
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'Nilai tidak sah'
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
                    'error': 'Jumlah pendapatan dan perbelanjaan diperlukan'
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
            if savings_amount is None:
                return jsonify({
                    'success': False,
                    'error': 'Jumlah simpanan diperlukan'
                }), 400
            try:
                savings_amount = float(savings_amount)
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'Nilai tidak sah'
                }), 400
            
            result = calculator.calculate_savings_zakat(
                savings_amount=savings_amount,
                year=str(year),
                year_type=year_type
            )
        else:
            return jsonify({
                'success': False,
                'error': f'Jenis zakat tidak dikenali: {zakat_type}'
            }), 400
        
        if not result or not result.get('success'):
            return jsonify({
                'success': False,
                'error': result.get('error', 'Ralat pengiraan') if result else 'Ralat pengiraan'
            }), 400
        
        return jsonify({
            'success': True,
            'reply': result.get('message', ''),
            'data': {
                'zakat_amount': result.get('zakat_amount', 0),
                'zakatable_amount': result.get('zakatable_amount', 0),
                'reaches_nisab': result.get('reaches_nisab', False),
                'nisab_value': result.get('nisab_value', 0),
                'type': zakat_type,
                'year': result.get('year', year),
                'year_type': result.get('year_type', year_type),
                'details': result.get('details', {})
            }
        }), 200
        
    except Exception as e:
        print(f"Error in calculate_zakat: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Ralat sistem. Sila cuba lagi.'
        }), 500


# Both endpoint patterns supported
@zakat_bp.route('/zakat-calculator/padi', methods=['POST'])
def calculate_padi_zakat_api():
    """Calculate zakat for padi (accepts jumlah_rm in RM)"""
    try:
        payload = request.get_json() or {}
        jumlah_rm = float(payload.get('jumlah_rm') or 0)
        year = payload.get('year', '')
        year_type = payload.get('year_type', 'M')

        if jumlah_rm <= 0:
            return jsonify({
                'success': False,
                'error': 'Jumlah hasil diperlukan dan mesti lebih daripada 0'
            }), 400

        calc = ZakatCalculator()
        result = calc.calculate_padi_zakat(jumlah_rm, year, year_type)

        if result['success']:
            return jsonify({
                'success': True,
                'reply': result['message'],
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Ralat pengiraan')
            }), 400

    except Exception as e:
        current_app.logger.exception("calculate_padi_zakat_api error")
        return jsonify({'success': False, 'error': str(e)}), 500


# Both endpoint patterns supported
@zakat_bp.route("/zakat-calculator/saham", methods=["POST"])
@zakat_extended_bp.route("/api/calculate-zakat-saham", methods=["POST"])
def calculate_zakat_saham():
    """Calculate zakat for saham (shares/stocks)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Tiada data diterima'
            }), 400
        
        # Get inputs
        nilai_portfolio = data.get('nilai_portfolio')
        hutang_saham = data.get('hutang_saham', 0)
        year = data.get('year', '1447')
        year_type = data.get('year_type', 'H')
        
        # Validate
        if nilai_portfolio is None:
            return jsonify({
                'success': False,
                'error': 'Nilai portfolio diperlukan'
            }), 400
        
        try:
            nilai_portfolio = float(nilai_portfolio)
            hutang_saham = float(hutang_saham)
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Nilai tidak sah'
            }), 400
        
        # Calculate
        result = calculator.calculate_saham_zakat(
            nilai_portfolio=nilai_portfolio,
            hutang_saham=hutang_saham,
            year=str(year),
            year_type=year_type
        )
        
        if not result or not result.get('success'):
            return jsonify({
                'success': False,
                'error': result.get('error', 'Ralat pengiraan') if result else 'Ralat pengiraan'
            }), 400
        
        return jsonify({
            'success': True,
            'reply': result.get('message', ''),
            'data': {
                'zakat_amount': result.get('zakat_amount', 0),
                'zakatable_amount': result.get('zakatable_amount', 0),
                'reaches_nisab': result.get('reaches_nisab', False),
                'nisab_value': result.get('nisab_value', 0),
                'type': 'saham',
                'year': result.get('year', year),
                'year_type': result.get('year_type', year_type),
                'details': result.get('details', {})
            }
        }), 200
        
    except Exception as e:
        print(f"Error in calculate_zakat_saham: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Ralat sistem. Sila cuba lagi.'
        }), 500


# Both endpoint patterns supported
@zakat_bp.route("/zakat-calculator/perak", methods=["POST"])
@zakat_extended_bp.route("/api/calculate-zakat-perak", methods=["POST"])
def calculate_zakat_perak():
    """Calculate zakat for perak (silver)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Tiada data diterima'
            }), 400
        
        # Get inputs
        berat_perak_g = data.get('berat_perak_g')
        harga_per_gram = data.get('harga_per_gram')
        year = data.get('year', '1447')
        year_type = data.get('year_type', 'H')
        
        # Validate
        if berat_perak_g is None or harga_per_gram is None:
            return jsonify({
                'success': False,
                'error': 'Berat perak dan harga per gram diperlukan'
            }), 400
        
        try:
            berat_perak_g = float(berat_perak_g)
            harga_per_gram = float(harga_per_gram)
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Nilai tidak sah'
            }), 400
        
        # Calculate
        result = calculator.calculate_perak_zakat(
            berat_perak_g=berat_perak_g,
            harga_per_gram=harga_per_gram,
            year=str(year),
            year_type=year_type
        )
        
        if not result or not result.get('success'):
            return jsonify({
                'success': False,
                'error': result.get('error', 'Ralat pengiraan') if result else 'Ralat pengiraan'
            }), 400
        
        return jsonify({
            'success': True,
            'reply': result.get('message', ''),
            'data': {
                'zakat_amount': result.get('zakat_amount', 0),
                'zakatable_amount': result.get('zakatable_amount', 0),
                'reaches_nisab': result.get('reaches_nisab', False),
                'nisab_value': result.get('nisab_value', 0),
                'type': 'perak',
                'year': result.get('year', year),
                'year_type': result.get('year_type', year_type),
                'details': result.get('details', {})
            }
        }), 200
        
    except Exception as e:
        print(f"Error in calculate_zakat_perak: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Ralat sistem. Sila cuba lagi.'
        }), 500


# Both endpoint patterns supported
@zakat_bp.route("/zakat-calculator/kwsp", methods=["POST"])
@zakat_extended_bp.route("/api/calculate-zakat-kwsp", methods=["POST"])
def calculate_zakat_kwsp():
    """Calculate zakat for KWSP (EPF)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Tiada data diterima'
            }), 400
        
        # Get inputs
        jumlah_akaun_1 = data.get('jumlah_akaun_1')
        jumlah_akaun_2 = data.get('jumlah_akaun_2')
        jumlah_pengeluaran = data.get('jumlah_pengeluaran', 0)
        year = data.get('year', '1447')
        year_type = data.get('year_type', 'H')
        
        # Validate
        if jumlah_akaun_1 is None or jumlah_akaun_2 is None:
            return jsonify({
                'success': False,
                'error': 'Jumlah Akaun 1 dan Akaun 2 diperlukan'
            }), 400
        
        try:
            jumlah_akaun_1 = float(jumlah_akaun_1)
            jumlah_akaun_2 = float(jumlah_akaun_2)
            jumlah_pengeluaran = float(jumlah_pengeluaran)
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Nilai tidak sah'
            }), 400
        
        # Calculate
        result = calculator.calculate_kwsp_zakat(
            jumlah_akaun_1=jumlah_akaun_1,
            jumlah_akaun_2=jumlah_akaun_2,
            jumlah_pengeluaran=jumlah_pengeluaran,
            year=str(year),
            year_type=year_type
        )
        
        if not result or not result.get('success'):
            return jsonify({
                'success': False,
                'error': result.get('error', 'Ralat pengiraan') if result else 'Ralat pengiraan'
            }), 400
        
        return jsonify({
            'success': True,
            'reply': result.get('message', ''),
            'data': {
                'zakat_amount': result.get('zakat_amount', 0),
                'zakatable_amount': result.get('zakatable_amount', 0),
                'reaches_nisab': result.get('reaches_nisab', False),
                'nisab_value': result.get('nisab_value', 0),
                'type': 'kwsp',
                'year': result.get('year', year),
                'year_type': result.get('year_type', year_type),
                'details': result.get('details', {})
            }
        }), 200
        
    except Exception as e:
        print(f"Error in calculate_zakat_kwsp: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': 'Ralat sistem. Sila cuba lagi.'
        }), 500


@zakat_bp.route("/api/zakat/years", methods=["GET"])
def get_zakat_years():
    """Get available years for zakat calculation"""
    try:
        year_type = request.args.get('type', 'H')  # H for Hijrah, M for Masihi
        
        # Validate year_type
        if year_type not in ['H', 'M']:
            year_type = 'H'
        
        result = calculator.fetch_available_years(year_type=year_type)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'years': result.get('years', [])
            }), 200
        else:
            # Return default years if API fails
            if year_type == 'H':
                default_years = [str(1447 - i) for i in range(10)]  # Last 10 Hijrah years
            else:
                default_years = [str(2024 - i) for i in range(10)]  # Last 10 Masihi years
            
            return jsonify({
                'success': True,
                'years': default_years,
                'fallback': True
            }), 200
            
    except Exception as e:
        print(f"Error in get_zakat_years: {e}")
        import traceback
        traceback.print_exc()
        
        # Return default years on error
        year_type = request.args.get('type', 'H')
        if year_type == 'H':
            default_years = [str(1447 - i) for i in range(10)]
        else:
            default_years = [str(2024 - i) for i in range(10)]
        
        return jsonify({
            'success': True,
            'years': default_years,
            'fallback': True
        }), 200


@zakat_extended_bp.route("/api/zakat/nisab-extended", methods=["GET"])
def get_nisab_extended():
    """Get nisab info for extended zakat types"""
    try:
        zakat_type = request.args.get('type', 'padi')
        year = request.args.get('year', '1447')
        year_type = request.args.get('year_type', 'H')
        
        result = calculator.get_nisab_extended(
            zakat_type=zakat_type,
            year=str(year),
            year_type=year_type
        )
        
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
        print(f"Error in get_nisab_extended: {e}")
        return jsonify({
            'success': False,
            'error': 'Ralat sistem'
        }), 500