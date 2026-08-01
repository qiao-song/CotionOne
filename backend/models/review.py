from models import db
from datetime import datetime


class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, comment='评论者ID')
    goods_id = db.Column(db.BigInteger, db.ForeignKey('goods.id'), nullable=False, comment='商品ID')
    order_id = db.Column(db.BigInteger, db.ForeignKey('orders.id'), nullable=True, unique=True, comment='订单ID（一个订单只能评论一次，非购买评论为空）')
    rating = db.Column(db.SmallInteger, default=5, comment='评分 1-5')
    content = db.Column(db.Text, nullable=True, comment='评论内容')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='reviews')
    goods = db.relationship('Goods', backref='reviews')
    order = db.relationship('Order', backref='review', uselist=False)

    def to_dict(self):
        result = {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'user_avatar': self.user.avatar if self.user else None,
            'goods_id': self.goods_id,
            'order_id': self.order_id,
            'rating': self.rating,
            'content': self.content or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }
        # Add purchase info if this review is from a verified order
        if self.order:
            result['purchase'] = {
                'goods_title': self.order.goods_title,
                'goods_price': str(self.order.goods_price),
                'quantity': self.order.quantity,
            }
        return result
