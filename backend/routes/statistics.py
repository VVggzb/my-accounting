from flask import Blueprint, request
from extensions import db
from models import Bill, Category
from utils import success_response, error_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import func

bp = Blueprint('statistics', __name__)


# ============================================================
# 接口 1：核心数据概览
# ============================================================
@bp.route('/statistics/overview', methods=['GET'])
@jwt_required()
def get_overview():
    """
    获取核心统计数据
    参数：start_date, end_date (可选，不传则查全部)
    返回：总收入、总支出、结余、日均支出、总笔数
    """
    user_id = int(get_jwt_identity())
    
    # 获取日期范围参数
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 基础查询
    query = Bill.query.filter_by(user_id=user_id, in_trash=False)
    
    # 日期筛选
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Bill.date >= start)
        except ValueError:
            return error_response('start_date 格式错误，请使用 YYYY-MM-DD', 400)
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Bill.date <= end)
        except ValueError:
            return error_response('end_date 格式错误，请使用 YYYY-MM-DD', 400)
    
    # 计算总收入
    total_income = query.filter_by(type='income').with_entities(func.sum(Bill.amount)).scalar() or 0
    
    # 计算总支出
    total_expense = query.filter_by(type='expense').with_entities(func.sum(Bill.amount)).scalar() or 0
    
    # 计算结余
    balance = total_income - total_expense
    
    # 计算总笔数
    total_count = query.count()
    
    # 计算日均支出（只有支出）
    expense_bills = query.filter_by(type='expense').all()
    if expense_bills and start_date and end_date:
        # 计算天数
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        days = (end - start).days + 1
        daily_avg = total_expense / days if days > 0 else 0
    else:
        daily_avg = 0
    
    # 计算待报销金额
    pending_reimbursement = query.filter_by(type='expense', reimbursement_status='pending').with_entities(func.sum(Bill.amount)).scalar() or 0
    
    return success_response({
        'total_income': round(total_income, 2),
        'total_expense': round(total_expense, 2),
        'balance': round(balance, 2),
        'daily_avg_expense': round(daily_avg, 2),
        'total_count': total_count,
        'pending_reimbursement': round(pending_reimbursement, 2)
    })


# ============================================================
# 接口 2：分类支出分析（环形图数据）
# ============================================================
@bp.route('/statistics/category', methods=['GET'])
@jwt_required()
def get_category_stats():
    """
    获取分类统计（环形图数据）
    参数：
        - start_date, end_date (可选)
        - type: expense 或 income (默认 expense)
    返回：各分类的金额、占比、笔数
    """
    user_id = int(get_jwt_identity())
    
    # 获取参数
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    stats_type = request.args.get('type', 'expense')  # 默认统计支出
    
    if stats_type not in ['expense', 'income']:
        return error_response('type 参数必须是 expense 或 income', 400)
    
    # 基础查询
    query = Bill.query.filter_by(user_id=user_id, type=stats_type, in_trash=False)
    
    # 日期筛选
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Bill.date >= start)
        except ValueError:
            return error_response('start_date 格式错误', 400)
    
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Bill.date <= end)
        except ValueError:
            return error_response('end_date 格式错误', 400)
    
    # 按分类分组统计
    results = db.session.query(
        Bill.category_id,
        func.sum(Bill.amount).label('total_amount'),
        func.count(Bill.id).label('count')
    ).filter(query.whereclause).group_by(Bill.category_id).all()
    
    # 计算总金额（用于占比）
    total_amount = sum(r.total_amount for r in results) or 1  # 避免除零
    
    # 构建返回数据
    categories_data = []
    for result in results:
        category = Category.query.get(result.category_id)
        if category:
            amount = float(result.total_amount)
            categories_data.append({
                'category_id': category.id,
                'category_name': category.name,
                'icon': category.icon,
                'amount': round(amount, 2),
                'percent': round(amount / total_amount * 100, 2),
                'count': result.count
            })
    
    # 按金额降序排序
    categories_data.sort(key=lambda x: x['amount'], reverse=True)
    
    return success_response({
        'type': stats_type,
        'total': round(total_amount, 2),
        'categories': categories_data
    })


