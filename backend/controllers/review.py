from flask import Blueprint, request, g
from marshmallow import ValidationError

from models import db
from models.review import Review
from models.order import Order
from schemas.review import ReviewCreateSchema
from utils.response import success, fail
from utils.auth import login_required

review_bp = Blueprint('review', __name__)


@review_bp.route('/api/reviews', methods=['POST'])
@login_required
def create_review():
    """Create a review for a product. Anyone logged in can review.
    If order_id is provided, validate purchase; buyer reviews show purchase info."""
    json_data = request.get_json(silent=True)
    if not json_data:
        return fail('请提供JSON数据')

    try:
        data = ReviewCreateSchema().load(json_data)
    except ValidationError as e:
        return fail(str(e.messages))

    # If order_id provided, validate ownership and status
    if data.get('order_id'):
        order = Order.query.filter_by(id=data['order_id'], buyer_id=g.user_id).first()
        if not order:
            return fail('订单不存在', 404)
        if order.status != 'received':
            return fail('只能评价已签收的订单')
        if order.goods_id != data['goods_id']:
            return fail('商品与订单不匹配')

        # Check if already reviewed
        existing = Review.query.filter_by(order_id=data['order_id']).first()
        if existing:
            return fail('该订单已评价过')

    try:
        review = Review(
            user_id=g.user_id,
            goods_id=data['goods_id'],
            order_id=data.get('order_id'),
            rating=data['rating'],
            content=data.get('content', '')
        )
        db.session.add(review)
        db.session.commit()
        return success(data=review.to_dict(), msg='评价成功')
    except Exception as e:
        db.session.rollback()
        return fail(f'评价失败: {str(e)}')


@review_bp.route('/api/reviews/goods/<int:goods_id>', methods=['GET'])
def list_goods_reviews(goods_id):
    """List reviews for a product (public), paginated."""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    page_size = min(page_size, 50)

    query = Review.query.filter_by(goods_id=goods_id).order_by(Review.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    # Calculate average rating
    from sqlalchemy import func
    avg_result = db.session.query(func.avg(Review.rating)).filter(
        Review.goods_id == goods_id
    ).scalar()
    avg_rating = round(float(avg_result), 1) if avg_result else 0

    return success(data={
        'items': [item.to_dict() for item in items],
        'total': total,
        'avg_rating': avg_rating,
        'page': page,
        'page_size': page_size
    })
