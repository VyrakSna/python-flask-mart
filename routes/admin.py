from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from decorators import admin_required
from models import db
from models.product import Product
from models.category import Category
from models.order import Order, OrderItem
from slugify import slugify
from sqlalchemy import or_
import os
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def save_product_image(file):
    """Save uploaded product image and return the file path"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"

        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'products')
        os.makedirs(upload_dir, exist_ok=True)

        # Save file
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)

        # Return the URL path (relative to static folder)
        return f"/static/uploads/products/{filename}"
    return None


def delete_product_image(image_path):
    """Delete product image file"""
    if image_path and image_path.startswith('/static/'):
        try:
            # Convert URL path to file system path
            file_path = os.path.join(
                current_app.root_path,
                image_path.lstrip('/')
            )
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            current_app.logger.error(f"Error deleting image: {str(e)}")


# ============================================================================
# DASHBOARD
# ============================================================================

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard with statistics"""
    total_products = Product.query.count()
    active_products = Product.query.filter_by(is_active=True).count()
    low_stock_products = Product.query.filter(
        Product.stock_quantity > 0,
        Product.stock_quantity <= Product.low_stock_threshold
    ).count()
    out_of_stock = Product.query.filter_by(stock_quantity=0).count()

    total_categories = Category.query.count()
    active_categories = Category.query.filter_by(is_active=True).count()

    # Order statistics
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    approved_orders = Order.query.filter_by(status='approved').count()
    shipped_orders = Order.query.filter_by(status='shipped').count()

    # Recent products
    recent_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()

    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()

    stats = {
        'total_products': total_products,
        'active_products': active_products,
        'low_stock_products': low_stock_products,
        'out_of_stock': out_of_stock,
        'total_categories': total_categories,
        'active_categories': active_categories,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'approved_orders': approved_orders,
        'shipped_orders': shipped_orders,
        'recent_products': recent_products,
        'recent_orders': recent_orders
    }

    return render_template('admin/dashboard.html', stats=stats)


# ============================================================================
# CATEGORIES CRUD
# ============================================================================

