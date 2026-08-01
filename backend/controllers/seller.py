from datetime import datetime
from flask import Blueprint
from sqlalchemy import func

from models import db
from models.user import User
from models.goods import Goods
from models.order import Order
from models.review import Review

seller_bp = Blueprint('seller', __name__)


@seller_bp.route('/api/seller/<int:user_id>', methods=['GET'])
def get_seller(user_id):
    """Get public seller profile with stats and goods list."""
    user = User.query.get(user_id)
    if not user:
        return fail('卖家不存在', 404)

    # Active goods count and list
    goods_query = Goods.query.filter(
        Goods.seller_id == user_id,
        Goods.status == 1,
        Goods.deleted_at.is_(None)
    )
    goods_list = goods_query.order_by(Goods.created_at.desc()).all()
    goods_count = len(goods_list)

    # Order stats for this seller's goods
    goods_ids = [g.id for g in goods_list]
    sold_count = Order.query.filter(Order.goods_id.in_(goods_ids)).count() if goods_ids else 0
    returned_count = Order.query.filter(
        Order.goods_id.in_(goods_ids),
        Order.status == 'returned'
    ).count() if goods_ids else 0

    # Average rating across all seller's goods
    avg_rating = 0.0
    review_count = 0
    if goods_ids:
        review_count = Review.query.filter(Review.goods_id.in_(goods_ids)).count()
        if review_count > 0:
            avg = db.session.query(func.avg(Review.rating)).filter(
                Review.goods_id.in_(goods_ids)
            ).scalar()
            avg_rating = round(float(avg), 1) if avg else 0.0

    # Buyer-side stats: cumulative spending, cumulative orders
    buyer_orders = Order.query.filter_by(buyer_id=user_id).all()
    total_spent = sum(float(o.total_amount) for o in buyer_orders) if buyer_orders else 0.0
    total_orders = len(buyer_orders)

    return success(data={
        'id': user.id,
        'username': user.username,
        'avatar': user.avatar or '/static/default.png',
        'created_at': user.created_at.strftime('%Y-%m-%d') if user.created_at else None,
        'sold_count': sold_count,
        'returned_count': returned_count,
        'goods_count': goods_count,
        'avg_rating': avg_rating,
        'review_count': review_count,
        'total_spent': round(total_spent, 2),
        'total_orders': total_orders,
        'goods': [g.to_dict() for g in goods_list]
    })
