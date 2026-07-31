import json
import random
from datetime import datetime
from flask import Blueprint, request, g
from marshmallow import ValidationError
from sqlalchemy import func

from models import db
from models.goods import Goods
from models.order import Order
from models.review import Review
from schemas.goods import GoodsCreateSchema, GoodsUpdateSchema
from utils.response import success, fail
from utils.auth import login_required
from utils.upload import save_upload, save_video
from config import MAX_IMAGE_COUNT

goods_bp = Blueprint('goods', __name__)


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
    """Public goods gallery: status=1, not deleted, newest first."""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    page_size = min(page_size, 100)

    query = Goods.query.filter(
        Goods.status == 1,
        Goods.deleted_at.is_(None)
    ).order_by(Goods.created_at.desc())

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

    # Validate form fields
    try:
        data = GoodsCreateSchema().load({
            'title': title,
            'price': price,
            'description': description or None
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

    update_data = {}
    if title:
        update_data['title'] = title
    if price:
        update_data['price'] = price
    if description:
        update_data['description'] = description

    if update_data:
        try:
            GoodsUpdateSchema().load(update_data)
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
    """List goods with videos for the Discover feed (public, paginated)."""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    page_size = min(page_size, 30)

    query = Goods.query.filter(
        Goods.status == 1,
        Goods.deleted_at.is_(None),
        Goods.video.isnot(None),
        Goods.video != ''
    ).order_by(Goods.created_at.desc())

    total = query.count()
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