# ============================================================
# 接口 3：趋势图表数据（柱状图/折线图）
# ============================================================
@bp.route('/statistics/trend', methods=['GET'])
@jwt_required()
def get_trend():
    """
    获取趋势图数据
    参数：
        - start_date, end_date (必填)
        - interval: day(按日), month(按月), week(按周) (默认 day)
        - type: expense, income, all (默认 expense)
    返回：按时间维度的金额汇总
    """
    user_id = int(get_jwt_identity())
    
    # 获取参数
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    interval = request.args.get('interval', 'day')
    trend_type = request.args.get('type', 'expense')
    
    # 校验必填参数
    if not start_date or not end_date:
        return error_response('请提供 start_date 和 end_date 参数', 400)
    
    # 解析日期
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return error_response('日期格式错误，请使用 YYYY-MM-DD', 400)
    
    if start > end:
        return error_response('开始日期不能晚于结束日期', 400)
    
    # 基础查询
    query = Bill.query.filter(
        Bill.user_id == user_id,
        Bill.in_trash == False,
        Bill.date >= start,
        Bill.date <= end
    )
    
    # 类型筛选
    if trend_type != 'all':
        query = query.filter(Bill.type == trend_type)
    
    # 根据 interval 选择分组方式
    if interval == 'month':
        # 按月分组
        results = db.session.query(
            func.strftime('%Y-%m', Bill.date).label('period'),
            func.sum(Bill.amount).label('total')
        ).filter(query.whereclause).group_by('period').order_by('period').all()
        
        # 格式化返回数据
        trend_data = []
        for result in results:
            trend_data.append({
                'date': result.period,
                'amount': round(float(result.total) if result.total else 0, 2)
            })
    
    elif interval == 'week':
        # 按周分组（返回周起始日期）
        results = db.session.query(
            func.strftime('%Y-%W', Bill.date).label('week_num'),
            func.sum(Bill.amount).label('total')
        ).filter(query.whereclause).group_by('week_num').order_by('week_num').all()
        
        trend_data = []
        for result in results:
            trend_data.append({
                'week': result.week_num,
                'amount': round(float(result.total) if result.total else 0, 2)
            })
    
    else:
        # 按日分组（默认）
        # 生成日期范围内的所有日期
        date_range = []
        current = start
        while current <= end:
            date_range.append(current)
            current += timedelta(days=1)
        
        # 查询每日汇总
        daily_results = db.session.query(
            Bill.date,
            func.sum(Bill.amount).label('total')
        ).filter(query.whereclause).group_by(Bill.date).all()
        
        # 构建日期到金额的映射
        amount_map = {str(r.date): r.total for r in daily_results}
        
        # 填充所有日期
        trend_data = []
        for date in date_range:
            date_str = date.isoformat()
            amount = amount_map.get(date_str, 0)
            trend_data.append({
                'date': date_str,
                'amount': round(float(amount), 2)
            })
    
    # 计算平均值参考线
    if trend_data:
        avg_amount = sum(item['amount'] for item in trend_data) / len(trend_data)
    else:
        avg_amount = 0
    
    return success_response({
        'interval': interval,
        'type': trend_type,
        'start_date': start_date,
        'end_date': end_date,
        'avg_line': round(avg_amount, 2),
        'data': trend_data
    })


# ============================================================
# 接口 4：月份对比（同比/环比）
# ============================================================
@bp.route('/statistics/compare', methods=['GET'])
@jwt_required()
def get_compare():
    """
    获取月份对比数据（环比）
    参数：month (格式 YYYY-MM)
    返回：当前月与上个月的支出对比、变化率
    """
    user_id = int(get_jwt_identity())
    
    month_str = request.args.get('month')
    if not month_str:
        return error_response('请提供 month 参数 (格式 YYYY-MM)', 400)
    
    # 解析当前月份
    try:
        current_month = datetime.strptime(month_str, '%Y-%m').date()
    except ValueError:
        return error_response('月份格式错误，请使用 YYYY-MM', 400)
    
    # 计算上个月
    if current_month.month == 1:
        prev_month = current_month.replace(year=current_month.year - 1, month=12)
    else:
        prev_month = current_month.replace(month=current_month.month - 1)
    
    # 当前月的支出
    current_start = current_month.replace(day=1)
    if current_month.month == 12:
        current_end = current_month.replace(year=current_month.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        current_end = current_month.replace(month=current_month.month + 1, day=1) - timedelta(days=1)
    
    current_expense = db.session.query(func.sum(Bill.amount)).filter(
        Bill.user_id == user_id,
        Bill.type == 'expense',
        Bill.in_trash == False,
        Bill.date >= current_start,
        Bill.date <= current_end
    ).scalar() or 0
    
    # 上个月的支出
    prev_start = prev_month.replace(day=1)
    if prev_month.month == 12:
        prev_end = prev_month.replace(year=prev_month.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        prev_end = prev_month.replace(month=prev_month.month + 1, day=1) - timedelta(days=1)
    
    prev_expense = db.session.query(func.sum(Bill.amount)).filter(
        Bill.user_id == user_id,
        Bill.type == 'expense',
        Bill.in_trash == False,
        Bill.date >= prev_start,
        Bill.date <= prev_end
    ).scalar() or 0
    
    # 计算变化率
    if prev_expense > 0:
        change_rate = round((current_expense - prev_expense) / prev_expense * 100, 2)
    else:
        change_rate = 100 if current_expense > 0 else 0
    
    return success_response({
        'current_month': month_str,
        'current_expense': round(float(current_expense), 2),
        'prev_month': prev_month.strftime('%Y-%m'),
        'prev_expense': round(float(prev_expense), 2),
        'change': round(float(current_expense - prev_expense), 2),
        'change_rate': change_rate,
        'trend': 'up' if current_expense > prev_expense else 'down' if current_expense < prev_expense else 'stable'
    })