from models import db
from datetime import datetime


class Goods(db.Model):
    __tablename__ = 'goods'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text, nullable=True)
    images = db.Column(db.JSON, nullable=True, default=list)
    status = db.Column(db.SmallInteger, default=1)
    video = db.Column(db.String(500), nullable=True)
    video_likes = db.Column(db.Integer, default=0)
    video_shares = db.Column(db.Integer, default=0)
    seller_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'price': str(self.price),
            'description': self.description or '',
            'images': self.images or [],
            'status': self.status,
            'video': self.video or '',
            'video_likes': self.video_likes or 0,
            'video_shares': self.video_shares or 0,
            'seller_id': self.seller_id,
            'seller_name': self.seller.username if self.seller else None,
            'seller_avatar': self.seller.avatar if self.seller else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
        }
