from models import db
from datetime import datetime


class VideoComment(db.Model):
    __tablename__ = 'video_comments'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, comment='评论者ID')
    goods_id = db.Column(db.BigInteger, db.ForeignKey('goods.id'), nullable=False, comment='视频商品ID')
    content = db.Column(db.Text, nullable=False, comment='评论内容')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='video_comments')
    goods = db.relationship('Goods', backref='video_comments')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else '未知',
            'user_avatar': self.user.avatar if self.user else '/static/default.png',
            'goods_id': self.goods_id,
            'content': self.content,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
        }
