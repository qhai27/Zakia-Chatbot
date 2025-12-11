"""
Zakat Routes - API endpoints for zakat calculations

"""

from flask import Blueprint, request, jsonify, current_app
from zakat_calculator import ZakatCalculator

# Create blueprint
zakat_bp = Blueprint('zakat', __name__)
calculator = ZakatCalculator()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def safe_float(value, default=0.0):
    """Safely convert value to float"""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def validate_input(data, required_fields):
    """Validate required fields in request data"""
    for field in required_fields:
        if data.get(field) is None:
            return False, f"{field} diperlukan"
    return True, None


def build_zakat_response(result, zakat_type, year, year_type):
    """Build standardized zakat response"""
    if not result or not result.get('success'):
        return {
            'success': False,
            'error': result.get('error', 'Ralat pengiraan') if result else 'Ralat pengiraan'
        }, 400

    return {
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
    }, 200


# ============================================================================
# INCOME & SAVINGS CALCULATIONS
# ============================================================================

@zakat_bp.route("/api/calculate-zakat", methods=["POST"])
def calculate_zakat():
    """Main zakat calculation endpoint for income (Kaedah A & B) and savings"""
    try:
        data = request.get_json() or {}
        zakat_type = data.get('type')
        year = data.get('year', '1447')
        year_type = data.get('year_type', 'H')

        # Kaedah A: Gross Income (tanpa tolakan)
        if zakat_type == 'income_kaedah_a':
            is_valid, error = validate_input(data, ['gross_income'])
            if not is_valid:
                return jsonify({'success': False, 'error': error}), 400

            gross_income = safe_float(data.get('gross_income'))
            result = calculator.calculate_income_zakat_kaedah_a(
                gross_income=gross_income,
                year=str(year),
                year_type=year_type
            )

        # Kaedah B: Net Income (dengan tolakan)
        elif zakat_type == 'income_kaedah_b':
            is_valid, error = validate_input(data, ['annual_income', 'annual_expenses'])
            if not is_valid:
                return jsonify({'success': False, 'error': error}), 400

            annual_income = safe_float(data.get('annual_income'))
            annual_expenses = safe_float(data.get('annual_expenses'))
            result = calculator.calculate_income_zakat_kaedah_b(
                annual_income=annual_income,
                annual_expenses=annual_expenses,
                year=str(year),
                year_type=year_type
            )

        # Savings
        elif zakat_type == 'savings':
            is_valid, error = validate_input(data, ['savings_amount'])
            if not is_valid:
                return jsonify({'success': False, 'error': error}), 400

            savings_amount = safe_float(data.get('savings_amount'))
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

        response, status = build_zakat_response(result, zakat_type, year, year_type)
        return jsonify(response), status

    except Exception as e:
        current_app.logger.exception("calculate_zakat error")
        return jsonify({'success': False, 'error': 'Ralat sistem. Sila cuba lagi.'}), 500


# ============================================================================
# EXTENDED ZAKAT TYPES (Padi, Saham, Perak, KWSP)
# ============================================================================

@zakat_bp.route('/zakat-calculator/padi', methods=['POST'])
def calculate_padi_zakat_api():
    """Calculate zakat for padi (rice) - accepts jumlah_rm (total value in RM)"""
    try:
        data = request.get_json() or {}
        jumlah_rm = safe_float(data.get('jumlah_rm'), 0)
        year = data.get('year', '')
        year_type = data.get('year_type', 'M')

        if jumlah_rm <= 0:
            return jsonify({
                'success': False,
                'error': 'Jumlah hasil diperlukan dan mesti lebih daripada 0'
            }), 400

        result = calculator.calculate_padi_zakat(jumlah_rm, year, year_type)
        response, status = build_zakat_response(result, 'padi', year, year_type)
        return jsonify(response), status

    except Exception as e:
        current_app.logger.exception("calculate_padi_zakat_api error")
        return jsonify({'success': False, 'error': str(e)}), 500


