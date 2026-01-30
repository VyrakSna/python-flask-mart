from models import db
from datetime import datetime


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    compare_price = db.Column(db.Numeric(10, 2), nullable=True)  # Original price for discounts
    cost_price = db.Column(db.Numeric(10, 2), nullable=True)  # Cost for profit calculation

    # Inventory
    sku = db.Column(db.String(100), unique=True, nullable=True)
    stock_quantity = db.Column(db.Integer, default=0, nullable=False)
    low_stock_threshold = db.Column(db.Integer, default=10, nullable=False)

    # Product details
    image_url = db.Column(db.String(500), nullable=True)
    weight = db.Column(db.Numeric(10, 2), nullable=True)  # in kg
    dimensions = db.Column(db.String(100), nullable=True)  # e.g., "10x20x30 cm"

    # Category relationship
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)

    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Product {self.name}>'

    @property
    def in_stock(self):
        """Check if product is in stock"""
        return self.stock_quantity > 0

    @property
    def is_low_stock(self):
        """Check if product is low in stock"""
        return 0 < self.stock_quantity <= self.low_stock_threshold

    @property
    def discount_percentage(self):
        """Calculate discount percentage if compare_price exists"""
        if self.compare_price and self.compare_price > self.price:
            return round(((self.compare_price - self.price) / self.compare_price) * 100)
        return 0

    @property
    def profit_margin(self):
        """Calculate profit margin if cost_price exists"""
        if self.cost_price and self.cost_price > 0:
            return round(((self.price - self.cost_price) / self.price) * 100, 2)
        return 0

    def to_dict(self):
        """Convert product to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'price': float(self.price),
            'compare_price': float(self.compare_price) if self.compare_price else None,
            'cost_price': float(self.cost_price) if self.cost_price else None,
            'sku': self.sku,
            'stock_quantity': self.stock_quantity,
            'low_stock_threshold': self.low_stock_threshold,
            'image_url': self.image_url,
            'weight': float(self.weight) if self.weight else None,
            'dimensions': self.dimensions,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'is_active': self.is_active,
            'is_featured': self.is_featured,
            'in_stock': self.in_stock,
            'is_low_stock': self.is_low_stock,
            'discount_percentage': self.discount_percentage,
            'profit_margin': self.profit_margin,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }