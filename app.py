import requests
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from functools import wraps

from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager

from models import db, init_db
from models.user import User
from models.category import Category
from models.product import Product

from flask_mail import Mail, Message
import json
import os
import paypalrestsdk

from payments import BakongPayment
from telegram import sendMessage
from tabulate import tabulate
import payments
from config import config

# Import admin blueprint
from routes.admin import admin_bp

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "fkdkasjfljdsfjas;klfjs"  # Change this!
jwt = JWTManager(app)
app.secret_key = "dsfijsdlfkasjdfjsadlkfj"

# Load configuration
config_name = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[config_name])

# Ensure upload directories exist
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'products'), exist_ok=True)

# Initialize database
init_db(app)

# Register admin blueprint
app.register_blueprint(admin_bp)


# Login required decorator - DEFINED AT MODULE LEVEL
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function

PRODUCTS = [
    {
        'id': 1,
        'name': 'Wireless Headphones',
        'sku': 'WH-001',
        'price': 99.99,
        'compare_price': 129.99,
        'image': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=300&fit=crop',
        'description': 'Premium wireless headphones with noise cancellation and 30-hour battery life. Perfect for music lovers and professionals.',
        'category': 'Electronics',
        'rating': 4.9,
        'in_stock': True,
        'stock_quantity': 50,
        'weight': 0.5,
        'brand': 'SoundMax',
        'created_at': '2025-01-01T00:00:00Z'
    },
    {
        'id': 2,
        'name': 'Smart Watch',
        'sku': 'SW-002',
        'price': 249.99,
        'compare_price': 299.99,
        'image': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=300&fit=crop',
        'description': 'Advanced smartwatch with health tracking, GPS, and 7-day battery. Monitor your fitness and stay connected.',
        'category': 'Electronics',
        'rating': 4.8,
        'in_stock': True,
        'stock_quantity': 35,
        'weight': 0.2,
        'brand': 'TechWear',
        'created_at': '2025-01-01T00:00:00Z'
    },
    {
        'id': 3,
        'name': 'Coffee Maker',
        'sku': 'CM-003',
        'price': 129.99,
        'compare_price': 159.99,
        'image': 'https://images.unsplash.com/photo-1559131397-f94da358f7ca?w=400&h=300&fit=crop',
        'description': 'Programmable coffee maker with thermal carafe. Brew perfect coffee every morning with customizable settings.',
        'category': 'Home & Kitchen',
        'rating': 4.3,
        'in_stock': True,
        'stock_quantity': 20,
        'weight': 2.5,
        'brand': 'BrewMaster',
        'created_at': '2025-01-01T00:00:00Z'
    },
    {
        'id': 4,
        'name': 'Laptop Backpack',
        'sku': 'LB-004',
        'price': 79.99,
        'compare_price': 99.99,
        'image': 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=300&fit=crop',
        'description': 'Durable laptop backpack with multiple compartments and USB charging port. Perfect for work and travel.',
        'category': 'Accessories',
        'rating': 4.6,
        'in_stock': True,
        'stock_quantity': 60,
        'weight': 1.0,
        'brand': 'UrbanCarry',
        'created_at': '2025-01-01T00:00:00Z'
    },
    {
        'id': 5,
        'name': 'Bluetooth Speaker',
        'sku': 'BS-005',
        'price': 59.99,
        'compare_price': 79.99,
        'image': 'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400&h=300&fit=crop',
        'description': 'Portable Bluetooth speaker with 360-degree sound and waterproof design. Great for outdoor adventures.',
        'category': 'Electronics',
        'rating': 4.4,
        'in_stock': True,
        'stock_quantity': 40,
        'weight': 0.8,
        'brand': 'BoomSound',
        'created_at': '2025-01-01T00:00:00Z'
    },
    {
        'id': 6,
        'name': 'Yoga Mat',
        'sku': 'YM-006',
        'price': 34.99,
        'compare_price': 49.99,
        'image': 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=400&h=300&fit=crop',
        'description': 'Premium yoga mat with excellent grip and cushioning. Made from eco-friendly materials.',
        'category': 'Sports & Fitness',
        'rating': 4.7,
        'in_stock': True,
        'stock_quantity': 100,
        'weight': 1.2,
        'brand': 'ZenFit',
        'created_at': '2025-01-01T00:00:00Z'
    }
]


