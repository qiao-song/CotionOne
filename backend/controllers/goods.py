import json
import random
from datetime import datetime
from flask import Blueprint, request, g
from marshmallow import ValidationError
from sqlalchemy import func, or_

from models import db
from models.goods import Goods
from models.user import User
from models.order import Order
from models.review import Review
from schemas.goods import GoodsCreateSchema, GoodsUpdateSchema
from utils.response import success, fail
from utils.auth import login_required
from utils.upload import save_upload, save_video
from config import MAX_IMAGE_COUNT

goods_bp = Blueprint('goods', __name__)

# Predefined tag options
PREDEFINED_TAGS = ['数码', '家电', '文创', '工具', '文具']


@goods_bp.route('/api/goods/tags', methods=['GET'])
def list_tags():
    """List all available tags (predefined + popular from goods)."""
    # Get all unique tags from existing goods
    all_goods = Goods.query.filter(
        Goods.status == 1,
        Goods.deleted_at.is_(None)
    ).all()
    used_tags = set()
    for g in all_goods:
        if g.tags:
            for t in g.tags:
                used_tags.add(t)
    # Merge predefined + used
    all_tags = list(dict.fromkeys(PREDEFINED_TAGS + sorted(used_tags)))
    return success(data=all_tags)


@goods_bp.route('/api/goods/<int:goods_id>', methods=['GET'])
def get_goods_detail(goods_id):
    """Get single product detail with stats."""
    goods = Goods.query.filter_by(id=goods_id, deleted_at=None).first()
    if not goods:
        return fail('商品不存在', 404)

    # Sales count
    sales_count = Order.query.filter_by(goods_id=goods_id).count()

    # Review stats
    review_count = Review.query.filter_by(goods_id=goods_id).count()
    avg_rating = db.session.query(func.avg(Review.rating)).filter(
        Review.goods_id == goods_id
    ).scalar()
    avg_rating = round(float(avg_rating), 1) if avg_rating else 0

    # Price history (simulated 6-month data)
    current_price = float(goods.price)
    now = datetime.utcnow()
    price_history = []
    for i in range(5, -1, -1):
        month_date = datetime(now.year, now.month, 1) if i == 0 else datetime(
            now.year if now.month > i else now.year - 1,
            (now.month - i) % 12 or 12, 1
        )
        if i == 0:
            p = current_price
        else:
            variation = random.uniform(-0.15, 0.15) * current_price
            p = round(current_price + variation, 2)
        price_history.append({
            'date': month_date.strftime('%Y-%m'),
            'price': p
        })

    data = goods.to_dict()
    data['sales_count'] = sales_count
    data['review_count'] = review_count
    data['avg_rating'] = avg_rating
    data['price_history'] = price_history

    return success(data=data)


@goods_bp.route('/api/goods', methods=['GET'])
def list_goods():
    """Public goods gallery with search, filters, and random sort."""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    page_size = min(page_size, 100)

    keyword = request.args.get('keyword', '').strip()
    tag = request.args.get('tag', '').strip()
    seller_name = request.args.get('seller_name', '').strip()
    price_min = request.args.get('price_min', type=float)
    price_max = request.args.get('price_max', type=float)
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    sort = request.args.get('sort', 'newest').strip()  # newest, random, price_asc, price_desc
    exclude_ids = request.args.get('exclude_ids', '').strip()

    # Base query
    query = Goods.query.filter(
        Goods.status == 1,
        Goods.deleted_at.is_(None)
    )

    # Keyword search (title + description)
    if keyword:
        query = query.filter(or_(
            Goods.title.contains(keyword),
            Goods.description.contains(keyword)
        ))

    # Tag filter
    if tag:
        # JSON_CONTAINS equivalent: filter goods where tags JSON array contains the tag
        query = query.filter(
            db.func.json_contains(Goods.tags, json.dumps(tag))
        )

    # Seller name search
    if seller_name:
        query = query.join(User, Goods.seller_id == User.id).filter(
            User.username.contains(seller_name)
        )

    # Price range
    if price_min is not None:
        query = query.filter(Goods.price >= price_min)
    if price_max is not None:
        query = query.filter(Goods.price <= price_max)

    # Date range
    if date_from:
        try:
            dt_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Goods.created_at >= dt_from)
        except ValueError:
            pass
    if date_to:
        try:
            dt_to = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(Goods.created_at <= dt_to)
        except ValueError:
            pass

    # Exclude previously seen IDs (for random sort dedup)
    if exclude_ids:
        try:
            excl = [int(x) for x in exclude_ids.split(',') if x.strip()]
            if excl:
                query = query.filter(~Goods.id.in_(excl))
        except ValueError:
            pass

    # Sorting
    if sort == 'random':
        query = query.order_by(func.rand())
    elif sort == 'price_asc':
        query = query.order_by(Goods.price.asc(), Goods.created_at.desc())
    elif sort == 'price_desc':
        query = query.order_by(Goods.price.desc(), Goods.created_at.desc())
    else:  # newest
        query = query.order_by(Goods.created_at.desc())

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return success(data={
        'items': [item.to_dict() for item in items],
        'total': total,
        'page': page,
        'page_size': page_size
    })


