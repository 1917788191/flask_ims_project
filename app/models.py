from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects import mysql
from sqlalchemy import ForeignKey  # 导入 ForeignKey

# 关键修正：从 app 包的 __init__.py 中导入已创建的 db 实例
# 而不是在这里再次实例化 SQLAlchemy()
from app import db


class Role(db.Model):
    """
    角色模型：定义用户角色，如 Admin, Employee。
    """
    __tablename__ = 'roles'
    id = db.Column(mysql.BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))

    users = db.relationship('User', backref='role', lazy='dynamic')  # 与 User 模型建立一对多关系

    def __repr__(self):
        return f'<Role {self.name}>'


class User(UserMixin, db.Model):
    """
    用户模型：存储系统用户的信息。
    包含用户ID、用户名、密码哈希、邮箱和注册时间。
    """
    __tablename__ = 'users'  # 数据库表名
    # 修改为无符号大整数主键，并明确自增
    id = db.Column(mysql.BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False)  # 用户名，唯一且非空
    email = db.Column(db.String(120), unique=True, nullable=False)  # 邮箱，唯一且非空
    password_hash = db.Column(db.String(128), nullable=False)  # 密码哈希值，非空
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # 注册时间，默认为当前UTC时间

    # 添加 role_id 外键和 role 关系
    role_id = db.Column(mysql.BIGINT(unsigned=True), db.ForeignKey('roles.id'), nullable=False,
                        default=1)  # 默认角色ID，假设1是Employee

    # role = db.relationship('Role', backref='users') # 这一行在 Role 模型中已经定义了 backref，所以这里不需要再定义 relationship

    # 定义密码设置方法，将明文密码哈希后存储
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # 定义密码验证方法，检查输入的密码是否与存储的哈希值匹配
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        """
        对象的字符串表示，方便调试。
        """
        return f'<User {self.username}>'


class Item(db.Model):
    """
    物品模型：存储公司日常物品的信息。
    例如：文件夹、卫生纸、笔等。
    """
    __tablename__ = 'items'  # 数据库表名
    # 修改为无符号大整数主键，并明确自增
    id = db.Column(mysql.BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    name = db.Column(db.String(128), unique=True, nullable=False)  # 物品名称，唯一且非空
    description = db.Column(db.String(256))  # 物品描述，可为空
    unit = db.Column(db.String(32), nullable=False, default='个')  # 物品单位，例如：个、盒、卷
    reorder_level = db.Column(db.Integer, default=10)  # 重新订购水平，当库存低于此值时提醒

    # 与 Inventory 和 Transaction 表建立关系
    # 修正：移除 Item.inventory 关系中的 lazy='dynamic'
    inventory = db.relationship('Inventory', backref='item', uselist=False, lazy=True)  # <--- 关键修正
    transactions = db.relationship('Transaction', backref='item', lazy='dynamic')

    def __repr__(self):
        return f'<Item {self.name}>'


class Inventory(db.Model):
    """
    库存模型：存储每种物品当前的库存数量。
    """
    __tablename__ = 'inventory'  # 数据库表名
    # 修改为无符号大整数主键，并明确自增
    id = db.Column(mysql.BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    # item_id 关联物品ID，修改为无符号大整数外键
    item_id = db.Column(mysql.BIGINT(unsigned=True), db.ForeignKey('items.id'), unique=True, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)  # 当前库存数量，非空，默认为0
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 最后更新时间

    def __repr__(self):
        return f'<Inventory Item_ID: {self.item_id}, Quantity: {self.quantity}>'


class Transaction(db.Model):
    """
    交易模型：记录物品库存的每一次变动（增加或减少）。
    """
    __tablename__ = 'transactions'  # 数据库表名
    # 修改为无符号大整数主键，并明确自增
    id = db.Column(mysql.BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    # item_id 关联物品ID，修改为无符号大整数外键
    item_id = db.Column(mysql.BIGINT(unsigned=True), db.ForeignKey('items.id'), nullable=False)
    # user_id 关联用户ID，修改为无符号大整数外键
    user_id = db.Column(mysql.BIGINT(unsigned=True), db.ForeignKey('users.id'), nullable=True)  # 允许为空，因为有些交易可能不是由特定用户发起
    quantity_change = db.Column(db.Integer, nullable=False)  # 数量变化，正数表示增加，负数表示减少
    transaction_type = db.Column(db.String(50), nullable=False)  # 交易类型，例如 '入库' (in), '出库' (out), '调整' (adjust)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # 交易时间

    def __repr__(self):
        return f'<Transaction Item_ID: {self.item_id}, Change: {self.quantity_change}, Type: {self.transaction_type}>'