@admin_bp.route('/categories')
@admin_required
def categories_list():
    """List all categories"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    search = request.args.get('search', '')

    query = Category.query

    if search:
        query = query.filter(
            or_(
                Category.name.ilike(f'%{search}%'),
                Category.description.ilike(f'%{search}%')
            )
        )

    categories = query.order_by(Category.name).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('admin/categories/list.html',
                           categories=categories,
                           search=search)


@admin_bp.route('/categories/create', methods=['GET', 'POST'])
@admin_required
def category_create():
    """Create new category"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        is_active = request.form.get('is_active') == 'on'

        if not name:
            flash('Category name is required.', 'error')
            return redirect(url_for('admin.category_create'))

        # Generate slug
        slug = slugify(name)

        # Check if slug already exists
        if Category.query.filter_by(slug=slug).first():
            flash('A category with this name already exists.', 'error')
            return redirect(url_for('admin.category_create'))

        try:
            category = Category(
                name=name,
                slug=slug,
                description=description if description else None,
                is_active=is_active
            )

            db.session.add(category)
            db.session.commit()

            flash(f'Category "{name}" created successfully!', 'success')
            return redirect(url_for('admin.categories_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error creating category: {str(e)}', 'error')
            return redirect(url_for('admin.category_create'))

    return render_template('admin/categories/create.html')


@admin_bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@admin_required
def category_edit(category_id):
    """Edit category"""
    category = Category.query.get_or_404(category_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        is_active = request.form.get('is_active') == 'on'

        if not name:
            flash('Category name is required.', 'error')
            return redirect(url_for('admin.category_edit', category_id=category_id))

        # Generate new slug if name changed
        new_slug = slugify(name)
        if new_slug != category.slug:
            if Category.query.filter_by(slug=new_slug).first():
                flash('A category with this name already exists.', 'error')
                return redirect(url_for('admin.category_edit', category_id=category_id))
            category.slug = new_slug

        try:
            category.name = name
            category.description = description if description else None
            category.is_active = is_active

            db.session.commit()

            flash(f'Category "{name}" updated successfully!', 'success')
            return redirect(url_for('admin.categories_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating category: {str(e)}', 'error')
            return redirect(url_for('admin.category_edit', category_id=category_id))

    return render_template('admin/categories/edit.html', category=category)


@admin_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@admin_required
def category_delete(category_id):
    """Delete category"""
    category = Category.query.get_or_404(category_id)

    # Check if category has products
    if category.products.count() > 0:
        flash(f'Cannot delete category "{category.name}" because it has {category.products.count()} products.', 'error')
        return redirect(url_for('admin.categories_list'))

    try:
        name = category.name
        db.session.delete(category)
        db.session.commit()

        flash(f'Category "{name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting category: {str(e)}', 'error')

    return redirect(url_for('admin.categories_list'))


# ============================================================================
# PRODUCTS CRUD
# ============================================================================

@admin_bp.route('/products')
@admin_required
def products_list():
    """List all products"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    search = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    status = request.args.get('status', '')

    query = Product.query

    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f'%{search}%'),
                Product.sku.ilike(f'%{search}%'),
                Product.description.ilike(f'%{search}%')
            )
        )

    if category_id:
        query = query.filter_by(category_id=category_id)

    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)
    elif status == 'low_stock':
        query = query.filter(
            Product.stock_quantity > 0,
            Product.stock_quantity <= Product.low_stock_threshold
        )
    elif status == 'out_of_stock':
        query = query.filter_by(stock_quantity=0)

    products = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()

    return render_template('admin/products/list.html',
                           products=products,
                           categories=categories,
                           search=search,
                           selected_category=category_id,
                           selected_status=status)


@admin_bp.route('/products/create', methods=['GET', 'POST'])
@admin_required
def product_create():
    """Create new product"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', type=float)
        compare_price = request.form.get('compare_price', type=float)
        cost_price = request.form.get('cost_price', type=float)
        sku = request.form.get('sku', '').strip()
        stock_quantity = request.form.get('stock_quantity', 0, type=int)
        low_stock_threshold = request.form.get('low_stock_threshold', 10, type=int)
        weight = request.form.get('weight', type=float)
        dimensions = request.form.get('dimensions', '').strip()
        category_id = request.form.get('category_id', type=int)
        is_active = request.form.get('is_active') == 'on'
        is_featured = request.form.get('is_featured') == 'on'

        # Handle image upload
        image_url = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                image_url = save_product_image(file)
                if not image_url:
                    flash('Invalid image file. Allowed types: png, jpg, jpeg, gif, webp', 'error')
                    return redirect(url_for('admin.product_create'))

        # Validation
        if not name:
            flash('Product name is required.', 'error')
            return redirect(url_for('admin.product_create'))

        if not price or price <= 0:
            flash('Valid price is required.', 'error')
            return redirect(url_for('admin.product_create'))

        # Generate slug
        slug = slugify(name)

        # Make slug unique if it already exists
        base_slug = slug
        counter = 1
        while Product.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        # Check if SKU exists
        if sku and Product.query.filter_by(sku=sku).first():
            flash('A product with this SKU already exists.', 'error')
            return redirect(url_for('admin.product_create'))

        try:
            product = Product(
                name=name,
                slug=slug,
                description=description if description else None,
                price=price,
                compare_price=compare_price if compare_price else None,
                cost_price=cost_price if cost_price else None,
                sku=sku if sku else None,
                stock_quantity=stock_quantity,
                low_stock_threshold=low_stock_threshold,
                image_url=image_url,
                weight=weight if weight else None,
                dimensions=dimensions if dimensions else None,
                category_id=category_id if category_id else None,
                is_active=is_active,
                is_featured=is_featured
            )

            db.session.add(product)
            db.session.commit()

            flash(f'Product "{name}" created successfully!', 'success')
            return redirect(url_for('admin.products_list'))

        except Exception as e:
            db.session.rollback()
            # Delete uploaded image if database operation failed
            if image_url:
                delete_product_image(image_url)
            flash(f'Error creating product: {str(e)}', 'error')
            return redirect(url_for('admin.product_create'))

    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    return render_template('admin/products/create.html', categories=categories)


@admin_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def product_edit(product_id):
    """Edit product"""
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price = request.form.get('price', type=float)
        compare_price = request.form.get('compare_price', type=float)
        cost_price = request.form.get('cost_price', type=float)
        sku = request.form.get('sku', '').strip()
        stock_quantity = request.form.get('stock_quantity', 0, type=int)
        low_stock_threshold = request.form.get('low_stock_threshold', 10, type=int)
        weight = request.form.get('weight', type=float)
        dimensions = request.form.get('dimensions', '').strip()
        category_id = request.form.get('category_id', type=int)
        is_active = request.form.get('is_active') == 'on'
        is_featured = request.form.get('is_featured') == 'on'
        remove_image = request.form.get('remove_image') == 'on'

        # Handle image upload
        old_image = product.image_url
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                new_image = save_product_image(file)
                if new_image:
                    # Delete old image
                    if old_image:
                        delete_product_image(old_image)
                    product.image_url = new_image
                else:
                    flash('Invalid image file. Allowed types: png, jpg, jpeg, gif, webp', 'error')
                    return redirect(url_for('admin.product_edit', product_id=product_id))

        # Remove image if requested
        if remove_image and product.image_url:
            delete_product_image(product.image_url)
            product.image_url = None

        # Validation
        if not name:
            flash('Product name is required.', 'error')
            return redirect(url_for('admin.product_edit', product_id=product_id))

        if not price or price <= 0:
            flash('Valid price is required.', 'error')
            return redirect(url_for('admin.product_edit', product_id=product_id))

        # Generate new slug if name changed
        new_slug = slugify(name)
        if new_slug != product.slug:
            # Make slug unique
            base_slug = new_slug
            counter = 1
            while Product.query.filter_by(slug=new_slug).filter(Product.id != product_id).first():
                new_slug = f"{base_slug}-{counter}"
                counter += 1
            product.slug = new_slug

        # Check if SKU exists (excluding current product)
        if sku and Product.query.filter_by(sku=sku).filter(Product.id != product_id).first():
            flash('A product with this SKU already exists.', 'error')
            return redirect(url_for('admin.product_edit', product_id=product_id))

        try:
            product.name = name
            product.description = description if description else None
            product.price = price
            product.compare_price = compare_price if compare_price else None
            product.cost_price = cost_price if cost_price else None
            product.sku = sku if sku else None
            product.stock_quantity = stock_quantity
            product.low_stock_threshold = low_stock_threshold
            product.weight = weight if weight else None
            product.dimensions = dimensions if dimensions else None
            product.category_id = category_id if category_id else None
            product.is_active = is_active
            product.is_featured = is_featured

            db.session.commit()

            flash(f'Product "{name}" updated successfully!', 'success')
            return redirect(url_for('admin.products_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'error')
            return redirect(url_for('admin.product_edit', product_id=product_id))

    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    return render_template('admin/products/edit.html', product=product, categories=categories)


@admin_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@admin_required
def product_delete(product_id):
    """Delete product"""
    product = Product.query.get_or_404(product_id)

    try:
        name = product.name
        image_url = product.image_url

        db.session.delete(product)
        db.session.commit()

        # Delete product image file
        if image_url:
            delete_product_image(image_url)

        flash(f'Product "{name}" deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}', 'error')

    return redirect(url_for('admin.products_list'))


# ============================================================================
# ORDERS MANAGEMENT
# ============================================================================

@admin_bp.route('/orders')
@admin_required
def orders_list():
    """List all orders"""
    page = request.args.get('page', 1, type=int)
    per_page = 20

    status_filter = request.args.get('status', '')
    search = request.args.get('search', '')

    query = Order.query

    if search:
        query = query.filter(
            or_(
                Order.order_number.ilike(f'%{search}%'),
                Order.customer_name.ilike(f'%{search}%'),
                Order.customer_email.ilike(f'%{search}%'),
                Order.customer_phone.ilike(f'%{search}%')
            )
        )

    if status_filter:
        query = query.filter_by(status=status_filter)

    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('admin/orders/list.html',
                           orders=orders,
                           selected_status=status_filter,
                           search=search)


@admin_bp.route('/orders/<int:order_id>')
@admin_required
def order_detail(order_id):
    """View order details"""
    order = Order.query.get_or_404(order_id)
    return render_template('admin/orders/detail.html', order=order)


@admin_bp.route('/orders/<int:order_id>/approve', methods=['POST'])
@admin_required
def order_approve(order_id):
    """Approve an order"""
    order = Order.query.get_or_404(order_id)

    if not order.can_approve:
        flash('This order cannot be approved.', 'error')
        return redirect(url_for('admin.order_detail', order_id=order_id))

    try:
        order.status = 'approved'
        order.approved_at = datetime.utcnow()

        admin_notes = request.form.get('admin_notes', '').strip()
        if admin_notes:
            order.admin_notes = admin_notes

        db.session.commit()

        flash(f'Order {order.order_number} has been approved!', 'success')

        # TODO: Send email notification to customer

    except Exception as e:
        db.session.rollback()
        flash(f'Error approving order: {str(e)}', 'error')

    return redirect(url_for('admin.order_detail', order_id=order_id))


@admin_bp.route('/orders/<int:order_id>/reject', methods=['POST'])
@admin_required
def order_reject(order_id):
    """Reject an order"""
    order = Order.query.get_or_404(order_id)

    if not order.can_reject:
        flash('This order cannot be rejected.', 'error')
        return redirect(url_for('admin.order_detail', order_id=order_id))

    try:
        order.status = 'rejected'

        admin_notes = request.form.get('admin_notes', '').strip()
        if admin_notes:
            order.admin_notes = admin_notes
        else:
            flash('Please provide a reason for rejection.', 'warning')
            return redirect(url_for('admin.order_detail', order_id=order_id))

        # Restore product stock
        for item in order.items:
            if item.product:
                item.product.stock_quantity += item.quantity

        db.session.commit()

        flash(f'Order {order.order_number} has been rejected.', 'success')

        # TODO: Send email notification to customer

    except Exception as e:
        db.session.rollback()
        flash(f'Error rejecting order: {str(e)}', 'error')

    return redirect(url_for('admin.order_detail', order_id=order_id))


@admin_bp.route('/orders/<int:order_id>/ship', methods=['POST'])
@admin_required
def order_ship(order_id):
    """Mark order as shipped"""
    order = Order.query.get_or_404(order_id)

    if not order.can_ship:
        flash('This order cannot be shipped.', 'error')
        return redirect(url_for('admin.order_detail', order_id=order_id))

    try:
        order.status = 'shipped'
        order.shipped_at = datetime.utcnow()

        tracking_number = request.form.get('tracking_number', '').strip()
        if tracking_number:
            if order.admin_notes:
                order.admin_notes += f"\n\nTracking Number: {tracking_number}"
            else:
                order.admin_notes = f"Tracking Number: {tracking_number}"

        db.session.commit()

        flash(f'Order {order.order_number} marked as shipped!', 'success')

        # TODO: Send shipping notification email to customer

    except Exception as e:
        db.session.rollback()
        flash(f'Error updating order: {str(e)}', 'error')

    return redirect(url_for('admin.order_detail', order_id=order_id))


@admin_bp.route('/orders/<int:order_id>/deliver', methods=['POST'])
@admin_required
def order_deliver(order_id):
    """Mark order as delivered"""
    order = Order.query.get_or_404(order_id)

    if order.status != 'shipped':
        flash('Only shipped orders can be marked as delivered.', 'error')
        return redirect(url_for('admin.order_detail', order_id=order_id))

    try:
        order.status = 'delivered'
        order.delivered_at = datetime.utcnow()

        db.session.commit()

        flash(f'Order {order.order_number} marked as delivered!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error updating order: {str(e)}', 'error')

    return redirect(url_for('admin.order_detail', order_id=order_id))


@admin_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
@admin_required
def order_cancel(order_id):
    """Cancel an order"""
    order = Order.query.get_or_404(order_id)

    if not order.can_cancel:
        flash('This order cannot be cancelled.', 'error')
        return redirect(url_for('admin.order_detail', order_id=order_id))

    try:
        order.status = 'cancelled'

        # Restore product stock
        for item in order.items:
            if item.product:
                item.product.stock_quantity += item.quantity

        db.session.commit()

        flash(f'Order {order.order_number} has been cancelled.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error cancelling order: {str(e)}', 'error')

    return redirect(url_for('admin.order_detail', order_id=order_id))


@admin_bp.route('/orders/<int:order_id>/update-notes', methods=['POST'])
@admin_required
def order_update_notes(order_id):
    """Update admin notes for an order"""
    order = Order.query.get_or_404(order_id)

    try:
        admin_notes = request.form.get('admin_notes', '').strip()
        order.admin_notes = admin_notes

        db.session.commit()

        flash('Order notes updated successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error updating notes: {str(e)}', 'error')

    return redirect(url_for('admin.order_detail', order_id=order_id))


# ============================================================================
# API ENDPOINTS (for AJAX operations)
# ============================================================================

@admin_bp.route('/api/products/<int:product_id>/toggle-active', methods=['POST'])
@admin_required
def api_product_toggle_active(product_id):
    """Toggle product active status"""
    product = Product.query.get_or_404(product_id)

    try:
        product.is_active = not product.is_active
        db.session.commit()

        return jsonify({
            'success': True,
            'is_active': product.is_active,
            'message': f'Product {"activated" if product.is_active else "deactivated"} successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@admin_bp.route('/api/products/<int:product_id>/toggle-featured', methods=['POST'])
@admin_required
def api_product_toggle_featured(product_id):
    """Toggle product featured status"""
    product = Product.query.get_or_404(product_id)

    try:
        product.is_featured = not product.is_featured
        db.session.commit()

        return jsonify({
            'success': True,
            'is_featured': product.is_featured,
            'message': f'Product {"featured" if product.is_featured else "unfeatured"} successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@admin_bp.route('/api/categories/<int:category_id>/toggle-active', methods=['POST'])
@admin_required
def api_category_toggle_active(category_id):
    """Toggle category active status"""
    category = Category.query.get_or_404(category_id)

    try:
        category.is_active = not category.is_active
        db.session.commit()

        return jsonify({
            'success': True,
            'is_active': category.is_active,
            'message': f'Category {"activated" if category.is_active else "deactivated"} successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500