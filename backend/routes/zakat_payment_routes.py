"""
Zakat Payment Integration Routes
Handles payment gateway integration with JomZakat portal
"""

from flask import Blueprint, request, jsonify, redirect
from database import DatabaseManager
import hashlib
import time
from urllib.parse import urlencode

payment_bp = Blueprint('payment', __name__)
db = DatabaseManager()

def generate_payment_token(data):
    """Generate secure token for payment verification"""
    timestamp = str(int(time.time()))
    raw = f"{data.get('zakat_amount')}{data.get('zakat_type')}{timestamp}"
    token = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return token

@payment_bp.route('/api/payment/prepare', methods=['POST'])
def prepare_payment():
    """
    Prepare payment data and return JomZakat form URL with pre-filled parameters
    """
    try:
        data = request.get_json() or {}
        
        # Required fields
        required = ['zakat_type', 'zakat_amount', 'year', 'year_type']
        for field in required:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'{field} diperlukan'
                }), 400
        
        # Extract data
        zakat_type = data.get('zakat_type')
        zakat_amount = float(data.get('zakat_amount'))
        year = data.get('year')
        year_type = data.get('year_type')
        details = data.get('details', {})
        
        # Generate payment reference
        payment_token = generate_payment_token(data)
        payment_ref = f"ZAKIA-{year}{year_type}-{payment_token}"
        
        # Save payment record to database (optional - for tracking)
        try:
            if db.connection and db.connection.is_connected():
                cursor = db.connection.cursor()
                cursor.execute("""
                    INSERT INTO payment_logs 
                    (payment_ref, zakat_type, zakat_amount, year, year_type, details, status, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, 'initiated', NOW())
                """, (payment_ref, zakat_type, zakat_amount, year, year_type, str(details)))
                db.connection.commit()
                cursor.close()
        except Exception as e:
            print(f"Warning: Could not log payment: {e}")
        
        # Map zakat types to JomZakat form IDs
        zakat_type_map = {
            'pendapatan': 'pendapatan',
            'income_kaedah_a': 'pendapatan',
            'income_kaedah_b': 'pendapatan',
            'simpanan': 'simpanan',
            'savings': 'simpanan',
            'padi': 'padi',
            'saham': 'saham',
            'perak': 'perak',
            'kwsp': 'kwsp'
        }
        
        jomzakat_type = zakat_type_map.get(zakat_type, 'pendapatan')
        
        # Build JomZakat payment URL with query parameters
        # Note: This assumes JomZakat accepts these parameters - may need adjustment
        payment_params = {
            'jenis': jomzakat_type,
            'jumlah': f"{zakat_amount:.2f}",
            'tahun': year,
            'jenisTahun': year_type,
            'rujukan': payment_ref,
            'source': 'zakia'
        }
        
        # Base JomZakat URL
        base_url = "https://jom.zakatkedah.com.my/kirazakat/tabkirazakat.php"
        payment_url = f"{base_url}?{urlencode(payment_params)}"
        
        return jsonify({
            'success': True,
            'payment_url': payment_url,
            'payment_ref': payment_ref,
            'zakat_type': jomzakat_type,
            'amount': zakat_amount,
            'message': 'Sila lengkapkan pembayaran di JomZakat'
        }), 200
        
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Jumlah zakat tidak sah'
        }), 400
    except Exception as e:
        print(f"Payment preparation error: {e}")
        return jsonify({
            'success': False,
            'error': 'Ralat sistem. Sila cuba lagi.'
        }), 500

@payment_bp.route('/api/payment/callback', methods=['POST', 'GET'])
def payment_callback():
    """
    Handle callback from JomZakat payment gateway
    This endpoint will be called when payment is completed
    """
    try:
        # Get callback data (adjust based on JomZakat's actual callback format)
        if request.method == 'POST':
            data = request.get_json() or request.form.to_dict()
        else:
            data = request.args.to_dict()
        
        payment_ref = data.get('rujukan') or data.get('reference')
        status = data.get('status')
        
        if not payment_ref:
            return jsonify({
                'success': False,
                'error': 'Payment reference missing'
            }), 400
        
        # Update payment status in database
        if db.connection and db.connection.is_connected():
            cursor = db.connection.cursor()
            cursor.execute("""
                UPDATE payment_logs 
                SET status = %s, updated_at = NOW(), callback_data = %s
                WHERE payment_ref = %s
            """, (status, str(data), payment_ref))
            db.connection.commit()
            cursor.close()
        
        return jsonify({
            'success': True,
            'message': 'Payment status updated',
            'payment_ref': payment_ref,
            'status': status
        }), 200
        
    except Exception as e:
        print(f"Payment callback error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@payment_bp.route('/api/payment/status/<payment_ref>', methods=['GET'])
def check_payment_status(payment_ref):
    """
    Check payment status by reference number
    """
    try:
        if not db.connection or not db.connection.is_connected():
            db.connect()
        
        cursor = db.connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT payment_ref, zakat_type, zakat_amount, status, created_at, updated_at
            FROM payment_logs
            WHERE payment_ref = %s
        """, (payment_ref,))
        
        result = cursor.fetchone()
        cursor.close()
        
        if not result:
            return jsonify({
                'success': False,
                'error': 'Payment not found'
            }), 404
        
        return jsonify({
            'success': True,
            'payment': result
        }), 200
        
    except Exception as e:
        print(f"Payment status check error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500