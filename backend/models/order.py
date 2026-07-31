from models import db
from datetime import datetime


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    buyer_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, comment='买家ID')
    goods_id = db.Column(db.BigInteger, db.ForeignKey('goods.id'), nullable=False, comment='商品ID')
    goods_title = db.Column(db.String(200), nullable=False, comment='商品标题快照')
    goods_price = db.Column(db.Numeric(10, 2), nullable=False, comment='成交价快照')
    goods_image = db.Column(db.String(500), nullable=True, comment='商品图片快照')
    quantity = db.Column(db.Integer, default=1, comment='数量')
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, comment='总金额')
    status = db.Column(db.String(20), default='pending', comment='pending=未发货, shipped=运输中, received=已签收, returned=已退货')
    logistics = db.Column(db.JSON, nullable=True, comment='物流记录')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    buyer = db.relationship('User', backref='orders')
    goods = db.relationship('Goods', backref='orders')

    def to_dict(self):
        return {
            'id': self.id,
            'buyer_id': self.buyer_id,
            'buyer_name': self.buyer.username if self.buyer else None,
            'goods_id': self.goods_id,
            'goods_title': self.goods_title,
            'goods_price': str(self.goods_price),
            'goods_image': self.goods_image,
            'quantity': self.quantity,
            'total_amount': str(self.total_amount),
            'status': self.status,
            'logistics': self.logistics or [],
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
        }
