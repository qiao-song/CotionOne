from flask import Blueprint, request, g
from marshmallow import ValidationError

from models import db
from models.video_comment import VideoComment
from schemas.video_comment import VideoCommentCreateSchema
from utils.response import success, fail
from utils.auth import login_required

video_comment_bp = Blueprint('video_comment', __name__)


@video_comment_bp.route('/api/video-comments/<int:goods_id>', methods=['GET'])
def list_comments(goods_id):
    """List comments for a video/goods (public), paginated."""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    page_size = min(page_size, 50)

    query = VideoComment.query.filter_by(goods_id=goods_id)\
        .order_by(VideoComment.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return success(data={
        'items': [item.to_dict() for item in items],
        'total': total,
        'page': page,
        'page_size': page_size
    })


@video_comment_bp.route('/api/video-comments', methods=['POST'])
@login_required
def create_comment():
    """Create a comment on a video/goods. Anyone logged in can comment."""
    json_data = request.get_json(silent=True)
    if not json_data:
        return fail('请提供JSON数据')

    try:
        data = VideoCommentCreateSchema().load(json_data)
    except ValidationError as e:
        return fail(str(e.messages))

    try:
        comment = VideoComment(
            user_id=g.user_id,
            goods_id=data['goods_id'],
            content=data['content']
        )
        db.session.add(comment)
        db.session.commit()
        return success(data=comment.to_dict(), msg='评论成功')
    except Exception as e:
        db.session.rollback()
        return fail(f'评论失败: {str(e)}')
