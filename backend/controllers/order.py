import random
from datetime import datetime, timedelta
from flask import Blueprint, request, g
from marshmallow import ValidationError
from sqlalchemy import func

from models import db
from models.user import User
from models.goods import Goods
from models.order import Order
from schemas.order import CheckoutSchema, OrderStatusSchema
from utils.response import success, fail
from utils.auth import login_required

order_bp = Blueprint('order', __name__)

# Chinese cities for simulated logistics
LOGISTICS_CITIES = [
    ('深圳转运中心', '广东省深圳市'),
    ('广州转运中心', '广东省广州市'),
    ('武汉转运中心', '湖北省武汉市'),
    ('上海转运中心', '上海市'),
    ('北京转运中心', '北京市'),
    ('杭州转运中心', '浙江省杭州市'),
    ('成都转运中心', '四川省成都市'),
]


def _generate_logistics(created_at):
    """Generate simulated logistics entries for a new order."""
    now = created_at or datetime.utcnow()
    cities = random.sample(LOGISTICS_CITIES, min(3, len(LOGISTICS_CITIES)))
    entries = [
        {
            'time': (now + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
            'status': '已揽收',
            'location': cities[0][0],
            'desc': f'包裹已在{cities[0][1]}揽收'
        },
        {
            'time': (now + timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S'),
            'status': '运输中',
            'location': cities[1][0],
            'desc': f'包裹已到达{cities[1][1]}'
        },
        {
            'time': (now + timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S'),
            'status': '派送中',
            'location': cities[2][0] if len(cities) > 2 else cities[1][0],
            'desc': '快递员正在派送中，请保持电话畅通'
        },
    ]
    return entries


@order_bp.route('/api/orders', methods=['POST'])
@login_required
def create_order():
    """Create orders from cart items. Deduct buyer balance, credit seller."""
    json_data = request.get_json(silent=True)
    if not json_data:
        return fail('请提供JSON数据')

    try:
        data = CheckoutSchema().load(json_data)
    except ValidationError as e:
        return fail(str(e.messages))

    buyer = User.query.get(g.user_id)
    if not buyer:
        return fail('用户不存在', 404)

    # Validate all items and calculate total
    total = 0
    order_items = []
    for item in data['items']:
        goods = Goods.query.filter_by(id=item['goods_id'], deleted_at=None, status=1).first()
        if not goods:
            return fail(f'商品 #{item["goods_id"]} 不存在或已下架')
        if goods.seller_id == g.user_id:
            return fail('不能购买自己的商品')

        qty = item['quantity']
        item_total = float(goods.price) * qty
        total += item_total
        order_items.append({
            'goods': goods,
            'quantity': qty,
            'item_total': item_total
        })

    # Check balance
    if float(buyer.balance) < total:
        return fail(f'余额不足，需要 ¥{total:.2f}，当前余额 ¥{float(buyer.balance):.2f}')

    # Create orders in transaction
    created_orders = []
    try:
        now = datetime.utcnow()
        for oi in order_items:
            goods = oi['goods']
            item_total = oi['item_total']

            # Deduct buyer balance
            buyer.balance = float(buyer.balance) - item_total

            # Credit seller balance
            seller = User.query.get(goods.seller_id)
            if seller:
                seller.balance = float(seller.balance) + item_total

            # Create order
            order = Order(
                buyer_id=g.user_id,
                goods_id=goods.id,
                goods_title=goods.title,
                goods_price=goods.price,
                goods_image=goods.images[0] if goods.images else None,
                quantity=oi['quantity'],
                total_amount=item_total,
                status='pending',
                logistics=_generate_logistics(now),
                created_at=now
            )
            db.session.add(order)
            created_orders.append(order)

        db.session.commit()

        return success(data={
            'orders': [o.to_dict() for o in created_orders],
            'balance': str(buyer.balance)
        }, msg='下单成功')
    except Exception as e:
        db.session.rollback()
        return fail(f'下单失败: {str(e)}')


@order_bp.route('/api/orders', methods=['GET'])
@login_required
def list_orders():
    """List current user's orders, newest first."""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    page_size = min(page_size, 50)

    query = Order.query.filter_by(buyer_id=g.user_id).order_by(Order.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return success(data={
        'items': [item.to_dict() for item in items],
        'total': total,
        'page': page,
        'page_size': page_size
    })


@order_bp.route('/api/orders/<int:order_id>', methods=['GET'])
@login_required
def get_order(order_id):
    """Get single order detail."""
    order = Order.query.filter_by(id=order_id, buyer_id=g.user_id).first()
    if not order:
        return fail('订单不存在', 404)

    data = order.to_dict()
    # Check if review exists
    from models.review import Review
    review = Review.query.filter_by(order_id=order_id).first()
    data['has_review'] = review is not None
    if review:
        data['review'] = review.to_dict()

    return success(data=data)


@order_bp.route('/api/orders/<int:order_id>/status', methods=['PUT'])
@login_required
def update_order_status(order_id):
    """Update order status (receive or return)."""
    order = Order.query.filter_by(id=order_id, buyer_id=g.user_id).first()
    if not order:
        return fail('订单不存在', 404)

    json_data = request.get_json(silent=True)
    if not json_data:
        return fail('请提供JSON数据')

    try:
        data = OrderStatusSchema().load(json_data)
    except ValidationError as e:
        return fail(str(e.messages))

    new_status = data['status']

    if new_status == 'returned':
        if order.status != 'received':
            return fail('只能退回收到的商品')
        # Refund buyer, deduct seller
        buyer = User.query.get(g.user_id)
        seller = User.query.get(order.goods.seller_id) if order.goods else None
        amount = float(order.total_amount)
        try:
            buyer.balance = float(buyer.balance) + amount
            if seller:
                seller.balance = float(seller.balance) - amount
            order.status = 'returned'
            order.updated_at = datetime.utcnow()
            # Add return logistics
            logs = list(order.logistics or [])
            logs.append({
                'time': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'status': '已退货',
                'location': '退货中心',
                'desc': '买家申请退货，退款已退回'
            })
            order.logistics = logs
            db.session.commit()
            return success(data=order.to_dict(), msg='退货成功，退款已退回')
        except Exception as e:
            db.session.rollback()
            return fail(f'退货失败: {str(e)}')

    elif new_status == 'received':
        if order.status not in ('pending', 'shipped'):
            return fail('当前状态无法确认收货')
        try:
            order.status = 'received'
            order.updated_at = datetime.utcnow()
            logs = list(order.logistics or [])
            logs.append({
                'time': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'status': '已签收',
                'location': '收件地址',
                'desc': '包裹已签收'
            })
            order.logistics = logs
            db.session.commit()
            return success(data=order.to_dict(), msg='已确认收货')
        except Exception as e:
            db.session.rollback()
            return fail(f'确认收货失败: {str(e)}')

    return fail('无效的状态')
