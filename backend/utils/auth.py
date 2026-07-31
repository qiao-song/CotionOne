import jwt
import datetime
from functools import wraps
from flask import request, g, current_app
from utils.response import fail


def generate_token(user_id: int) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=current_app.config.get('JWT_EXPIRY_DAYS', 7)),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')


def set_token_cookie(response, token: str):
    response.set_cookie(
        current_app.config['JWT_COOKIE_NAME'],
        token,
        httponly=True,
        secure=False,
        samesite='Lax',
        max_age=current_app.config.get('JWT_EXPIRY_DAYS', 7) * 86400,
        path='/'
    )


def clear_token_cookie(response):
    response.delete_cookie(current_app.config['JWT_COOKIE_NAME'], path='/')


def decode_token(token: str):
    try:
        return jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get(current_app.config['JWT_COOKIE_NAME'])
        if not token:
            return fail('请先登录', 401)
        payload = decode_token(token)
        if payload is None:
            return fail('登录已过期，请重新登录', 401)
        g.user_id = payload['user_id']
        return f(*args, **kwargs)
    return decorated
