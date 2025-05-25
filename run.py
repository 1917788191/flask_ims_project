from app import create_app, db
# 导入所有模型，以便在 shell 中使用，也确保它们被加载
from app.models import User, Item, Inventory, Transaction, Role

# 调用应用程序工厂函数创建 Flask 应用实例
app = create_app()


# 移除 db.create_all()，数据库将通过 Flask-Migrate 命令管理

@app.shell_context_processor
def make_shell_context():
    """
    为 Flask shell 提供额外的上下文，方便调试。
    在 `flask shell` 命令下，可以直接访问 db, User, Item 等对象。
    """
    return {'db': db, 'User': User, 'Item': Item, 'Inventory': Inventory, 'Transaction': Transaction, 'Role': Role}


if __name__ == '__main__':
    # 如果是直接运行此脚本，则启动 Flask 开发服务器
    # debug=True 会在代码修改时自动重启服务器，并提供调试信息
    app.run(debug=True)
