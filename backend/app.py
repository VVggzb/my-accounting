from flask import Flask
from config import Config
from extensions import db, migrate, jwt, bcrypt, cors

# 导入模型
from models import User, Category, Bill, BillTemplate

# 导入蓝图
from routes import auth, category, bill, statistics

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    
    # ============================================================
    # CORS 配置 - 解决跨域问题
    # ============================================================
    # 方式1：允许所有来源（开发环境推荐）
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    
    # 方式2：只允许特定来源（更安全，生产环境用）
    # cors.init_app(app, resources={r"/api/*": {"origins": ["http://localhost:5500", "http://127.0.0.1:5500"]}})
    
    # 注册蓝图
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    app.register_blueprint(category.bp, url_prefix='/api')
    app.register_blueprint(bill.bp, url_prefix='/api')
    app.register_blueprint(statistics.bp, url_prefix='/api')
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)