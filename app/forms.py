from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField, SelectField, \
    HiddenField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length, NumberRange, Optional
from app.models import User, Item, Role  # 导入 User, Item, Role 模型


# 物品表单 (ItemForm) - 假设你的 Item 模型有 name, description, reorder_level 字段
class ItemForm(FlaskForm):
    name = StringField('物品名称', validators=[DataRequired(),
                                               Length(min=2, max=128, message='物品名称长度必须在2到128个字符之间。')])
    description = TextAreaField('物品描述', validators=[Length(max=500, message='描述不能超过500个字符。'), Optional()])
    unit = StringField('单位', validators=[DataRequired(), Length(min=1, max=32)], default='个')  # <--- 重新添加 unit 字段
    reorder_level = IntegerField('补货点',
                                 validators=[DataRequired(), NumberRange(min=0, message='补货点必须是非负整数。')])
    submit = SubmitField('提交')

    # 自定义验证：检查物品名称是否已存在 (仅针对新增，或编辑时排除自身)
    def validate_name(self, name):
        # 假设在编辑模式下，表单会有一个 item_id 属性来存储当前物品的ID
        # 如果是新增，self.item_id 可能不存在或为 None
        if hasattr(self, 'item_id') and self.item_id.data:
            item = Item.query.filter(Item.name == name.data, Item.id != self.item_id.data).first()
        else:
            item = Item.query.filter_by(name=name.data).first()

        if item is not None:
            raise ValidationError('此物品名称已存在，请使用其他名称。')


# 用户表单 (UserForm) - 用于编辑现有用户，可能包含角色选择
class UserForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(),
                                                 Length(min=2, max=64, message='用户名长度必须在2到64个字符之间。')])
    email = StringField('邮箱', validators=[DataRequired(), Email(message='请输入有效的邮箱地址。')])
    password = PasswordField('密码', validators=[Optional(), Length(min=6, message='密码至少需要6个字符。')])  # 编辑时密码可不填
    password2 = PasswordField('重复密码', validators=[EqualTo('password', message='两次输入的密码不一致。')])

    role = SelectField('角色', coerce=int, validators=[DataRequired(message='请选择一个角色。')])

    submit = SubmitField('提交')

    # 用于编辑时跳过自身验证的隐藏字段
    original_username = HiddenField()
    original_email = HiddenField()

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        # 动态加载角色选项
        self.role.choices = [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]

    def validate_username(self, username):
        # 如果是编辑模式，还需要排除自身，这里假设 UserForm 的实例会有 original_username
        if self.original_username.data and self.original_username.data == username.data:
            return  # 如果用户名没有改变，跳过验证
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('此用户名已存在，请使用其他用户名。')

    def validate_email(self, email):
        # 如果是编辑模式，还需要排除自身，这里假设 UserForm 的实例会有 original_email
        if self.original_email.data and self.original_email.data == email.data:
            return  # 如果邮箱没有改变，跳过验证
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('此邮箱已被注册，请使用其他邮箱。')


# 注册表单 (RegistrationForm) - 用于新用户注册
class RegistrationForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(),
                                                 Length(min=2, max=64, message='用户名长度必须在2到64个字符之间。')])
    email = StringField('邮箱', validators=[DataRequired(), Email(message='请输入有效的邮箱地址。')])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6, message='密码至少需要6个字符。')])
    password2 = PasswordField('重复密码',
                              validators=[DataRequired(), EqualTo('password', message='两次输入的密码不一致。')])
    submit = SubmitField('注册')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('此用户名已存在，请使用其他用户名。')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('此邮箱已被注册，请使用其他邮箱。')


# 登录表单
class LoginForm(FlaskForm):
    username = StringField('用户名', validators=[DataRequired(message='请输入用户名。')])
    password = PasswordField('密码', validators=[DataRequired(message='请输入密码。')])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')


# 库存调整表单 (InventoryAdjustmentForm) - 假设你的 Transaction 模型有 item_id, quantity, transaction_type 字段
class InventoryAdjustmentForm(FlaskForm):
    quantity_change = IntegerField('数量变化', validators=[DataRequired(message='请输入数量变化。')])
    transaction_type = StringField('交易类型', validators=[DataRequired(), Length(min=2, max=50)])
    submit = SubmitField('调整库存')


# 交易表单 (TransactionForm) - 假设你的 Transaction 模型有 item_id, quantity, transaction_type 字段
class TransactionForm(FlaskForm):
    # item 字段通常是下拉选择框，让用户选择要操作的物品
    item = SelectField('物品', coerce=int, validators=[DataRequired(message='请选择物品。')])

    quantity = IntegerField('数量', validators=[DataRequired(), NumberRange(min=1, message='数量必须是正整数。')])

    # 交易类型：入库 (in) 或 出库 (out)
    transaction_type = SelectField('交易类型', choices=[('in', '入库'), ('out', '出库')],
                                   validators=[DataRequired(message='请选择交易类型。')])

    submit = SubmitField('记录交易')

    def __init__(self, *args, **kwargs):
        super(TransactionForm, self).__init__(*args, **kwargs)
        # 动态加载物品选项
        self.item.choices = [(item.id, item.name) for item in Item.query.order_by(Item.name).all()]

    # 自定义验证：出库时检查库存是否足够
    def validate_quantity(self, quantity):
        if self.transaction_type.data == 'out':  # 如果是出库操作
            selected_item_id = self.item.data
            selected_item = Item.query.get(selected_item_id)
            if selected_item and selected_item.inventory.quantity < quantity.data:  # 修正：使用 selected_item.inventory.quantity
                raise ValidationError(
                    f'库存不足。当前 "{selected_item.name}" 仅剩 {selected_item.inventory.quantity} 个。')
