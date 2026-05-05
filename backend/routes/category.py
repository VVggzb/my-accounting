from flask import Blueprint, request
from extensions import db
from models import Category
from utils import success_response, error_response
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('category', __name__)

# 获取当前用户的所有分类
@bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    user_id = int(get_jwt_identity())
    
    # 查询用户的分类（未删除的）
    categories = Category.query.filter_by(
        user_id=user_id, 
        in_trash=False
    ).all()
    
    return success_response({
        'categories': [{
            'id': c.id,
            'name': c.name,
            'type': c.type,
            'icon': c.icon
        } for c in categories]
    })


# 创建新分类
@bp.route('/category', methods=['POST'])
@jwt_required()
def create_category():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    name = data.get('name')
    category_type = data.get('type')  # 'expense' 或 'income'
    icon = data.get('icon', '💡')
    
    if not name:
        return error_response('分类名称不能为空', 400)
    
    if category_type not in ['expense', 'income']:
        return error_response('类型必须是 expense 或 income', 400)
    
    # 检查是否已存在同名分类
    existing = Category.query.filter_by(
        user_id=user_id, 
        name=name,
        in_trash=False
    ).first()
    
    if existing:
        return error_response('分类名称已存在', 409)
    
    new_category = Category(
        user_id=user_id,
        name=name,
        type=category_type,
        icon=icon
    )
    
    db.session.add(new_category)
    db.session.commit()
    
    return success_response({
        'id': new_category.id,
        'name': new_category.name,
        'type': new_category.type,
        'icon': new_category.icon
    }, '创建成功', 201)


# 编辑分类
@bp.route('/category/<int:category_id>', methods=['PUT'])
@jwt_required()
def update_category(category_id):
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    category = Category.query.filter_by(
        id=category_id, 
        user_id=user_id,
        in_trash=False
    ).first()
    
    if not category:
        return error_response('分类不存在', 404)
    
    if 'name' in data:
        category.name = data['name']
    if 'icon' in data:
        category.icon = data['icon']
    
    db.session.commit()
    
    return success_response({
        'id': category.id,
        'name': category.name,
        'type': category.type,
        'icon': category.icon
    }, '更新成功')


# 删除分类（软删除）
@bp.route('/category/<int:category_id>', methods=['DELETE'])
@jwt_required()
def delete_category(category_id):
    user_id = int(get_jwt_identity())
    
    category = Category.query.filter_by(
        id=category_id, 
        user_id=user_id,
        in_trash=False
    ).first()
    
    if not category:
        return error_response('分类不存在', 404)
    
    category.in_trash = True
    db.session.commit()
    
    return success_response({}, '删除成功')