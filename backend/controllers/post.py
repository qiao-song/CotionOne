import json
from datetime import datetime
from flask import Blueprint, request, g
from marshmallow import ValidationError

from models import db
from models.post import Post
from models.emoji import Emoji
from schemas.post import PostCreateSchema
from utils.response import success, fail
from utils.auth import login_required
from utils.upload import save_upload, save_video
from services.news_scraper import get_hot_news
from config import MAX_IMAGE_COUNT

post_bp = Blueprint('post', __name__)


@post_bp.route('/api/posts', methods=['GET'])
def list_posts():
    """Public feed with news injection every 5 posts."""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    page_size = min(page_size, 30)

    # Calculate how many posts to fetch per page
    # Every 5 posts we inject 1 news item, so we need fewer posts
    posts_to_fetch = page_size  # fetch full page_size, then inject news

    # Fetch posts from DB
    query = Post.query.order_by(Post.created_at.desc())
    total_posts = query.count()
    posts = query.offset((page - 1) * posts_to_fetch).limit(posts_to_fetch).all()

    # Build mixed feed: every 5th position gets a news card
    feed = []
    news_pool = get_hot_news()
    news_idx = 0

    for i, post in enumerate(posts):
        feed.append({'type': 'post', **post.to_dict()})
        # Inject news every 5th position (1-indexed)
        position = (page - 1) * posts_to_fetch + i + 1
        if position % 5 == 0 and news_pool:
            news_item = news_pool[news_idx % len(news_pool)]
            news_idx += 1
            feed.append({
                'type': 'news',
                'id': f'news-{position}',
                'title': news_item.get('title', ''),
                'content': news_item.get('summary', ''),
                'source': news_item.get('source', '网络'),
                'url': news_item.get('url', '#'),
                'image': news_item.get('image', ''),
                'created_at': news_item.get('time', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
            })

    # If no posts at all, still return news on first page
    if page == 1 and len(posts) == 0:
        for i, news_item in enumerate(news_pool[:3]):
            feed.append({
                'type': 'news',
                'id': f'news-init-{i}',
                'title': news_item.get('title', ''),
                'content': news_item.get('summary', ''),
                'source': news_item.get('source', '网络'),
                'url': news_item.get('url', '#'),
                'image': news_item.get('image', ''),
                'created_at': news_item.get('time', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
            })

    return success(data={
        'items': feed,
        'total': total_posts,
        'page': page,
        'page_size': page_size
    })


@post_bp.route('/api/posts', methods=['POST'])
@login_required
def create_post():
    """Create a new post with multipart form data."""
    content = request.form.get('content', '').strip()

    # Validate content
    try:
        data = PostCreateSchema().load({'content': content})
    except ValidationError as e:
        return fail(str(e.messages))

    # Handle image uploads
    images = request.files.getlist('images')
    if len(images) > MAX_IMAGE_COUNT:
        return fail(f'最多上传{MAX_IMAGE_COUNT}张图片')

    image_urls = []
    for img in images:
        url = save_upload(img, 'goods')  # reuse goods folder for post images
        if url:
            image_urls.append(url)

    # Handle video upload
    video_file = request.files.get('video')
    video_url = None
    if video_file and video_file.filename:
        video_url = save_video(video_file)

    # Handle emoji uploads within the post (optional: dedicated post emoji images)
    # Emoji references in content are stored as [emoji:id] tags

    try:
        post = Post(
            user_id=g.user_id,
            content=data['content'],
            images=image_urls,
            video=video_url
        )
        db.session.add(post)
        db.session.commit()
        return success(data=post.to_dict(), msg='发布成功')
    except Exception as e:
        db.session.rollback()
        return fail(f'发布失败: {str(e)}')


@post_bp.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post_detail(post_id):
    """Get a single post detail."""
    post = Post.query.get(post_id)
    if not post:
        return fail('日志不存在', 404)
    return success(data=post.to_dict())
