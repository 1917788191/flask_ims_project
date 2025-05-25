import os
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()


class Config:
    """
    应用程序配置类。
    从环境变量中加载数据库URI和SECRET_KEY。
    """
    # 从 .env 文件获取数据库连接字符串
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')  # <-- 已修正为 'DATABASE_URL'
    # 关闭SQLAlchemy事件追踪，减少内存消耗
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 从 .env 文件获取用于会话加密的密钥
    SECRET_KEY = os.getenv('SECRET_KEY') or 'a_very_secret_key_fallback'