@zakat_bp.route("/zakat-calculator/saham", methods=["POST"])
def calculate_zakat_saham():
    """Calculate zakat for saham (shares/stocks)"""
    try:
        data = request.get_json() or {}
        is_valid, error = validate_input(data, ['nilai_portfolio'])
        if not is_valid:
            return jsonify({'success': False, 'error': error}), 400

        nilai_portfolio = safe_float(data.get('nilai_portfolio'))
        hutang_saham = safe_float(data.get('hutang_saham'), 0)
        year = data.get('year', '1447')
        year_type = data.get('year_type', 'H')

        result = calculator.calculate_saham_zakat(
            nilai_portfolio=nilai_portfolio,
            hutang_saham=hutang_saham,
            year=str(year),
            year_type=year_type
        )
        response, status = build_zakat_response(result, 'saham', year, year_type)
        return jsonify(response), status

    except Exception as e:
        current_app.logger.exception("calculate_zakat_saham error")
        return jsonify({'success': False, 'error': 'Ralat sistem. Sila cuba lagi.'}), 500


@zakat_bp.route("/zakat-calculator/perak", methods=["POST"])
def calculate_zakat_perak():
    """Calculate zakat for perak (silver)"""
    try:
        data = request.get_json() or {}
        is_valid, error = validate_input(data, ['berat_perak_g', 'harga_per_gram'])
        if not is_valid:
            return jsonify({'success': False, 'error': error}), 400

        berat_perak_g = safe_float(data.get('berat_perak_g'))
        harga_per_gram = safe_float(data.get('harga_per_gram'))
        year = data.get('year', '1447')
        year_type = data.get('year_type', 'H')

        result = calculator.calculate_perak_zakat(
            berat_perak_g=berat_perak_g,
            harga_per_gram=harga_per_gram,
            year=str(year),
            year_type=year_type
        )
        response, status = build_zakat_response(result, 'perak', year, year_type)
        return jsonify(response), status

    except Exception as e:
        current_app.logger.exception("calculate_zakat_perak error")
        return jsonify({'success': False, 'error': 'Ralat sistem. Sila cuba lagi.'}), 500


@zakat_bp.route("/zakat-calculator/kwsp", methods=["POST"])
def calculate_zakat_kwsp():
    """Calculate zakat for KWSP (EPF)"""
    try:
        data = request.get_json() or {}
        is_valid, error = validate_input(data, ['jumlah_akaun_1', 'jumlah_akaun_2'])
        if not is_valid:
            return jsonify({'success': False, 'error': error}), 400

        jumlah_akaun_1 = safe_float(data.get('jumlah_akaun_1'))
        jumlah_akaun_2 = safe_float(data.get('jumlah_akaun_2'))
        jumlah_pengeluaran = safe_float(data.get('jumlah_pengeluaran'), 0)
        year = data.get('year', '1447')
        year_type = data.get('year_type', 'H')

        result = calculator.calculate_kwsp_zakat(
            jumlah_akaun_1=jumlah_akaun_1,
            jumlah_akaun_2=jumlah_akaun_2,
            jumlah_pengeluaran=jumlah_pengeluaran,
            year=str(year),
            year_type=year_type
        )
        response, status = build_zakat_response(result, 'kwsp', year, year_type)
        return jsonify(response), status

    except Exception as e:
        current_app.logger.exception("calculate_zakat_kwsp error")
        return jsonify({'success': False, 'error': 'Ralat sistem. Sila cuba lagi.'}), 500


# ============================================================================
# NISAB & YEAR INFORMATION
# ============================================================================

@zakat_bp.route("/api/zakat/years", methods=["GET"])
def get_zakat_years():
    """Get available years for zakat calculation"""
    try:
        year_type = request.args.get('type', 'H')  # H=Hijrah, M=Masihi
        if year_type not in ['H', 'M']:
            year_type = 'H'

        result = calculator.fetch_available_years(year_type=year_type)

        if result.get('success'):
            return jsonify({
                'success': True,
                'years': result.get('years', [])
            }), 200

        # Fallback to default years
        default_years = [str(1447 - i) for i in range(10)] if year_type == 'H' \
                       else [str(2024 - i) for i in range(10)]

        return jsonify({
            'success': True,
            'years': default_years,
            'fallback': True
        }), 200

    except Exception as e:
        current_app.logger.exception("get_zakat_years error")
        year_type = request.args.get('type', 'H')
        default_years = [str(1447 - i) for i in range(10)] if year_type == 'H' \
                       else [str(2024 - i) for i in range(10)]
        return jsonify({
            'success': True,
            'years': default_years,
            'fallback': True
        }), 200


