from flask import Blueprint, request
from extensions import db
from models import Bill, Category
from utils import success_response, error_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

bp = Blueprint('bill', __name__)


# ============================================================
# 创建账单
# ============================================================
@bp.route('/bill', methods=['POST'])
@jwt_required()
def create_bill():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    # 必填字段校验
    category_id = data.get('category_id')
    amount = data.get('amount')
    bill_type = data.get('type')  # expense 或 income
    date_str = data.get('date')
    
    if not category_id or not amount or not bill_type or not date_str:
        return error_response('缺少必填字段', 400)
    
    # 验证分类是否存在且属于当前用户
    category = Category.query.filter_by(id=category_id, user_id=user_id, in_trash=False).first()
    if not category:
        return error_response('分类不存在', 404)
    
    # 验证类型与分类类型是否匹配
    if category.type != bill_type:
        return error_response('账单类型与分类类型不匹配', 400)
    
    # 解析日期
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return error_response('日期格式错误，请使用 YYYY-MM-DD 格式', 400)
    
    # 创建账单
    new_bill = Bill(
        user_id=user_id,
        category_id=category_id,
        amount=amount,
        type=bill_type,
        date=date,
        note=data.get('note', ''),
        tags=data.get('tags', ''),
        account=data.get('account', ''),
        discount=data.get('discount', 0),
        attachment=data.get('attachment', ''),
        reimbursement_status=data.get('reimbursement_status', 'none'),
        is_template=False,
        in_trash=False
    )
    
    db.session.add(new_bill)
    db.session.commit()
    
    return success_response({
        'id': new_bill.id,
        'category_id': new_bill.category_id,
        'category_name': category.name,
        'amount': new_bill.amount,
        'type': new_bill.type,
        'date': new_bill.date.isoformat(),
        'note': new_bill.note,
        'account': new_bill.account
    }, '账单创建成功', 201)


# ============================================================
# 获取账单列表（支持筛选）
# ============================================================
@bp.route('/bills', methods=['GET'])
@jwt_required()
def get_bills():
    user_id = int(get_jwt_identity())
    
    # 获取查询参数
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category_id = request.args.get('category_id')
    bill_type = request.args.get('type')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # 基础查询（未删除的账单）
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
    
    # 分类筛选
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # 类型筛选
    if bill_type and bill_type in ['expense', 'income']:
        query = query.filter_by(type=bill_type)
    
    # 分页
    paginated = query.order_by(Bill.date.desc()).paginate(page=page, per_page=per_page)
    
    # 构建返回数据
    bills = []
    for bill in paginated.items:
        category = Category.query.get(bill.category_id)
        bills.append({
            'id': bill.id,
            'category_id': bill.category_id,
            'category_name': category.name if category else '未知',
            'amount': float(bill.amount),
            'type': bill.type,
            'date': bill.date.isoformat(),
            'note': bill.note,
            'tags': bill.tags,
            'account': bill.account,
            'discount': float(bill.discount) if bill.discount else 0,
            'reimbursement_status': bill.reimbursement_status
        })
    
    return success_response({
        'bills': bills,
        'total': paginated.total,
        'page': page,
        'per_page': per_page,
        'pages': paginated.pages
    })


# ============================================================
# 获取单条账单详情（编辑时用）
# ============================================================
@bp.route('/bill/<int:bill_id>', methods=['GET'])
@jwt_required()
def get_bill_detail(bill_id):
    user_id = int(get_jwt_identity())
    
    bill = Bill.query.filter_by(id=bill_id, user_id=user_id, in_trash=False).first()
    if not bill:
        return error_response('账单不存在', 404)
    
    category = Category.query.get(bill.category_id)
    
    return success_response({
        'id': bill.id,
        'category_id': bill.category_id,
        'category_name': category.name if category else '未知',
        'amount': float(bill.amount),
        'type': bill.type,
        'date': bill.date.isoformat(),
        'note': bill.note or '',
        'account': bill.account or '',
        'tags': bill.tags or '',
        'discount': float(bill.discount) if bill.discount else 0,
        'reimbursement_status': bill.reimbursement_status or 'none'
    })


# ============================================================
# 更新账单（编辑保存）
# ============================================================
@bp.route('/bill/<int:bill_id>', methods=['PUT'])
@jwt_required()
def update_bill(bill_id):
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    bill = Bill.query.filter_by(id=bill_id, user_id=user_id, in_trash=False).first()
    if not bill:
        return error_response('账单不存在', 404)
    
    # 更新分类
    if 'category_id' in data:
        category = Category.query.filter_by(id=data['category_id'], user_id=user_id).first()
        if not category:
            return error_response('分类不存在', 404)
        bill.category_id = data['category_id']
    
    # 更新金额
    if 'amount' in data:
        bill.amount = data['amount']
    
    # 更新类型
    if 'type' in data:
        if data['type'] not in ['expense', 'income']:
            return error_response('类型必须是 expense 或 income', 400)
        bill.type = data['type']
    
    # 更新日期
    if 'date' in data:
        try:
            bill.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return error_response('日期格式错误，请使用 YYYY-MM-DD', 400)
    
    # 更新备注
    if 'note' in data:
        bill.note = data['note']
    
    # 更新账户
    if 'account' in data:
        bill.account = data['account']
    
    db.session.commit()
    
    return success_response({}, '账单更新成功')


# ============================================================
# 删除账单（软删除）
# ============================================================
@bp.route('/bill/<int:bill_id>', methods=['DELETE'])
@jwt_required()
def delete_bill(bill_id):
    user_id = int(get_jwt_identity())
    
    bill = Bill.query.filter_by(id=bill_id, user_id=user_id, in_trash=False).first()
    if not bill:
        return error_response('账单不存在', 404)
    
    bill.in_trash = True
    db.session.commit()
    
    return success_response({}, '账单删除成功')