@goods_bp.route('/api/goods', methods=['POST'])
@login_required
def create_goods():
    """Create a new product with multipart form data."""
    title = request.form.get('title', '').strip()
    price = request.form.get('price', '').strip()
    description = request.form.get('description', '').strip()
    tags_str = request.form.get('tags', '').strip()

    # Parse tags from JSON string or comma-separated
    tags = []
    if tags_str:
        try:
            tags = json.loads(tags_str)
        except (json.JSONDecodeError, TypeError):
            tags = [t.strip() for t in tags_str.split(',') if t.strip()]
        # Limit to 10 tags, each max 20 chars
        tags = tags[:10]
        tags = [t[:20] for t in tags]

    # Validate form fields
    try:
        data = GoodsCreateSchema().load({
            'title': title,
            'price': price,
            'description': description or None,
            'tags': tags
        })
    except ValidationError as e:
        return fail(str(e.messages))

    # Handle image uploads
    images = request.files.getlist('images')
    if len(images) > MAX_IMAGE_COUNT:
        return fail(f'最多上传{MAX_IMAGE_COUNT}张图片')

    image_urls = []
    for img in images:
        url = save_upload(img, 'goods')
        if url:
            image_urls.append(url)

    # Handle video upload
    video_file = request.files.get('video')
    video_url = None
    if video_file and video_file.filename:
        video_url = save_video(video_file)

    try:
        goods = Goods(
            title=data['title'],
            price=data['price'],
            description=data.get('description', ''),
            images=image_urls,
            video=video_url,
            tags=data.get('tags', []),
            status=1,
            seller_id=g.user_id
        )
        db.session.add(goods)
        db.session.commit()
        return success(data=goods.to_dict(), msg='商品发布成功')
    except Exception as e:
        db.session.rollback()
        return fail(f'发布失败: {str(e)}')


@goods_bp.route('/api/goods/<int:goods_id>', methods=['PUT'])
@login_required
def update_goods(goods_id):
    """Update a product (seller only)."""
    goods = Goods.query.filter_by(id=goods_id, deleted_at=None).first()
    if not goods:
        return fail('商品不存在', 404)
    if goods.seller_id != g.user_id:
        return fail('无权操作此商品', 403)

    title = request.form.get('title', '').strip()
    price = request.form.get('price', '').strip()
    description = request.form.get('description', '').strip()
    tags_str = request.form.get('tags', '').strip()

    update_data = {}
    if title:
        update_data['title'] = title
    if price:
        update_data['price'] = price
    if description:
        update_data['description'] = description

    # Parse tags if provided
    if tags_str:
        try:
            tags = json.loads(tags_str)
        except (json.JSONDecodeError, TypeError):
            tags = [t.strip() for t in tags_str.split(',') if t.strip()]
        tags = tags[:10]
        update_data['tags'] = [t[:20] for t in tags]

    if update_data:
        try:
            # Validate with schema (skip tags for partial validation)
            validation_data = {k: v for k, v in update_data.items() if k != 'tags'}
            if validation_data:
                GoodsUpdateSchema().load(validation_data)
        except ValidationError as e:
            return fail(str(e.messages))

    # Handle images
    keep_images = request.form.get('keep_images', '')
    if keep_images:
        try:
            keep_list = json.loads(keep_images)
        except json.JSONDecodeError:
            keep_list = []
    else:
        keep_list = goods.images or []

    new_images = request.files.getlist('images')
    for img in new_images:
        if len(keep_list) >= MAX_IMAGE_COUNT:
            break
        url = save_upload(img, 'goods')
        if url:
            keep_list.append(url)

    try:
        for key, value in update_data.items():
            setattr(goods, key, value)
        goods.images = keep_list
        goods.updated_at = datetime.utcnow()

        # Handle video
        video_file = request.files.get('video')
        if video_file and video_file.filename:
            video_url = save_video(video_file)
            if video_url:
                goods.video = video_url
        # Check if user wants to remove video
        if request.form.get('remove_video') == '1':
            goods.video = None

        db.session.commit()
        return success(data=goods.to_dict(), msg='商品更新成功')
    except Exception as e:
        db.session.rollback()
        return fail(f'更新失败: {str(e)}')


