"""
Admin Analytics Routes
Provides comprehensive analytics for the ZAKIA chatbot system
"""

from flask import Blueprint, request, jsonify
from database import DatabaseManager
from datetime import datetime, timedelta
from collections import defaultdict

admin_analytics_bp = Blueprint('admin_analytics', __name__, url_prefix='/admin/analytics')

# Initialize database
db = DatabaseManager()

@admin_analytics_bp.route('/dashboard', methods=['GET'])
def get_analytics_dashboard():
    """
    Get comprehensive analytics dashboard data
    Query params:
        - period: 'day', 'week', 'month' (default: 'month')
    """
    try:
        period = request.args.get('period', 'month')
        
        # Calculate date range
        end_date = datetime.now()
        if period == 'day':
            start_date = end_date - timedelta(days=1)
        elif period == 'week':
            start_date = end_date - timedelta(weeks=1)
        else:  # month
            start_date = end_date - timedelta(days=30)
        
        if not db.connection or not db.connection.is_connected():
            db.connect()
        
        cursor = db.connection.cursor(dictionary=True)
        
        # ===== OVERVIEW STATS =====
        
        # Total chats in period
        cursor.execute("""
            SELECT COUNT(*) as total_chats
            FROM chat_logs
            WHERE created_at >= %s AND created_at <= %s
        """, (start_date, end_date))
        total_chats = cursor.fetchone()['total_chats']
        
        # Unique users in period
        cursor.execute("""
            SELECT COUNT(DISTINCT session_id) as unique_users
            FROM chat_logs
            WHERE created_at >= %s AND created_at <= %s
            AND session_id IS NOT NULL
        """, (start_date, end_date))
        unique_users = cursor.fetchone()['unique_users']
        
        # Average session length
        cursor.execute("""
            SELECT AVG(message_count) as avg_session
            FROM (
                SELECT session_id, COUNT(*) as message_count
                FROM chat_logs
                WHERE created_at >= %s AND created_at <= %s
                AND session_id IS NOT NULL
                GROUP BY session_id
            ) as sessions
        """, (start_date, end_date))
        avg_session_result = cursor.fetchone()
        avg_session_length = float(avg_session_result['avg_session']) if avg_session_result['avg_session'] else 0
        
        # Growth rate (compared to previous period)
        prev_start = start_date - (end_date - start_date)
        cursor.execute("""
            SELECT COUNT(*) as prev_chats
            FROM chat_logs
            WHERE created_at >= %s AND created_at < %s
        """, (prev_start, start_date))
        prev_chats = cursor.fetchone()['prev_chats']
        
        if prev_chats > 0:
            growth_rate = round(((total_chats - prev_chats) / prev_chats) * 100, 1)
        else:
            growth_rate = 0 if total_chats == 0 else 100
        
        # Engagement score (messages per user * 10, capped at 100)
        engagement_score = min(100, round((total_chats / max(unique_users, 1)) * 10, 1))
        
        overview = {
            "total_chats": total_chats,
            "unique_users": unique_users,
            "avg_session_length": round(avg_session_length, 1),
            "growth_rate": growth_rate,
            "engagement_score": engagement_score
        }
        
        # ===== CHATS PER DAY =====
        
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as count
            FROM chat_logs
            WHERE created_at >= %s AND created_at <= %s
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        """, (start_date, end_date))
        chats_per_day = cursor.fetchall()
        
        # Convert date objects to strings
        for item in chats_per_day:
            item['date'] = item['date'].strftime('%Y-%m-%d')
        
        # ===== HOURLY DISTRIBUTION =====
        
        cursor.execute("""
            SELECT 
                HOUR(created_at) as hour,
                COUNT(*) as count
            FROM chat_logs
            WHERE created_at >= %s AND created_at <= %s
            GROUP BY HOUR(created_at)
            ORDER BY hour ASC
        """, (start_date, end_date))
        hourly_distribution = cursor.fetchall()
        
        # Fill in missing hours with 0
        hourly_dict = {item['hour']: item['count'] for item in hourly_distribution}
        hourly_distribution = [
            {"hour": h, "count": hourly_dict.get(h, 0)}
            for h in range(24)
        ]
        
        # ===== TOP QUESTIONS =====
        
        cursor.execute("""
            SELECT 
                user_message,
                COUNT(*) as frequency
            FROM chat_logs
            WHERE created_at >= %s AND created_at <= %s
            AND user_message IS NOT NULL
            AND user_message != ''
            GROUP BY user_message
            ORDER BY frequency DESC
            LIMIT 10
        """, (start_date, end_date))
        top_questions = cursor.fetchall()
        
        # ===== ZAKAT TYPE POPULARITY =====
        
        cursor.execute("""
            SELECT 
                zakat_type,
                COUNT(*) as count,
                SUM(zakat_amount) as total_amount
            FROM reminders
            WHERE created_at >= %s AND created_at <= %s
            AND zakat_type IS NOT NULL
            GROUP BY zakat_type
            ORDER BY count DESC
        """, (start_date, end_date))
        zakat_popularity = cursor.fetchall()
        
        # Convert Decimal to float for JSON serialization
        for item in zakat_popularity:
            if item.get('total_amount'):
                item['total_amount'] = float(item['total_amount'])
        
        cursor.close()
        
        return jsonify({
            "success": True,
            "overview": overview,
            "charts": {
                "chats_per_day": chats_per_day,
                "hourly_distribution": hourly_distribution
            },
            "top_questions": top_questions,
            "zakat_popularity": zakat_popularity
        })
        
    except Exception as e:
        print(f"❌ Analytics dashboard error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@admin_analytics_bp.route('/export', methods=['GET'])
def export_analytics():
    """
    Export analytics data
    Query params:
        - type: 'chats', 'questions', 'zakat'
        - date_from: start date (YYYY-MM-DD)
        - date_to: end date (YYYY-MM-DD)
    """
    try:
        export_type = request.args.get('type', 'chats')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        if not date_from or not date_to:
            return jsonify({
                "success": False,
                "error": "date_from and date_to are required"
            }), 400
        
        if not db.connection or not db.connection.is_connected():
            db.connect()
        
        cursor = db.connection.cursor(dictionary=True)
        
        if export_type == 'chats':
            cursor.execute("""
                SELECT 
                    id_log,
                    session_id,
                    user_message,
                    bot_response,
                    created_at
                FROM chat_logs
                WHERE created_at >= %s AND created_at <= %s
                ORDER BY created_at DESC
            """, (date_from, date_to))
            
        elif export_type == 'questions':
            cursor.execute("""
                SELECT 
                    user_message,
                    COUNT(*) as frequency
                FROM chat_logs
                WHERE created_at >= %s AND created_at <= %s
                GROUP BY user_message
                ORDER BY frequency DESC
            """, (date_from, date_to))
            
        elif export_type == 'zakat':
            cursor.execute("""
                SELECT 
                    name,
                    ic_number,
                    phone,
                    zakat_type,
                    zakat_amount,
                    year,
                    created_at
                FROM reminders
                WHERE created_at >= %s AND created_at <= %s
                ORDER BY created_at DESC
            """, (date_from, date_to))
        else:
            cursor.close()
            return jsonify({
                "success": False,
                "error": "Invalid export type"
            }), 400
        
        data = cursor.fetchall()
        
        # Format timestamps
        for item in data:
            if item.get('created_at'):
                item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            # Convert Decimal to float
            if item.get('zakat_amount'):
                item['zakat_amount'] = float(item['zakat_amount'])
        
        cursor.close()
        
        return jsonify({
            "success": True,
            "data": data,
            "count": len(data)
        })
        
    except Exception as e:
        print(f"❌ Export analytics error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# Health check
@admin_analytics_bp.route('/health', methods=['GET'])
def analytics_health():
    """Health check for analytics endpoints"""
    return jsonify({
        "success": True,
        "message": "Analytics endpoints are operational"
    })