from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db  # 确保 db 实例从 __init__.py 导入
from app.models import Item, Inventory, Transaction, User, Role  # 导入所有模型
from app.forms import ItemForm, InventoryAdjustmentForm  # 导入 main 蓝图需要的表单
from datetime import datetime
from functools import wraps

# 定义主蓝图
main_bp = Blueprint('main', __name__)


# --- 权限控制装饰器 (在 main 蓝图内定义，供 main 蓝图使用) ---
def role_required(role_name):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or not current_user.role or current_user.role.name != role_name:
                flash('您没有权限访问此页面。', 'danger')
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)

        return decorated_function

    return decorator


# --- 主页路由 ---
@main_bp.route('/')
@main_bp.route('/index')
@login_required
def index():
    """
    主页/仪表盘：显示库存概览和低库存提醒。
    """
    items = Item.query.all()
    low_stock_items = [item for item in items if item.inventory and item.inventory.quantity <= item.reorder_level]
    return render_template('index.html', title='主页', items=items, low_stock_items=low_stock_items)


# --- 物品管理路由 ---

@main_bp.route('/items')
@login_required
def items():  # 路由函数名称为 items
    """
    显示所有物品列表。
    """
    all_items = Item.query.all()
    return render_template('items/list.html', title='物品列表', items=all_items)


@main_bp.route('/items/add', methods=['GET', 'POST'])  # <--- 修正: methods=['GET', 'POST']
@login_required
@role_required('Admin')  # 只有管理员才能添加物品
def add_item():
    """
    添加新物品。
    """
    form = ItemForm()
    if form.validate_on_submit():
        existing_item = Item.query.filter_by(name=form.name.data).first()
        if existing_item:
            flash('物品名称已存在，请更换。', 'danger')
            return render_template('items/add.html', title='添加物品', form=form)

        item = Item(
            name=form.name.data,
            description=form.description.data,
            unit=form.unit.data,
            reorder_level=form.reorder_level.data
        )
        db.session.add(item)
        db.session.commit()

        inventory = Inventory(item_id=item.id, quantity=0)
        db.session.add(inventory)
        db.session.commit()

        flash(f'物品 "{item.name}" 添加成功！', 'success')  # 修正：使用 item.name
        return redirect(url_for('main.items'))
    return render_template('items/add.html', title='添加物品', form=form)


@main_bp.route('/items/edit/<int:item_id>', methods=['GET', 'POST'])  # <--- 修正: methods=['GET', 'POST']
@login_required
@role_required('Admin')  # 只有管理员才能编辑物品
def edit_item(item_id):
    """
    编辑现有物品信息。
    """
    item = Item.query.get_or_404(item_id)
    form = ItemForm(obj=item)
    # 确保 original_name 被设置，用于表单验证
    if request.method == 'GET':
        form.original_name = item.name

    if form.validate_on_submit():
        # 确保 original_name 在 POST 请求时也可用
        form.original_name = item.name

        item.name = form.name.data
        item.description = form.description.data
        item.unit = form.unit.data
        item.reorder_level = form.reorder_level.data
        db.session.commit()
        flash(f'物品 "{item.name}" 更新成功！', 'success')
        return redirect(url_for('main.items'))
    return render_template('items/edit.html', title='编辑物品', form=form, item=item)


@main_bp.route('/items/delete/<int:item_id>', methods=['POST'])  # <--- 修正: methods=['POST']
@login_required
@role_required('Admin')  # 只有管理员才能删除物品
def delete_item(item_id):
    """
    删除物品。
    """
    item = Item.query.get_or_404(item_id)
    try:
        Inventory.query.filter_by(item_id=item.id).delete()
        Transaction.query.filter_by(item_id=item.id).delete()
        db.session.delete(item)
        db.session.commit()
        flash('物品及其相关库存和交易记录已删除。', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除物品时发生错误: {e}', 'danger')
    return redirect(url_for('main.items'))


# --- 库存管理路由 ---
@main_bp.route('/inventory')
@login_required
def inventory():
    """
    显示所有物品的当前库存。
    """
    all_inventory = db.session.query(Item, Inventory).outerjoin(Inventory).all()
    return render_template('inventory/list.html', title='库存管理', inventory_items=all_inventory)


@main_bp.route('/inventory/adjust/<int:item_id>', methods=['GET', 'POST'])  # <--- 修正: methods=['GET', 'POST']
@login_required
def adjust_inventory(item_id):
    inventory_item = Inventory.query.filter_by(item_id=item_id).first_or_404()
    item_name = inventory_item.item.name

    form = InventoryAdjustmentForm()
    if form.validate_on_submit():
        quantity_change = form.quantity_change.data
        transaction_type = form.transaction_type.data

        if quantity_change < 0 and (inventory_item.quantity + quantity_change < 0):  # 修正：使用 inventory_item.quantity
            flash('出库数量不能大于当前库存！', 'danger')
            return render_template('inventory/adjust.html', title=f'调整 {item_name} 库存', form=form,
                                   item=inventory_item.item)

        new_transaction = Transaction(
            item_id=item_id,
            user_id=current_user.id,
            quantity_change=quantity_change,
            transaction_type=transaction_type
        )
        db.session.add(new_transaction)

        inventory_item.quantity += quantity_change
        inventory_item.last_updated = datetime.utcnow()

        db.session.commit()
        flash(f'物品 "{item_name}" 库存已调整 {quantity_change}。当前库存: {inventory_item.quantity}', 'success')
        return redirect(url_for('main.inventory'))

    return render_template('inventory/adjust.html', title=f'调整 {item_name} 库存', form=form, item=inventory_item.item)


# --- 交易记录路由 ---
@main_bp.route('/transactions')
@login_required
def transactions():
    """
    显示所有交易记录。
    """
    all_transactions = db.session.query(Transaction, Item, User).join(Item).outerjoin(User).order_by(
        Transaction.timestamp.desc()).all()
    return render_template('transactions/transactions.html', title='交易记录', transactions=all_transactions)
