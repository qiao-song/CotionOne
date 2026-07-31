from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

from models.user import User
from models.goods import Goods
from models.order import Order
from models.review import Review
