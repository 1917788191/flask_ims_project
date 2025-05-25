from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
from flask_moment import Moment
from flask_wtf import CSRFProtect
from flask_bootstrap import Bootstrap  # 确保这里是导入 Bootstrap

# 从 .env 文件加载环境变量
load_dotenv()

# 全局实例化扩展，但不绑定到具体的 Flask 应用
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请登录以访问此页面。'
login_manager.login_message_category = 'info'
moment = Moment()
csrf = CSRFProtect()
bootstrap = Bootstrap()  # 实例化 Bootstrap


def create_app():
    app = Flask(__name__)

    # 配置应用
    # 修正：从 app.config.from_object('config.Config') 改为 'app.config.Config'
    app.config.from_object('app.config.Config')  # <--- 关键修正：修改配置导入路径

    # 确保 SECRET_KEY 和 DATABASE_URI 被正确设置
    # app.config.from_object 应该已经处理了这些，但为了确保，可以保留 os.environ.get 的逻辑
    # 注意：如果 config.py 已经正确加载，这些行可能不是严格必要的，但保留它们可以作为额外的安全网
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'you-will-never-guess-my-secret-key-for-flask'

    database_uri = os.environ.get('DATABASE_URL')
    if database_uri:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_uri.replace('your_password',
                                                                     '12345678')  # 请将 '12345678' 替换为你的实际MySQL root密码
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:12345678@localhost/office_ims_db'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 初始化所有 Flask 扩展，将它们绑定到当前的 app 实例
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    moment.init_app(app)
    csrf.init_app(app)
    bootstrap.init_app(app)

    # 关键修正：在 db.init_app(app) 之后才导入模型和蓝图
    from app.models import User, Item, Inventory, Transaction, Role  # 导入所有模型
    from app.main import main_bp
    from app.auth import auth_bp
    from app.admin import admin_bp

    # 注册蓝图
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Flask-Login 的用户加载回调函数
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # 配置日志记录 (可选，但推荐用于生产环境)
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/ims_app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('IMS App startup')

    return app