# Add this function here
def seed_products():
    """Seed database with initial products"""
    from models.product import Product
    import re

    def create_slug(name):
        """Simple slug creation"""
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        return slug.strip('-')

    # Check if products already exist
    existing_count = Product.query.count()
    if existing_count > 0:
        print(f"Database already has {existing_count} products. Skipping seed.")
        return

    print("Seeding products into database...")

    for product_data in PRODUCTS:
        product = Product(
            name=product_data['name'],
            slug=create_slug(product_data['name']),
            sku=product_data['sku'],
            description=product_data['description'],
            price=product_data['price'],
            compare_price=product_data.get('compare_price'),
            image_url=product_data['image'],
            stock_quantity=product_data['stock_quantity'],
            weight=product_data.get('weight', 0),
            is_active=product_data.get('in_stock', True),
            is_featured=False,
            low_stock_threshold=10
        )
        db.session.add(product)

    try:
        db.session.commit()
        print(f"✓ Successfully seeded {len(PRODUCTS)} products into database")
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error seeding products: {e}")

paypalrestsdk.configure({
    "mode": "sandbox",
    "client_id": os.environ.get('PAYPAL_CLIENT_ID'),
    "client_secret": os.environ.get('PAYPAL_CLIENT_SECRET')
})

client_id = os.environ.get('PAYPAL_CLIENT_ID')
secret = os.environ.get('PAYPAL_CLIENT_SECRET')


@app.route('/create-order', methods=['POST'])
def create_order():
    """Create orders using PayPal Orders API"""
    import requests

    # Get access token
    auth_response = requests.post(
        'https://api.sandbox.paypal.com/v1/oauth2/token',
        headers={'Accept': 'application/json'},
        auth=(client_id, secret),
        data={'grant_type': 'client_credentials'}
    )

    access_token = auth_response.json()['access_token']

    # Create orders
    order_response = requests.post(
        'https://api.sandbox.paypal.com/v2/checkout/orders',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        },
        json={
            'intent': 'CAPTURE',
            'purchase_units': [{
                'amount': {
                    'currency_code': 'USD',
                    'value': '10.00'
                }
            }]
        }
    )

    return jsonify(order_response.json())


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('catalog'))
    return redirect(url_for('login'))


@app.route('/login')
def login():
    if 'user_id' in session:
        return redirect(url_for('catalog'))
    return render_template('auth/login.html')


@app.post('/login')
def login_user():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')

    # Validate input
    if not email or not password:
        flash('Email and password are required.', 'error')
        return redirect(url_for('login'))

    # Query user from database
    user = User.query.filter_by(email=email).first()

    if user and user.check_password(password):
        session['user_id'] = user.id
        session['username'] = user.username
        session.permanent = True
        flash(f'Welcome back, {user.username}!', 'success')

        # Redirect to next page if specified, otherwise catalog
        next_page = request.args.get('next')
        return redirect(next_page if next_page else url_for('catalog'))
    else:
        flash('Invalid email or password.', 'error')
        return redirect(url_for('login'))


@app.route('/register')
def register():
    if 'user_id' in session:
        return redirect(url_for('catalog'))
    return render_template('auth/register.html')


