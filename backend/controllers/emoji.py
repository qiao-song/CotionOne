from flask import Blueprint, request, g
from marshmallow import ValidationError

from models import db
from models.emoji import Emoji
from schemas.emoji import EmojiCreateSchema
from utils.response import success, fail
from utils.auth import login_required
from services.emoji_upload import save_emoji

emoji_bp = Blueprint('emoji', __name__)


@emoji_bp.route('/api/emojis', methods=['GET'])
def list_emojis():
    """List all emoji packs, sorted by download count descending."""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 50, type=int)
    page_size = min(page_size, 100)
    search = request.args.get('search', '').strip()

    query = Emoji.query
    if search:
        query = query.filter(Emoji.name.contains(search))

    query = query.order_by(Emoji.download_count.desc(), Emoji.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return success(data={
        'items': [e.to_dict() for e in items],
        'total': total,
        'page': page,
        'page_size': page_size
    })


@emoji_bp.route('/api/emojis', methods=['POST'])
@login_required
def upload_emoji():
    """Upload a new emoji pack (multipart: name + image)."""
    name = request.form.get('name', '').strip()

    try:
        data = EmojiCreateSchema().load({'name': name})
    except ValidationError as e:
        return fail(str(e.messages))

    image_file = request.files.get('image')
    if not image_file or not image_file.filename:
        return fail('请选择表情图片')

    image_url = save_emoji(image_file, image_file.filename)
    if not image_url:
        return fail('表情图片仅支持 jpg/png/webp 格式')

    try:
        emoji = Emoji(
            name=data['name'],
            image_url=image_url,
            uploader_id=g.user_id
        )
        db.session.add(emoji)
        db.session.commit()
        return success(data=emoji.to_dict(), msg='表情上传成功')
    except Exception as e:
        db.session.rollback()
        return fail(f'上传失败: {str(e)}')


@emoji_bp.route('/api/emojis/<int:emoji_id>/download', methods=['POST'])
def download_emoji(emoji_id):
    """Increment download count for an emoji."""
    emoji = Emoji.query.get(emoji_id)
    if not emoji:
        return fail('表情不存在', 404)

    try:
        emoji.download_count = (emoji.download_count or 0) + 1
        db.session.commit()
        return success(data=emoji.to_dict(), msg='下载成功')
    except Exception as e:
        db.session.rollback()
        return fail(f'下载失败: {str(e)}')
