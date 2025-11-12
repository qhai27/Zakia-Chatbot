from flask import Blueprint, request, jsonify
from zakat_calculator import ZakatCalculator

zakat_bp = Blueprint('zakat', __name__)
calculator = ZakatCalculator()


@zakat_bp.route("/api/calculate-zakat", methods=["POST"])
def calculate_zakat():
    try:
        data = request.json
        z_type = data.get('type', '').lower()
        year = data.get('year', '1447')
        year_type = data.get('year_type', 'H')

        if z_type == 'income':
            result = calculator.calculate_income_zakat(data.get('amount'), data.get('expenses'), year, year_type)
        elif z_type == 'savings':
            result = calculator.calculate_savings_zakat(data.get('amount'), year, year_type)
        else:
            return jsonify({'success': False, 'error': 'Jenis zakat tidak sah'}), 400

        return jsonify({'success': True, 'reply': result['message'], 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@zakat_bp.route("/api/zakat/nisab-info", methods=["GET"])
def nisab_info():
    year = request.args.get('year', '1447')
    year_type = request.args.get('type', 'H')
    result = calculator.get_nisab_info(year, year_type)
    return jsonify(result)


@zakat_bp.route('/api/zakat/years', methods=['GET'])
def get_years():
    """
    GET /api/zakat/years?type=H
    Returns list of years for Hijrah (H) or Masihi (M)
    """
    year_type = (request.args.get('type') or 'H').upper()
    if year_type not in ('H', 'M'):
        return jsonify({'success': False, 'error': 'Invalid type parameter. Use H or M.'}), 400

    try:
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
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500