@app.post('/register')
def register_user():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    password_confirm = request.form.get('password_confirm', '')

    # Validate input
    if not all([username, email, password, password_confirm]):
        flash('All fields are required.', 'error')
        return redirect(url_for('register'))

    if password != password_confirm:
        flash('Passwords do not match.', 'error')
        return redirect(url_for('register'))

    if len(password) < 8:
        flash('Password must be at least 8 characters long.', 'error')
        return redirect(url_for('register'))

    if len(username) < 3:
        flash('Username must be at least 3 characters long.', 'error')
        return redirect(url_for('register'))

    # Check if user already exists
    if User.query.filter_by(email=email).first():
        flash('Email already registered.', 'error')
        return redirect(url_for('register'))

    if User.query.filter_by(username=username).first():
        flash('Username already taken.', 'error')
        return redirect(url_for('register'))

    # Create new user
    try:
        new_user = User(
            username=username,
            email=email
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    except Exception as e:
        db.session.rollback()
        app.logger.error(f'Registration error: {str(e)}')
        flash('An error occurred during registration. Please try again.', 'error')
        return redirect(url_for('register'))


@app.route('/logout')
@login_required
def logout():
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}!', 'info')
    return redirect(url_for('login'))


@app.route('/catalog')
@login_required
def catalog():
    # Get active products from database
    products = Product.query.filter_by(is_active=True).all()

    # Convert to dict format for template compatibility
    products_list = [{
        'id': p.id,
        'name': p.name,
        'sku': p.sku,
        'price': float(p.price),
        'compare_price': float(p.compare_price) if p.compare_price else None,
        'image': p.image_url,  # Map image_url to 'image' for template
        'description': p.description,
        'category': p.category.name if p.category else 'Uncategorized',
        'rating': 4.5,  # Default rating since your model doesn't have it
        'in_stock': p.in_stock,
        'stock_quantity': p.stock_quantity,
        'weight': float(p.weight) if p.weight else 0,
        'brand': 'Generic',  # Default brand since your model doesn't have it
    } for p in products]

    return render_template('catalog.html', products=products_list)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    # Get product from database
    product = Product.query.get_or_404(product_id)

    product_dict = {
        'id': product.id,
        'name': product.name,
        'sku': product.sku,
        'price': float(product.price),
        'compare_price': float(product.compare_price) if product.compare_price else None,
        'image': product.image_url,
        'description': product.description,
        'category': product.category.name if product.category else 'Uncategorized',
        'rating': 4.5,
        'in_stock': product.in_stock,
        'stock_quantity': product.stock_quantity,
        'weight': float(product.weight) if product.weight else 0,
        'brand': 'Generic',
    }
    return render_template('product_detail.html', product=product_dict)


@app.route('/api/product/<int:product_id>')
def api_product(product_id):
    # Get product from database
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    return jsonify({
        'id': product.id,
        'name': product.name,
        'sku': product.sku,
        'price': float(product.price),
        'compare_price': float(product.compare_price) if product.compare_price else None,
        'image': product.image_url,  # Frontend expects 'image'
        'description': product.description,
        'category': product.category.name if product.category else 'Uncategorized',
        'rating': 4.5,
        'in_stock': product.in_stock,
        'stock_quantity': product.stock_quantity,
        'weight': float(product.weight) if product.weight else 0,
        'brand': 'Generic',
    })
@app.route('/cart')
def cart():
    return render_template('cart.html')



@app.get('/checkout')
def checkout():
    return render_template('checkout.html', client_id=client_id)


