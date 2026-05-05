from flask import Blueprint, request
from extensions import db, bcrypt
from models import User
from utils import success_response, error_response
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from datetime import timedelta

bp = Blueprint('auth', __name__)

# 用户注册
@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # 参数校验
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not username or not password:
        return error_response('用户名和密码不能为空', 400)
    
    # 检查用户名是否已存在
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return error_response('用户名已存在', 409)
    
    # 创建新用户
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(
        username=username,
        password_hash=hashed_password,
        email=email
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return success_response({
        'id': new_user.id,
        'username': new_user.username,
        'email': new_user.email
    }, '注册成功', 201)


# 用户登录
@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return error_response('用户名和密码不能为空', 400)
    
    # 查找用户
    user = User.query.filter_by(username=username).first()
    if not user:
        return error_response('用户名或密码错误', 401)
    
    # 验证密码
    if not bcrypt.check_password_hash(user.password_hash, password):
        return error_response('用户名或密码错误', 401)
    
    # 生成 JWT token（有效期 7 天）
    access_token = create_access_token(
        identity=str(user.id),
        expires_delta=timedelta(days=7)
    )
    
    return success_response({
        'token': access_token,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    }, '登录成功')


# 获取当前用户信息（需要认证）
@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return error_response('用户不存在', 404)
    
    return success_response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'created_at': user.created_at.isoformat() if user.created_at else None
    })