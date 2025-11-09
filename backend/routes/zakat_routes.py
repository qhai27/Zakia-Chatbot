from flask import Blueprint, request, jsonify
from zakat_calculator import ZakatCalculator

zakat_bp = Blueprint('zakat', __name__)
calculator = ZakatCalculator()


@zakat_bp.route("/calculate-zakat", methods=["POST"])
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


@zakat_bp.route("/zakat/nisab-info", methods=["GET"])
def nisab_info():
    year = request.args.get('year', '1447')
    year_type = request.args.get('type', 'H')
    result = calculator.get_nisab_info(year, year_type)
    return jsonify(result)


@zakat_bp.route("/zakat/years", methods=["GET"])
def get_years():
    year_type = request.args.get('type', 'H')
    result = calculator.fetch_available_years(year_type)
    if result['success']:
        return jsonify({'success': True, 'years': result['years'], 'year_type': result['year_type']})
    return jsonify({'success': True, 'years': ['1447', '1446', '1445'], 'fallback': True})
