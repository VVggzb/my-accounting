from extensions import db
from datetime import datetime

# 关联表：账单和模板的多对多（暂不需要，先忽略）

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    categories = db.relationship('Category', backref='user', lazy=True, cascade='all, delete-orphan')
    bills = db.relationship('Bill', backref='user', lazy=True, cascade='all, delete-orphan')
    templates = db.relationship('BillTemplate', backref='user', lazy=True, cascade='all, delete-orphan')


class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'expense' 或 'income'
    icon = db.Column(db.String(50), default='💡')
    in_trash = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联
    bills = db.relationship('Bill', backref='category', lazy=True)


class Bill(db.Model):
    __tablename__ = 'bills'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'expense' 或 'income'
    date = db.Column(db.Date, nullable=False)
    note = db.Column(db.String(200), nullable=True)
    tags = db.Column(db.String(200), nullable=True)  # 逗号分隔
    account = db.Column(db.String(50), nullable=True)  # 账户：微信/支付宝/现金等
    discount = db.Column(db.Float, default=0)  # 优惠金额
    attachment = db.Column(db.String(200), nullable=True)  # 图片路径
    reimbursement_status = db.Column(db.String(20), default='none')  # 'none', 'pending', 'reimbursed'
    is_template = db.Column(db.Boolean, default=False)  # 是否为模板
    parent_refund_id = db.Column(db.Integer, db.ForeignKey('bills.id'), nullable=True)  # 退款关联原账单
    in_trash = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 自关联退款
    refund_relation = db.relationship('Bill', remote_side=[id], backref='original_bill', foreign_keys=[parent_refund_id])


class BillTemplate(db.Model):
    __tablename__ = 'bill_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    template_name = db.Column(db.String(50), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(10), nullable=False)
    note = db.Column(db.String(200), nullable=True)
    tags = db.Column(db.String(200), nullable=True)
    account = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)