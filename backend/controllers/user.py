import os
import bcrypt
from flask import Blueprint, request, g, url_for
from marshmallow import ValidationError
from sqlalchemy import func

from models import db
from models.user import User
from models.goods import Goods
from models.order import Order
from schemas.user import ChangePasswordSchema
from utils.response import success, fail
from utils.auth import login_required
from utils.upload import save_upload

user_bp = Blueprint('user', __name__)


@user_bp.route('/api/seller/search', methods=['GET'])
def search_sellers():
    """Search sellers by keyword (username)."""
    keyword = request.args.get('keyword', '').strip()
    if not keyword:
        return success(data=[])

    users = User.query.filter(
        User.username.contains(keyword)
    ).limit(20).all()

    results = []
    for u in users:
        goods_count = Goods.query.filter(
            Goods.seller_id == u.id,
            Goods.status == 1,
            Goods.deleted_at.is_(None)
        ).count()
        results.append({
            'id': u.id,
            'username': u.username,
            'avatar': u.avatar or '/static/default.png',
            'goods_count': goods_count
        })

    return success(data=results)


@user_bp.route('/api/seller/<int:seller_id>', methods=['GET'])
def get_seller_info(seller_id):
    """Get seller public profile with stats and goods."""
    user = User.query.get(seller_id)
    if not user:
        return fail('卖家不存在', 404)

    # All non-deleted goods
    goods_list = Goods.query.filter(
        Goods.seller_id == seller_id,
        Goods.deleted_at.is_(None)
    ).order_by(Goods.created_at.desc()).all()

    # Sold orders count (all orders for this seller's goods, including returned)
    from models.order import Order
    sold_count = db.session.query(func.count(Order.id)).filter(
        Order.goods_id.in_(
            db.session.query(Goods.id).filter(
                Goods.seller_id == seller_id,
                Goods.deleted_at.is_(None)
            )
        )
    ).scalar() or 0

    # Returned count
    returned_count = db.session.query(func.count(Order.id)).filter(
        Order.goods_id.in_(
            db.session.query(Goods.id).filter(
                Goods.seller_id == seller_id,
                Goods.deleted_at.is_(None)
            )
        ),
        Order.status == 'returned'
    ).scalar() or 0

    # Seller's total reviews received
    from models.review import Review
    review_count = db.session.query(func.count(Review.id)).filter(
        Review.goods_id.in_(
            db.session.query(Goods.id).filter(
                Goods.seller_id == seller_id,
                Goods.deleted_at.is_(None)
            )
        )
    ).scalar() or 0

    avg_rating = db.session.query(func.avg(Review.rating)).filter(
        Review.goods_id.in_(
            db.session.query(Goods.id).filter(
                Goods.seller_id == seller_id,
                Goods.deleted_at.is_(None)
            )
        )
    ).scalar()
    avg_rating = round(float(avg_rating), 1) if avg_rating else 0

    return success(data={
        'id': user.id,
        'username': user.username,
        'avatar': user.avatar or '/static/default.png',
        'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None,
        'sold_count': sold_count,
        'returned_count': returned_count,
        'review_count': review_count,
        'avg_rating': avg_rating,
        'goods_count': len(goods_list),
        'goods': [g.to_dict() for g in goods_list]
    })


@user_bp.route('/api/user/balance', methods=['GET'])
@login_required
def get_balance():
    """Get user balance and spending summary."""
    user = User.query.get(g.user_id)
    if not user:
        return fail('用户不存在', 404)

    # Total spent
    total_spent = db.session.query(func.sum(Order.total_amount)).filter(
        Order.buyer_id == g.user_id,
        Order.status != 'returned'
    ).scalar()
    total_spent = float(total_spent) if total_spent else 0

    # Order count
    order_count = Order.query.filter_by(buyer_id=g.user_id).count()

    return success(data={
        'balance': str(user.balance),
        'total_spent': str(round(total_spent, 2)),
        'order_count': order_count
    })


@user_bp.route('/api/user/goods', methods=['GET'])
@login_required
def my_goods():
    """Get current user's goods (including off-shelf, excluding soft-deleted)."""
    items = Goods.query.filter(
        Goods.seller_id == g.user_id,
        Goods.deleted_at.is_(None)
    ).order_by(Goods.created_at.desc()).all()

    return success(data=[item.to_dict() for item in items])


@user_bp.route('/api/user/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update user profile (avatar upload, username)."""
    user = User.query.get(g.user_id)
    if not user:
        return fail('用户不存在', 404)

    # Handle avatar upload
    avatar_file = request.files.get('avatar')
    if avatar_file and avatar_file.filename:
        url = save_upload(avatar_file, 'avatars')
        if url is None:
            return fail('头像仅支持 jpg/png/webp 格式')
        user.avatar = url

    # Handle username update
    username = request.form.get('username', '').strip()
    if username:
        if len(username) < 2 or len(username) > 50:
            return fail('用户名长度需在2-50个字符之间')
        existing = User.query.filter_by(username=username).first()
        if existing and existing.id != user.id:
            return fail('用户名已被占用')
        user.username = username

    try:
        db.session.commit()
        return success(data=user.to_dict(), msg='个人资料更新成功')
    except Exception as e:
        db.session.rollback()
        return fail(f'更新失败: {str(e)}')


@user_bp.route('/api/user/password', methods=['PUT'])
@login_required
def change_password():
    """Change user password (requires old password verification)."""
    json_data = request.get_json(silent=True)
    if not json_data:
        return fail('请提供JSON数据')

    try:
        data = ChangePasswordSchema().load(json_data)
    except ValidationError as e:
        return fail(str(e.messages))

    user = User.query.get(g.user_id)
    if not user:
        return fail('用户不存在', 404)

    # Verify old password
    if not bcrypt.checkpw(data['old_password'].encode('utf-8'), user.password_hash.encode('utf-8')):
        return fail('原密码错误')

    # Update password
    try:
        user.password_hash = bcrypt.hashpw(
            data['new_password'].encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        db.session.commit()
        return success(msg='密码修改成功，请重新登录')
    except Exception as e:
        db.session.rollback()
        return fail(f'密码修改失败: {str(e)}')


@user_bp.route('/api/user/earn-points', methods=['POST'])
@login_required
def earn_points():
    """Convert game points to account balance."""
    json_data = request.get_json(silent=True)
    if not json_data:
        return fail('请提供JSON数据')

    points = json_data.get('points', 0)
    game_name = json_data.get('game', '')

    if not isinstance(points, (int, float)) or points <= 0:
        return fail('点数必须大于0')

    # Conversion rate: 1 point = 0.01 balance (100 points = 1 yuan)
    amount = round(points * 0.01, 2)

    user = User.query.get(g.user_id)
    if not user:
        return fail('用户不存在', 404)

    try:
        user.balance = float(user.balance) + amount
        db.session.commit()
        return success(data={
            'points': points,
            'amount': amount,
            'balance': str(user.balance),
            'game': game_name
        }, msg=f'成功将 {points} 点数兑换为 ¥{amount} 余额')
    except Exception as e:
        db.session.rollback()
        return fail(f'兑换失败: {str(e)}')
