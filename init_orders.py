#!/usr/bin/env python3
"""
Initialize Orders tables in the database
"""
from app import app
from models import db
from models.order import Order, OrderItem


def init_orders_tables():
    """Create orders and order_items tables"""
    with app.app_context():
        print("Creating orders and order_items tables...")
        try:
            db.create_all()
            print("✓ Tables created successfully!")

            # Check table counts
            order_count = Order.query.count()

            print(f"✓ Orders: {order_count}")

        except Exception as e:
            print(f"✗ Error: {str(e)}")


def check_orders():
    """Check existing orders"""
    with app.app_context():
        print("\n" + "=" * 50)
        print("CHECKING ORDERS")
        print("=" * 50)

        orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()

        if not orders:
            print("No orders found in database.")
            return

        print(f"\n{'Order #':<15} {'Customer':<25} {'Total':<10} {'Status':<12} {'Date'}")
        print("=" * 85)

        for order in orders:
            created = order.created_at.strftime('%Y-%m-%d %H:%M')
            print(
                f"{order.order_number:<15} {order.customer_name:<25} ${order.total:<9.2f} {order.status:<12} {created}")


def get_order_stats():
    """Get orders statistics"""
    with app.app_context():
        print("\n" + "=" * 50)
        print("ORDER STATISTICS")
        print("=" * 50)

        total = Order.query.count()
        pending = Order.query.filter_by(status='pending').count()
        approved = Order.query.filter_by(status='approved').count()
        shipped = Order.query.filter_by(status='shipped').count()
        delivered = Order.query.filter_by(status='delivered').count()
        cancelled = Order.query.filter_by(status='cancelled').count()
        rejected = Order.query.filter_by(status='rejected').count()

        print(f"Total Orders: {total}")
        print(f"Pending: {pending}")
        print(f"Approved: {approved}")
        print(f"Shipped: {shipped}")
        print(f"Delivered: {delivered}")
        print(f"Cancelled: {cancelled}")
        print(f"Rejected: {rejected}")

        if total > 0:
            from sqlalchemy import func
            total_revenue = db.session.query(func.sum(Order.total)).filter(
                Order.status.in_(['approved', 'shipped', 'delivered'])
            ).scalar() or 0
            print(f"\nTotal Revenue (Approved+): ${total_revenue:.2f}")


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python init_orders.py init     - Create orders tables")
        print("  python init_orders.py check    - Check existing orders")
        print("  python init_orders.py stats    - Show orders statistics")
    elif sys.argv[1] == 'init':
        init_orders_tables()
    elif sys.argv[1] == 'check':
        check_orders()
    elif sys.argv[1] == 'stats':
        get_order_stats()
    else:
        print(f"Unknown command: {sys.argv[1]}")