@zakat_bp.route('/api/zakat/nisab-info', methods=['GET'])
def nisab_info():
    """
    Return comprehensive nisab info for all zakat types.
    GET params: year (e.g. "1447" or "2024"), type ('H' or 'M')
    Returns: pendapatan, simpanan, padi, saham, perak, kwsp
    """
    year = request.args.get('year', '') or ''
    year_type = request.args.get('type', 'M') or 'M'

    try:
        calc = ZakatCalculator()
        res = calc.fetch_nisab_data(year, year_type)

        if not res.get('success'):
            current_app.logger.warning("fetch_nisab_data failed: %s", res.get('error'))
            return jsonify({
                'success': False,
                'error': res.get('error', 'Gagal mendapatkan maklumat nisab')
            }), 502

        data = res.get('data', {}) or {}

        # Extract main nisab values
        nisab_pendapatan = safe_float(data.get('nisab_pendapatan'), 22000.0)
        nisab_simpanan = safe_float(data.get('nisab_simpanan'), nisab_pendapatan)
        kadar = safe_float(data.get('kadar_zakat'), 0.02577)

        # Fetch extended type nisab values
        nisab_padi = safe_float(
            calc.fetch_nisab_extended('padi', year, year_type).get('nisab', 1300.0)
        )
        nisab_saham = safe_float(
            calc.fetch_nisab_extended('saham', year, year_type).get('nisab', 85.0)
        )
        nisab_perak = safe_float(
            calc.fetch_nisab_extended('perak', year, year_type).get('nisab', 595.0)
        )
        nisab_kwsp = safe_float(
            calc.fetch_nisab_extended('kwsp', year, year_type).get('nisab', 85.0)
        )

        # Build comprehensive reply
        year_label = 'Hijrah' if year_type == 'H' else 'Masihi'
        reply_lines = [
            f"📊 **Maklumat Nisab Lengkap - Tahun {year} ({year_label})**\n",
            "💼 **Zakat Pendapatan:**",
            f"   • Nisab: RM{nisab_pendapatan:,.2f}",
            f"   • Kadar: {kadar*100:.2f}%\n",
            "💰 **Zakat Simpanan:**",
            f"   • Nisab: RM{nisab_simpanan:,.2f}",
            f"   • Kadar: {kadar*100:.2f}%\n",
            "🌾 **Zakat Padi:**",
            f"   • Nisab: {nisab_padi:,.2f} kg",
            f"   • Kadar: 10%\n",
            "📈 **Zakat Saham:**",
            f"   • Nisab: {nisab_saham:,.2f} gram emas",
            f"   • Kadar: 2.5%\n",
            "🥈 **Zakat Perak:**",
            f"   • Nisab: {nisab_perak:,.2f} gram",
            f"   • Kadar: 2.577%\n",
            "🏦 **Zakat KWSP:**",
            f"   • Nisab: {nisab_kwsp:,.2f} gram emas",
            f"   • Kadar: 2.577%"
        ]

        return jsonify({
            'success': True,
            'reply': "\n".join(reply_lines),
            'data': {
                'pendapatan': {'nisab': nisab_pendapatan, 'kadar': kadar, 'unit': 'RM'},
                'simpanan': {'nisab': nisab_simpanan, 'kadar': kadar, 'unit': 'RM'},
                'padi': {'nisab': nisab_padi, 'kadar': 0.10, 'unit': 'kg'},
                'saham': {'nisab': nisab_saham, 'kadar': 0.025, 'unit': 'gram emas'},
                'perak': {'nisab': nisab_perak, 'kadar': 0.02577, 'unit': 'gram'},
                'kwsp': {'nisab': nisab_kwsp, 'kadar': 0.02577, 'unit': 'gram emas'}
            },
            'year': year,
            'year_type': year_label
        }), 200

    except Exception as e:
        current_app.logger.exception("nisab_info error")
        return jsonify({'success': False, 'error': str(e)}), 500


@zakat_bp.route("/api/zakat/nisab-extended", methods=["GET"])
def get_nisab_extended():
    """Get nisab info for extended zakat types (padi, saham, perak, kwsp)"""
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

        return jsonify({
            'success': False,
            'error': result.get('error', 'Gagal mendapatkan maklumat nisab')
        }), 500

    except Exception as e:
        current_app.logger.exception("get_nisab_extended error")
        return jsonify({'success': False, 'error': 'Ralat sistem'}), 500