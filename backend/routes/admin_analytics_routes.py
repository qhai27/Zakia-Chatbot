"""
Admin Analytics Routes - FIXED
Provides comprehensive analytics for the ZAKIA chatbot system
"""

from flask import Blueprint, request, jsonify
from database import DatabaseManager
from datetime import datetime, timedelta
from collections import defaultdict

admin_analytics_bp = Blueprint('admin_analytics', __name__, url_prefix='/admin/analytics')

@admin_analytics_bp.route('/dashboard', methods=['GET'])
def get_analytics_dashboard():
    """
    Get comprehensive analytics dashboard data
    Query params:
        - period: 'day', 'week', 'month' (default: 'month')
    """
    local_db = None
    cursor = None
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
        
        # Create fresh connection for this request
        local_db = DatabaseManager()
        if not local_db.connect():
            return jsonify({
                "success": False,
                "error": "Database connection failed"
            }), 500
        
        cursor = local_db.connection.cursor(dictionary=True)
        
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
        
        # ===== FAQ ANALYTICS =====
        
        # Total FAQs
        cursor.execute("SELECT COUNT(*) as total FROM faqs")
        total_faqs = cursor.fetchone()['total']
        
        # FAQs by category
        cursor.execute("""
            SELECT 
                COALESCE(category, 'Umum') as category,
                COUNT(*) as count
            FROM faqs
            GROUP BY COALESCE(category, 'Umum')
            ORDER BY count DESC
        """)
        faqs_by_category = cursor.fetchall()
        
        # Debug: Log the data structure
        print(f"📊 FAQ categories query result: {len(faqs_by_category)} categories")
        if faqs_by_category:
            print(f"   First item: {faqs_by_category[0]}")
            print(f"   First item type: {type(faqs_by_category[0])}")
            if isinstance(faqs_by_category[0], dict):
                print(f"   First item keys: {list(faqs_by_category[0].keys())}")
        
        # Ensure data is properly formatted as list of dicts
        formatted_categories = []
        for item in faqs_by_category:
            if isinstance(item, dict):
                formatted_categories.append({
                    'category': item.get('category', 'Umum'),
                    'count': int(item.get('count', 0))
                })
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                # Handle tuple/list format
                formatted_categories.append({
                    'category': str(item[0]) if item[0] else 'Umum',
                    'count': int(item[1]) if item[1] else 0
                })
        
        faqs_by_category = formatted_categories if formatted_categories else faqs_by_category
        
        # Recent FAQs (last 30 days)
        cursor.execute("""
            SELECT COUNT(*) as recent_count
            FROM faqs
            WHERE created_at >= %s OR updated_at >= %s
        """, (start_date, start_date))
        recent_faqs = cursor.fetchone()['recent_count']
        
        # FAQ growth over time (for the period)
        cursor.execute("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as count
            FROM faqs
            WHERE created_at >= %s AND created_at <= %s
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        """, (start_date, end_date))
        faq_growth = cursor.fetchall()
        
        # Convert date objects to strings
        for item in faq_growth:
            item['date'] = item['date'].strftime('%Y-%m-%d')
        
        # Average answer length
        cursor.execute("""
            SELECT AVG(LENGTH(answer)) as avg_length
            FROM faqs
        """)
        avg_length_result = cursor.fetchone()
        avg_answer_length = round(float(avg_length_result['avg_length']) if avg_length_result['avg_length'] else 0, 0)
        
        # Most used categories (top 5)
        top_categories = faqs_by_category[:5] if len(faqs_by_category) > 5 else faqs_by_category
        
        faq_analytics = {
            "total_faqs": total_faqs,
            "recent_faqs": recent_faqs,
            "faqs_by_category": faqs_by_category,
            "faq_growth": faq_growth,
            "avg_answer_length": avg_answer_length,
            "top_categories": top_categories
        }
        
        return jsonify({
            "success": True,
            "overview": overview,
            "charts": {
                "chats_per_day": chats_per_day,
                "hourly_distribution": hourly_distribution
            },
            "top_questions": top_questions,
            "zakat_popularity": zakat_popularity,
            "faq_analytics": faq_analytics
        })
        
    except Exception as e:
        print(f"❌ Analytics dashboard error: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
        
    finally:
        # Clean up resources
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if local_db:
            try:
                local_db.close()
            except:
                pass


@admin_analytics_bp.route('/export', methods=['GET'])
def export_analytics():
    """
    Export analytics data
    Query params:
        - type: 'chats', 'questions', 'zakat'
        - date_from: start date (YYYY-MM-DD)
        - date_to: end date (YYYY-MM-DD)
    """
    local_db = None
    cursor = None
    try:
        export_type = request.args.get('type', 'chats')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        if not date_from or not date_to:
            return jsonify({
                "success": False,
                "error": "date_from and date_to are required"
            }), 400
        
        # Create fresh connection
        local_db = DatabaseManager()
        if not local_db.connect():
            return jsonify({
                "success": False,
                "error": "Database connection failed"
            }), 500
        
        cursor = local_db.connection.cursor(dictionary=True)
        
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
        
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if local_db:
            try:
                local_db.close()
            except:
                pass


# Health check
@admin_analytics_bp.route('/health', methods=['GET'])
def analytics_health():
    """Health check for analytics endpoints"""
    return jsonify({
        "success": True,
        "message": "Analytics endpoints are operational"
    })