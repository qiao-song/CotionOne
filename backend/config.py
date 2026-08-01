import os

DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '123456')
DB_NAME = os.environ.get('DB_NAME', 'tbao')

SQLALCHEMY_DATABASE_URI = (
    f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    '?charset=utf8mb4'
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

SECRET_KEY = os.environ.get('SECRET_KEY', 'tbao-dev-secret-key-2024')
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
JWT_EXPIRY_DAYS = 7
JWT_COOKIE_NAME = 'tbao_token'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
AVATAR_FOLDER = os.path.join(UPLOAD_FOLDER, 'avatars')
GOODS_FOLDER = os.path.join(UPLOAD_FOLDER, 'goods')
MAX_CONTENT_LENGTH = 60 * 1024 * 1024  # 60MB (for videos)
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'mov', 'avi'}
MAX_IMAGE_COUNT = 9
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB
MAX_VIDEO_DURATION = 15  # seconds (enforced client-side)
VIDEOS_FOLDER = os.path.join(UPLOAD_FOLDER, 'videos')
EMOJI_FOLDER = os.path.join(UPLOAD_FOLDER, 'emojis')
POSTS_FOLDER = os.path.join(UPLOAD_FOLDER, 'posts')