@goods_bp.route('/api/goods/<int:goods_id>', methods=['DELETE'])
@login_required
def delete_goods(goods_id):
    """Soft delete a product (seller only)."""
    goods = Goods.query.filter_by(id=goods_id, deleted_at=None).first()
    if not goods:
        return fail('商品不存在', 404)
    if goods.seller_id != g.user_id:
        return fail('无权操作此商品', 403)

    try:
        goods.deleted_at = datetime.utcnow()
        db.session.commit()
        return success(msg='商品已删除')
    except Exception as e:
        db.session.rollback()
        return fail(f'删除失败: {str(e)}')


@goods_bp.route('/api/goods/<int:goods_id>/status', methods=['PUT'])
@login_required
def toggle_status(goods_id):
    """Toggle product status (seller only)."""
    goods = Goods.query.filter_by(id=goods_id, deleted_at=None).first()
    if not goods:
        return fail('商品不存在', 404)
    if goods.seller_id != g.user_id:
        return fail('无权操作此商品', 403)

    try:
        goods.status = 0 if goods.status == 1 else 1
        db.session.commit()
        status_text = '上架' if goods.status == 1 else '下架'
        return success(data=goods.to_dict(), msg=f'商品已{status_text}')
    except Exception as e:
        db.session.rollback()
        return fail(f'操作失败: {str(e)}')


@goods_bp.route('/api/discover', methods=['GET'])
def discover_feed():
    """List goods with videos for the Discover feed (public, random order with dedup)."""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    page_size = min(page_size, 30)
    exclude_ids = request.args.get('exclude_ids', '').strip()
    sort = request.args.get('sort', 'random').strip()

    query = Goods.query.filter(
        Goods.status == 1,
        Goods.deleted_at.is_(None),
        Goods.video.isnot(None),
        Goods.video != ''
    )

    # Exclude already-seen videos
    if exclude_ids:
        try:
            excl = [int(x) for x in exclude_ids.split(',') if x.strip()]
            if excl:
                query = query.filter(~Goods.id.in_(excl))
        except ValueError:
            pass

    total = query.count()

    # If all videos have been seen, reset — cycle through all videos
    if total == 0 and exclude_ids:
        query = Goods.query.filter(
            Goods.status == 1,
            Goods.deleted_at.is_(None),
            Goods.video.isnot(None),
            Goods.video != ''
        )
        total = query.count()

    # Sort: random or newest
    if sort == 'random':
        query = query.order_by(func.rand())
    else:
        query = query.order_by(Goods.created_at.desc())

    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return success(data={
        'items': [item.to_dict() for item in items],
        'total': total,
        'page': page,
        'page_size': page_size
    })


@goods_bp.route('/api/goods/<int:goods_id>/like', methods=['POST'])
def like_video(goods_id):
    """Increment video like count."""
    goods = Goods.query.filter_by(id=goods_id, deleted_at=None).first()
    if not goods:
        return fail('商品不存在', 404)

    try:
        goods.video_likes = (goods.video_likes or 0) + 1
        db.session.commit()
        return success(data={'likes': goods.video_likes}, msg='点赞成功')
    except Exception as e:
        db.session.rollback()
        return fail(f'点赞失败: {str(e)}')


@goods_bp.route('/api/goods/<int:goods_id>/share', methods=['POST'])
def share_video(goods_id):
    """Increment video share count."""
    goods = Goods.query.filter_by(id=goods_id, deleted_at=None).first()
    if not goods:
        return fail('商品不存在', 404)

    share_link = f'/goods/{goods_id}'

    try:
        goods.video_shares = (goods.video_shares or 0) + 1
        db.session.commit()
        return success(data={'shares': goods.video_shares, 'link': share_link}, msg='分享成功')
    except Exception as e:
        db.session.rollback()
        return fail(f'分享失败: {str(e)}')
