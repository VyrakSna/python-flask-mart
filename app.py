from http.client import responses

from flask import Flask, render_template, request, jsonify
from flask_mail import Mail, Message
import json
import os
import paypalrestsdk

from payments import BakongPayment
from telegram import sendMessage
from tabulate import tabulate
import payments

app = Flask(__name__)

PRODUCTS = [
    {
        'id': 1,
        'name': 'Wireless Headphones',
        'price': 99.99,
        'image': 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=300&fit=crop',
        'description': 'Premium wireless headphones with noise cancellation and 30-hour battery life. Perfect for music lovers and professionals.',
        'category': 'Electronics',
        'rating': 4.9,
        'in_stock': True
    },
    {
        'id': 2,
        'name': 'Smart Watch',
        'price': 249.99,
        'image': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=300&fit=crop',
        'description': 'Advanced smartwatch with health tracking, GPS, and 7-day battery. Monitor your fitness and stay connected.',
        'category': 'Electronics',
        'rating': 4.8,
        'in_stock': True
    },
    {
        'id': 3,
        'name': 'Coffee Maker',
        'price': 129.99,
        'image': 'https://images.unsplash.com/photo-1559131397-f94da358f7ca?w=400&h=300&fit=crop',
        'description': 'Programmable coffee maker with thermal carafe. Brew perfect coffee every morning with customizable settings.',
        'category': 'Home & Kitchen',
        'rating': 4.3,
        'in_stock': True
    },
    {
        'id': 4,
        'name': 'Laptop Backpack',
        'price': 79.99,
        'image': 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=300&fit=crop',
        'description': 'Durable laptop backpack with multiple compartments and USB charging port. Perfect for work and travel.',
        'category': 'Accessories',
        'rating': 4.6,
        'in_stock': True
    },
    {
        'id': 5,
        'name': 'Bluetooth Speaker',
        'price': 59.99,
        'image': 'https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400&h=300&fit=crop',
        'description': 'Portable Bluetooth speaker with 360-degree sound and waterproof design. Great for outdoor adventures.',
        'category': 'Electronics',
        'rating': 4.4,
        'in_stock': True
    },
    {
        'id': 6,
        'name': 'Yoga Mat',
        'price': 34.99,
        'image': 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=400&h=300&fit=crop',
        'description': 'Premium yoga mat with excellent grip and cushioning. Made from eco-friendly materials.',
        'category': 'Sports & Fitness',
        'rating': 4.7,
        'in_stock': True
    }
]

paypalrestsdk.configure({
    "mode": "sandbox",
    "client_id": os.environ.get('PAYPAL_CLIENT_ID'),
    "client_secret": os.environ.get('PAYPAL_CLIENT_SECRET')
})

client_id = os.environ.get('PAYPAL_CLIENT_ID')
secret = os.environ.get('PAYPAL_CLIENT_SECRET')
@app.route('/create-order', methods=['POST'])
def create_order():
    """Create order using PayPal Orders API"""
    import requests

    # Get access token


    auth_response = requests.post(
        'https://api.sandbox.paypal.com/v1/oauth2/token',
        headers={'Accept': 'application/json'},
        auth=(client_id, secret),
        data={'grant_type': 'client_credentials'}
    )

    access_token = auth_response.json()['access_token']

    # Create order
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
def catalog():
    return render_template('catalog.html', products=PRODUCTS)




@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = next((p for p in PRODUCTS if p['id'] == product_id), None)
    if not product:
        return "Product not found", 404
    return render_template('product_detail.html', product=product)


@app.route('/cart')
def cart():
    return render_template('cart.html')


@app.route('/api/product/<int:product_id>')
def api_product(product_id):

    product = next((p for p in PRODUCTS if p['id'] == product_id), None)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify(product)

@app.get('/checkout')
def checkout():
    return render_template('checkout.html', client_id = client_id)

@app.post('/api/place-order')
def place_order():
    order_data = request.get_json()

    items = order_data.get('items', [])
    totals = order_data.get('totals', [])
    bill_info = order_data.get('billing', [])
    print(totals)
    name = bill_info['fullName']
    email = bill_info['email']
    phone = bill_info['phone']
    address = bill_info['address']

    table_data = []
    # total_amount = 0
    print(order_data)
    for item in items:
        subtotal = item['price'] * item['quantity']
        # total_amount += subtotal
        table_data.append([item['name'], item['price'], item['quantity'], subtotal])

    table_data.append(['SHIPPING', '', '', totals['shipping']])
    table_data.append(['───────────────', '────────', '────────', '──────────'])
    table_data.append(['TOTAL', '', '', totals['total']])

    items_table = tabulate(table_data, headers=['Name', 'Price', 'Quantity', 'Subtotal'])


    message_content = f"""<strong>Customer Name: {name}</strong>\n<strong>Email: {email}</strong>\n<strong>Phone: {phone}</strong>\n<strong>Address: {address}</strong>\n<pre>{items_table}</pre>
    """

    print(sendMessage('784362028', message_content))
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'kuaspvp1a@gmail.com'
    app.config['MAIL_PASSWORD'] = 'ozeu mnmw tkfk bcny'
    app.config['MAIL_DEFAULT_SENDER'] = 'kuaspvp1a@gmail.com'
    mail = Mail(app)

    msg = Message('Invoice From SU4.13 Shop', recipients=[email])
    msg.body = 'This is a plain text email sent from Flask.'
    message_html = render_template('mail/invoice.html',  name=name,
                               email=email,
                               phone=phone,
                               address=f"{address}, {bill_info.get('city', '')}, {bill_info.get('state', '')} {bill_info.get('zipCode', '')}, {bill_info.get('country', '')}".strip(', '),
                               full_address=bill_info,
                               items=items,
                               totals=totals,
                               notes=bill_info.get('notes', ''))
    msg.html = message_html
    mail.send(msg)

    return jsonify({
        'success': True,
        'message': 'Order placed successfully',
    }), 201

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


if __name__ == '__main__':
    app.run(debug=True)


