import random
import bcrypt
from datetime import datetime, timedelta
from flask import Blueprint, request, g
from marshmallow import ValidationError

from models import db
from models.user import User
from schemas.auth import SendCodeSchema, RegisterSchema, LoginSchema
from utils.response import success, fail
from utils.auth import generate_token, set_token_cookie, clear_token_cookie, login_required

auth_bp = Blueprint('auth', __name__)

# In-memory SMS code store: {phone: {code, expires_at}}
_sms_codes = {}


def _clean_expired_codes():
    now = datetime.utcnow()
    expired = [p for p, v in _sms_codes.items() if v['expires_at'] < now]
    for p in expired:
        del _sms_codes[p]


@auth_bp.route('/api/auth/send-code', methods=['POST'])
def send_code():
    json_data = request.get_json(silent=True)
    if not json_data:
        return fail('请提供JSON数据')

    try:
        data = SendCodeSchema().load(json_data)
    except ValidationError as e:
        return fail(str(e.messages))

    _clean_expired_codes()

    phone = data['phone']
    code = str(random.randint(100000, 999999))
    _sms_codes[phone] = {
        'code': code,
        'expires_at': datetime.utcnow() + timedelta(minutes=5)
    }

    # Simulate SMS: print to console
    print(f"\n{'='*50}")
    print(f"[Tbao SMS] 验证码已发送至 {phone}")
    print(f"[Tbao SMS] 验证码: {code}")
    print(f"[Tbao SMS] 有效期: 5分钟")
    print(f"{'='*50}\n")

    return success(msg='验证码已发送，请查看控制台输出')


@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    json_data = request.get_json(silent=True)
    if not json_data:
        return fail('请提供JSON数据')

    try:
        data = RegisterSchema().load(json_data)
    except ValidationError as e:
        return fail(str(e.messages))

    username = data['username']
    phone = data['phone']
    password = data['password']

    # Check uniqueness
    if User.query.filter_by(username=username).first():
        return fail('用户名已存在')
    if User.query.filter_by(phone=phone).first():
        return fail('手机号已被注册')

    # Hash password and create user
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    try:
        user = User(username=username, phone=phone, password_hash=password_hash)
        db.session.add(user)
        db.session.commit()

        # Auto-login: generate token and set cookie
        token = generate_token(user.id)
        resp = success(data=user.to_dict(), msg='注册成功')
        set_token_cookie(resp, token)
        return resp
    except Exception as e:
        db.session.rollback()
        return fail(f'注册失败: {str(e)}')


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    json_data = request.get_json(silent=True)
    if not json_data:
        return fail('请提供JSON数据')

    try:
        data = LoginSchema().load(json_data)
    except ValidationError as e:
        return fail(str(e.messages))

    # Phone + SMS code login
    if data.get('phone') and data.get('code'):
        phone = data['phone']
        code = data['code']

        _clean_expired_codes()
        cached = _sms_codes.get(phone)

        if not cached:
            return fail('请先获取验证码')
        if cached['code'] != code:
            return fail('验证码错误')
        if cached['expires_at'] < datetime.utcnow():
            del _sms_codes[phone]
            return fail('验证码已过期')

        # Delete used code
        del _sms_codes[phone]

        user = User.query.filter_by(phone=phone).first()
        if not user:
            return fail('该手机号未注册')

        token = generate_token(user.id)
        resp = success(data=user.to_dict(), msg='登录成功')
        set_token_cookie(resp, token)
        return resp

    # Username + password login
    if data.get('username') and data.get('password'):
        username = data['username']
        password = data['password']

        user = User.query.filter_by(username=username).first()
        if not user:
            return fail('用户名不存在')

        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return fail('密码错误')

        token = generate_token(user.id)
        resp = success(data=user.to_dict(), msg='登录成功')
        set_token_cookie(resp, token)
        return resp

    # Phone + password login
    if data.get('phone') and data.get('password'):
        phone = data['phone']
        password = data['password']

        user = User.query.filter_by(phone=phone).first()
        if not user:
            return fail('手机号未注册')

        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return fail('密码错误')

        token = generate_token(user.id)
        resp = success(data=user.to_dict(), msg='登录成功')
        set_token_cookie(resp, token)
        return resp

    return fail('请提供有效的登录凭据')


@auth_bp.route('/api/auth/me', methods=['GET'])
@login_required
def get_me():
    user = User.query.get(g.user_id)
    if not user:
        return fail('用户不存在', 404)
    return success(data=user.to_dict())


@auth_bp.route('/api/auth/logout', methods=['POST'])
@login_required
def logout():
    resp = success(msg='已退出登录')
    clear_token_cookie(resp)
    return resp
