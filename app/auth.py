from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app import db  # 导入 db 实例
from app.models import User, Role  # 导入 User 和 Role 模型
from app.forms import LoginForm, RegistrationForm  # 导入登录和注册表单

# 定义认证蓝图
auth_bp = Blueprint('auth', __name__, template_folder='templates')  # 指定模板文件夹为 auth/templates


# 登录路由
@auth_bp.route('/login', methods=['GET', 'POST'])  # <--- 修正：添加 methods=['GET', 'POST']
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('无效的用户名或密码', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)

        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.index')
        return redirect(next_page)

    return render_template('auth/login.html', title='登录', form=form)


# 退出登录路由
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已成功退出登录。', 'info')
    return redirect(url_for('main.index'))


# 用户注册路由
@auth_bp.route('/register', methods=['GET', 'POST'])  # <--- 修正：添加 methods=['GET', 'POST']
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        employee_role = Role.query.filter_by(name='Employee').first()
        if not employee_role:
            flash('系统未配置默认员工角色，请联系管理员。', 'danger')
            return redirect(url_for('auth.register'))

        user = User(
            username=form.username.data,
            email=form.email.data,
            role=employee_role
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('恭喜，您已成功注册！', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', title='注册', form=form)