@app.post('/api/place-order')
def place_order():
    from models.order import Order, OrderItem
    from models.product import Product
    import uuid
    import traceback
    import threading

    def send_notifications_async(order_number, name, email, phone, address, city, state, zip_code, country, items,
                                 totals, bill_info, notes):
        """Send email and telegram notifications in background"""
        with app.app_context():
            # Telegram
            try:
                table_data = []
                for item in items:
                    subtotal = item['price'] * item['quantity']
                    table_data.append([item['name'], item['price'], item['quantity'], subtotal])

                table_data.append(['SHIPPING', '', '', totals['shipping']])
                table_data.append(['───────────────', '────────', '────────', '──────────'])
                table_data.append(['TOTAL', '', '', totals['total']])

                items_table = tabulate(table_data, headers=['Name', 'Price', 'Quantity', 'Subtotal'])

                message_content = f"""<strong>🛒 NEW ORDER: {order_number}</strong>
<strong>Customer Name: {name}</strong>
<strong>Email: {email}</strong>
<strong>Phone: {phone}</strong>
<strong>Address: {address}, {city}, {state} {zip_code}, {country}</strong>
<pre>{items_table}</pre>
<strong>Status: PENDING APPROVAL</strong>
"""
                sendMessage('784362028', message_content)
                print("✓ Telegram notification sent")
            except Exception as e:
                print(f"⚠ Telegram failed: {e}")

            # Email
            try:
                from flask_mail import Mail, Message
                import socket
                socket.setdefaulttimeout(15)

                app.config['MAIL_SERVER'] = 'smtp.gmail.com'
                app.config['MAIL_PORT'] = 587
                app.config['MAIL_USE_TLS'] = True
                app.config['MAIL_USERNAME'] = 'kuaspvp1a@gmail.com'
                app.config['MAIL_PASSWORD'] = 'ozeu mnmw tkfk bcny'
                app.config['MAIL_DEFAULT_SENDER'] = 'kuaspvp1a@gmail.com'
                mail = Mail(app)

                msg = Message(f'Order Confirmation - {order_number}', recipients=[email])
                msg.body = f'Thank you for your order! Order number: {order_number}'
                message_html = render_template('mail/invoice.html',
                                               name=name,
                                               email=email,
                                               phone=phone,
                                               order_number=order_number,
                                               address=f"{address}, {city}, {state} {zip_code}, {country}".strip(', '),
                                               full_address=bill_info,
                                               items=items,
                                               totals=totals,
                                               notes=notes)
                msg.html = message_html
                mail.send(msg)
                print("✓ Email sent")
            except Exception as e:
                print(f"⚠ Email failed: {e}")

    order_data = request.get_json()

    items = order_data.get('items', [])
    totals = order_data.get('totals', {})
    bill_info = order_data.get('billing', {})

    if not items or not bill_info:
        return jsonify({'success': False, 'message': 'Invalid order data'}), 400

    name = bill_info.get('fullName', '')
    email = bill_info.get('email', '')
    phone = bill_info.get('phone', '')
    address = bill_info.get('address', '')
    city = bill_info.get('city', '')
    state = bill_info.get('state', '')
    zip_code = bill_info.get('zipCode', '')
    country = bill_info.get('country', '')
    notes = bill_info.get('notes', '')

    try:
        order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"

        order = Order(
            order_number=order_number,
            user_id=session.get('user_id'),
            customer_name=name,
            customer_email=email,
            customer_phone=phone,
            shipping_address=address,
            shipping_city=city,
            shipping_state=state,
            shipping_zip=zip_code,
            shipping_country=country,
            subtotal=totals.get('subtotal', 0),
            shipping_cost=totals.get('shipping', 0),
            tax=totals.get('tax', 0),
            total=totals.get('total', 0),
            status='pending',
            payment_status='pending',
            customer_notes=notes
        )

        db.session.add(order)
        db.session.flush()

        for item in items:
            product = Product.query.get(item.get('id'))

            if not product:
                raise Exception(f"Product ID {item.get('id')} not found")

            if not product.is_active:
                raise Exception(f"Product '{product.name}' is no longer available")

            if product.stock_quantity < item.get('quantity'):
                raise Exception(f"Insufficient stock for '{product.name}'")

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                product_name=product.name,
                product_sku=product.sku,
                product_image=product.image_url or item.get('image'),
                price=float(item.get('price')),
                quantity=item.get('quantity'),
                subtotal=float(item.get('price')) * item.get('quantity')
            )
            db.session.add(order_item)
            product.stock_quantity -= item.get('quantity')

        db.session.commit()
        print(f"✓ Order {order_number} created!")

        # Send notifications in background thread
        thread = threading.Thread(
            target=send_notifications_async,
            args=(
            order_number, name, email, phone, address, city, state, zip_code, country, items, totals, bill_info, notes)
        )
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'message': 'Order placed successfully',
            'order_number': order_number,
            'order_id': order.id
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ ERROR: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error placing order: {str(e)}'
        }), 500


