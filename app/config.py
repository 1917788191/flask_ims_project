import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量。
# 这行代码在本地开发时非常重要，它会读取您在项目根目录创建的 .env 文件。
# 在生产服务器上，环境变量将由服务器环境本身提供，这行代码不会有副作用。
load_dotenv()


class Config:
    # SECRET_KEY 用于会话安全，在生产环境中必须非常复杂且保密。
    # 它首先尝试从环境变量 'SECRET_KEY' 获取。
    # 如果环境变量不存在（通常在本地开发时），则使用一个回退值。
    # 生产环境部署时，您需要在服务器上设置 SECRET_KEY 环境变量为一个强随机字符串。
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-long-and-random-secret-key-for-development'

    # 数据库连接 URI。
    # 它首先尝试从环境变量 'DATABASE_URL' 获取。
    # 如果环境变量不存在（通常在本地开发时），则使用您本地 MySQL 数据库的连接字符串。
    # 生产环境部署时，您需要在服务器上设置 DATABASE_URL 环境变量为远程数据库的连接字符串。
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'mysql+mysqlconnector://root:your_local_mysql_password@localhost/office_ims_db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 禁用 SQLAlchemy 事件追踪，可以节省内存和 CPU。

    # 日志配置（示例，您可以根据需要调整）
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')  # 如果设置为True，日志会输出到标准输出，适合容器化环境

    # 邮件配置（如果您有邮件功能的话，此处为示例）
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['your-admin-email@example.com']  # 管理员邮箱列表

    # 分页大小（如果您有分页列表的话）
    ITEMS_PER_PAGE = 20
