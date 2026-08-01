from datetime import datetime
from models import db


class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    images = db.Column(db.JSON, nullable=True, default=list)
    video = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='posts')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else '未知',
            'user_avatar': self.user.avatar if self.user else '/static/default.png',
            'content': self.content,
            'images': self.images or [],
            'video': self.video,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
