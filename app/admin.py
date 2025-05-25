from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import login_required, current_user
from app import db  # 导入 db 实例
from app.models import User, Item, Role, Transaction  # 导入 User, Item, Role, Transaction 模型
from app.forms import UserForm  # <--- 修正：导入 UserForm
from functools import wraps  # 确保导入 wraps

# 定义管理蓝图
admin_bp = Blueprint('admin', __name__, url_prefix='/admin', template_folder='templates')


# 自定义装饰器：检查用户是否是管理员
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.role or current_user.role.name != 'Admin':
            flash('您没有权限访问此页面。', 'danger')
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


# 管理仪表板路由
@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    user_count = User.query.count()
    item_count = Item.query.count()
    return render_template('admin/dashboard.html', title='管理仪表板',
                           user_count=user_count, item_count=item_count)


# 用户管理列表
@admin_bp.route('/users')
@admin_required
def users_admin():
    users = User.query.all()
    return render_template('admin/users_admin.html', title='用户管理', users=users)


# 添加用户路由
@admin_bp.route('/user/add', methods=['GET', 'POST'])
@admin_required
def add_user_admin():
    form = UserForm()  # 使用 UserForm 来添加新用户
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=Role.query.get(form.role.data)
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('用户添加成功！', 'success')
        return redirect(url_for('admin.users_admin'))
    return render_template('admin/add_user_admin.html', title='添加用户', form=form)


# 编辑用户路由
@admin_bp.route('/user/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user_admin(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)  # 用现有数据填充表单

    # 确保 original_username 和 original_email 被设置，用于表单验证
    if request.method == 'GET':
        form.original_username.data = user.username
        form.original_email.data = user.email
        form.role.data = user.role_id  # 确保角色选择框预填充当前用户的角色

    if form.validate_on_submit():
        # 在 POST 请求时，确保 original_username 和 original_email 再次被设置
        # 这是因为 WTForms 的 obj=user 只在 GET 请求时填充数据
        form.original_username.data = user.username
        form.original_email.data = user.email

        user.username = form.username.data
        user.email = form.email.data
        user.role = Role.query.get(form.role.data)
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('用户信息更新成功！', 'success')
        return redirect(url_for('admin.users_admin'))

    return render_template('admin/edit_user_admin.html', title='编辑用户', form=form, user=user)


# 删除用户路由
@admin_bp.route('/user/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('您不能删除您自己的管理员账户！', 'danger')
        return redirect(url_for('admin.users_admin'))

    Transaction.query.filter_by(user_id=user.id).delete()

    db.session.delete(user)
    db.session.commit()
    flash('用户已删除！', 'info')
    return redirect(url_for('admin.users_admin'))


# 角色管理路由
@admin_bp.route('/roles')
@admin_required
def manage_roles():
    roles = Role.query.all()
    return render_template('admin/roles.html', title='角色管理', roles=roles)
