from models import db
from datetime import datetime


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)

    # Customer information
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Nullable for guest checkout
    customer_name = db.Column(db.String(200), nullable=False)
    customer_email = db.Column(db.String(200), nullable=False)
    customer_phone = db.Column(db.String(50), nullable=False)

    # Shipping address
    shipping_address = db.Column(db.String(500), nullable=False)
    shipping_city = db.Column(db.String(100), nullable=True)
    shipping_state = db.Column(db.String(100), nullable=True)
    shipping_zip = db.Column(db.String(20), nullable=True)
    shipping_country = db.Column(db.String(100), nullable=True)

    # Order details
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    shipping_cost = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    tax = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)

    # Order status
    status = db.Column(db.String(50), default='pending', nullable=False)
    # Statuses: pending, approved, processing, shipped, delivered, cancelled, rejected

    # Payment information
    payment_method = db.Column(db.String(50), nullable=True)
    payment_status = db.Column(db.String(50), default='pending', nullable=False)
    # Payment statuses: pending, paid, failed, refunded

    # Notes
    customer_notes = db.Column(db.Text, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    shipped_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship('User', backref='orders', lazy=True)
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Order {self.order_number}>'

    @property
    def status_color(self):
        """Get color for status badge"""
        colors = {
            'pending': 'warning',
            'approved': 'info',
            'processing': 'primary',
            'shipped': 'success',
            'delivered': 'success',
            'cancelled': 'danger',
            'rejected': 'danger'
        }
        return colors.get(self.status, 'secondary')

    @property
    def can_approve(self):
        """Check if order can be approved"""
        return self.status == 'pending'

    @property
    def can_reject(self):
        """Check if order can be rejected"""
        return self.status == 'pending'

    @property
    def can_cancel(self):
        """Check if order can be cancelled"""
        return self.status in ['pending', 'approved', 'processing']

    @property
    def can_ship(self):
        """Check if order can be shipped"""
        return self.status in ['approved', 'processing']

    def to_dict(self):
        """Convert order to dictionary"""
        return {
            'id': self.id,
            'order_number': self.order_number,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'customer_phone': self.customer_phone,
            'shipping_address': self.shipping_address,
            'shipping_city': self.shipping_city,
            'shipping_state': self.shipping_state,
            'shipping_zip': self.shipping_zip,
            'shipping_country': self.shipping_country,
            'subtotal': float(self.subtotal),
            'shipping_cost': float(self.shipping_cost),
            'tax': float(self.tax),
            'total': float(self.total),
            'status': self.status,
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'customer_notes': self.customer_notes,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'items': [item.to_dict() for item in self.items]
        }


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)

    # Product details (stored in case product is deleted)
    product_name = db.Column(db.String(200), nullable=False)
    product_sku = db.Column(db.String(100), nullable=True)
    product_image = db.Column(db.String(500), nullable=True)

    # Pricing
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    # Relationship
    product = db.relationship('Product', backref='order_items', lazy=True)

    def __repr__(self):
        return f'<OrderItem {self.product_name} x{self.quantity}>'

    def to_dict(self):
        """Convert order item to dictionary"""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'product_sku': self.product_sku,
            'product_image': self.product_image,
            'price': float(self.price),
            'quantity': self.quantity,
            'subtotal': float(self.subtotal)
        }