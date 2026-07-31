import os
import pymysql
from flask import Flask, send_from_directory
from flask_cors import CORS

from config import (
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME,
    SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS,
    SECRET_KEY, JWT_SECRET_KEY, JWT_EXPIRY_DAYS, JWT_COOKIE_NAME,
    UPLOAD_FOLDER, AVATAR_FOLDER, GOODS_FOLDER, VIDEOS_FOLDER, MAX_CONTENT_LENGTH
)
from models import db, migrate


def create_app():
    app = Flask(__name__)

    # Database config
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS

    # Security config
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
    app.config['JWT_EXPIRY_DAYS'] = JWT_EXPIRY_DAYS
    app.config['JWT_COOKIE_NAME'] = JWT_COOKIE_NAME

    # Upload config
    app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # CORS
    CORS(app, supports_credentials=True)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from controllers.auth import auth_bp
    from controllers.goods import goods_bp
    from controllers.user import user_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(goods_bp)
    app.register_blueprint(user_bp)
    # Lazy-register new blueprints (import after db is ready)
    try:
        from controllers.order import order_bp
        from controllers.review import review_bp
        app.register_blueprint(order_bp)
        app.register_blueprint(review_bp)
    except ImportError:
        pass

    # Serve uploads
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(UPLOAD_FOLDER, filename)

    # Serve default static files
    @app.route('/static/<path:filename>')
    def static_file(filename):
        return send_from_directory(os.path.join(os.path.dirname(__file__), 'static'), filename)

    # Health check
    @app.route('/api/health')
    def health():
        return {'code': 0, 'msg': 'ok'}

    # Create tables and upload dirs
    with app.app_context():
        _ensure_database()
        db.create_all()
        _ensure_directories()

    return app


def _ensure_database():
    """Create database if it doesn't exist (for local dev without Docker init.sql)."""
    try:
        conn = pymysql.connect(
            host=DB_HOST, port=int(DB_PORT),
            user=DB_USER, password=DB_PASSWORD,
            charset='utf8mb4'
        )
        with conn.cursor() as cursor:
            cursor.execute("SHOW DATABASES LIKE %s", (DB_NAME,))
            if cursor.fetchone():
                # Database entry exists, verify it's usable
                try:
                    conn.select_db(DB_NAME)
                except Exception:
                    # Corrupted — drop and recreate
                    print(f"[WARN] Database '{DB_NAME}' is corrupted, recreating...")
                    cursor.execute(f"DROP DATABASE `{DB_NAME}`")
                    cursor.execute(
                        f"CREATE DATABASE `{DB_NAME}` "
                        "DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci"
                    )
            else:
                cursor.execute(
                    f"CREATE DATABASE `{DB_NAME}` "
                    "DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci"
                )
        conn.close()
        print(f"[INFO] Database '{DB_NAME}' is ready.")
    except Exception as e:
        print(f"[WARN] Could not auto-create database: {e}")


def _ensure_directories():
    os.makedirs(AVATAR_FOLDER, exist_ok=True)
    os.makedirs(GOODS_FOLDER, exist_ok=True)
    os.makedirs(VIDEOS_FOLDER, exist_ok=True)


def _run_migrations():
    """Idempotent schema migrations for existing databases."""
    from models import db as _db
    try:
        with _db.engine.connect() as conn:
            # Add balance column if not exists
            result = conn.execute(
                _db.text("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                         "WHERE TABLE_SCHEMA = :db AND TABLE_NAME = 'users' AND COLUMN_NAME = 'balance'"),
                {'db': DB_NAME}
            )
            if result.scalar() == 0:
                conn.execute(_db.text("ALTER TABLE users ADD COLUMN balance DECIMAL(10,2) NOT NULL DEFAULT 200.00 COMMENT '账户余额'"))
                conn.commit()
                print("[MIGRATION] Added balance column to users table")

            # Add video column if not exists
            result = conn.execute(
                _db.text("SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
                         "WHERE TABLE_SCHEMA = :db AND TABLE_NAME = 'goods' AND COLUMN_NAME = 'video'"),
                {'db': DB_NAME}
            )
            if result.scalar() == 0:
                conn.execute(_db.text("ALTER TABLE goods ADD COLUMN video VARCHAR(500) DEFAULT NULL COMMENT '商品视频'"))
                conn.execute(_db.text("ALTER TABLE goods ADD COLUMN video_likes INT DEFAULT 0 COMMENT '视频点赞数'"))
                conn.execute(_db.text("ALTER TABLE goods ADD COLUMN video_shares INT DEFAULT 0 COMMENT '视频分享数'"))
                conn.commit()
                print("[MIGRATION] Added video columns to goods table")
    except Exception as e:
        print(f"[WARN] Migration check failed (may be OK if tables don't exist yet): {e}")


app = create_app()

# Run migrations after app context is available
with app.app_context():
    _run_migrations()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
