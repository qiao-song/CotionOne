from datetime import datetime
from models import db


class Emoji(db.Model):
    __tablename__ = 'emojis'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)
    uploader_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False)
    download_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    uploader = db.relationship('User', backref='emojis')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'image_url': self.image_url,
            'uploader_id': self.uploader_id,
            'uploader_name': self.uploader.username if self.uploader else '未知',
            'download_count': self.download_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