# BAKONG PAYMENT API
payments_db = {}


@app.route('/bakong/form')
def getform_bakong():
    return render_template('bakong-testing.html')


@app.route('/payment/bakong/initiate', methods=['POST'])
def initiate_bakong_payment():
    """Initiate Bakong payment"""
    try:
        # Get form data
        amount = float(request.form.get('amount'))
        description = request.form.get('description', 'Payment')
        customer_name = request.form.get('customer_name', '')
        customer_email = request.form.get('customer_email', '')

        # Create Bakong payment
        bakong = BakongPayment()
        result = bakong.create_payment(
            amount=amount,
            currency='USD',
            description=description
        )

        if result['success']:
            payment_id = result['data'].get('payment_id')

            # Store payment info
            payments_db[payment_id] = {
                'payment_id': payment_id,
                'amount': amount,
                'description': description,
                'customer_name': customer_name,
                'customer_email': customer_email,
                'status': 'pending',
                'gateway': 'bakong'
            }

            # Generate QR code
            qr_result = bakong.generate_qr_code(payment_id)

            if qr_result['success']:
                return render_template('bakong_qr.html',
                                       payment_id=payment_id,
                                       qr_code=qr_result.get('qr_code'),
                                       amount=amount,
                                       description=description)
            else:
                return render_template('error.html',
                                       error='Failed to generate QR code')
        else:
            return render_template('error.html',
                                   error=result.get('error', 'Payment failed'))

    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route('/payment/bakong/status/<payment_id>')
def check_bakong_status(payment_id):
    """Check Bakong payment status (AJAX endpoint)"""
    bakong = BakongPayment()
    result = bakong.check_payment_status(payment_id)

    if result['success']:
        status = result['data'].get('status')

        # Update local database
        if payment_id in payments_db:
            payments_db[payment_id]['status'] = status

        return jsonify({
            'success': True,
            'status': status,
            'data': result['data']
        })
    else:
        return jsonify({
            'success': False,
            'error': result.get('error')
        })


@app.route('/payment/callback/bakong', methods=['POST'])
def bakong_callback():
    """Handle Bakong webhook callback"""
    data = request.get_json()
    signature = request.headers.get('X-Signature')

    bakong = BakongPayment()

    # Verify signature
    if not bakong.verify_callback(data, signature):
        app.logger.error('Invalid Bakong callback signature')
        return jsonify({'error': 'Invalid signature'}), 400

    payment_id = data.get('payment_id')
    status = data.get('status')

    # Update payment status in database
    if payment_id in payments_db:
        payments_db[payment_id]['status'] = status
        app.logger.info(f'Payment {payment_id} updated to {status}')

    return jsonify({'message': 'Callback received'}), 200


@app.route('/payment/success/<payment_id>')
def payment_success(payment_id):
    """Payment success page"""
    payment = payments_db.get(payment_id)

    if payment:
        return render_template('success.html', payment=payment)
    else:
        return render_template('error.html', error='Payment not found')


@app.route('/payment/failed')
def payment_failed():
    """Payment failed page"""
    return render_template('error.html', error='Payment failed or cancelled')

#
# # Error handlers
# @app.errorhandler(404)
# def not_found(error):
#     return render_template('errors/404.html'), 404
#
#
# @app.errorhandler(500)
# def internal_error(error):
#     db.session.rollback()
#     return render_template('errors/500.html'), 500
if __name__ == '__main__':
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        # Seed products into database
        seed_products()

    app.run(debug=True)