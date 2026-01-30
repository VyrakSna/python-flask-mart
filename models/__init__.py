from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()


def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        # Import models here to ensure they're registered
        from models.user import User
        # from models.product import Product
        # from models.catalog import Catalog
        # from models.orders import Order
        # Create tables if they don't exist
        db.create_all()

    return db