#!/usr/bin/env python3
"""
Initialize Product and Category tables in the database
"""
from app import app
from models import db
from models.category import Category
from models.product import Product


def init_tables():
    """Create product and category tables"""
    with app.app_context():
        print("Creating product and category tables...")
        try:
            db.create_all()
            print("✓ Tables created successfully!")

            # Check table counts
            category_count = Category.query.count()
            product_count = Product.query.count()

            print(f"✓ Categories: {category_count}")
            print(f"✓ Products: {product_count}")

        except Exception as e:
            print(f"✗ Error: {str(e)}")


def create_sample_data():
    """Create sample categories and products"""
    with app.app_context():
        print("\nCreating sample data...")

        # Check if data already exists
        if Category.query.count() > 0:
            print("Sample data already exists!")
            return

        try:
            # Create categories
            electronics = Category(
                name='Electronics',
                slug='electronics',
                description='Electronic devices and gadgets',
                is_active=True
            )

            home_kitchen = Category(
                name='Home & Kitchen',
                slug='home-kitchen',
                description='Home and kitchen appliances',
                is_active=True
            )

            accessories = Category(
                name='Accessories',
                slug='accessories',
                description='Various accessories and gear',
                is_active=True
            )

            sports = Category(
                name='Sports & Fitness',
                slug='sports-fitness',
                description='Sports equipment and fitness gear',
                is_active=True
            )

            db.session.add_all([electronics, home_kitchen, accessories, sports])
            db.session.commit()

            print("✓ Created 4 categories")

            # Create products
            products = [
                Product(
                    name='Wireless Headphones',
                    slug='wireless-headphones',
                    description='Premium wireless headphones with noise cancellation and 30-hour battery life.',
                    price=99.99,
                    compare_price=129.99,
                    cost_price=60.00,
                    sku='WH-001',
                    stock_quantity=50,
                    low_stock_threshold=10,
                    image_url='https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400',
                    category=electronics,
                    is_active=True,
                    is_featured=True
                ),
                Product(
                    name='Smart Watch',
                    slug='smart-watch',
                    description='Advanced smartwatch with health tracking, GPS, and 7-day battery.',
                    price=249.99,
                    compare_price=299.99,
                    cost_price=150.00,
                    sku='SW-001',
                    stock_quantity=30,
                    image_url='https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400',
                    category=electronics,
                    is_active=True,
                    is_featured=True
                ),
                Product(
                    name='Coffee Maker',
                    slug='coffee-maker',
                    description='Programmable coffee maker with thermal carafe.',
                    price=129.99,
                    cost_price=70.00,
                    sku='CM-001',
                    stock_quantity=25,
                    image_url='https://images.unsplash.com/photo-1559131397-f94da358f7ca?w=400',
                    category=home_kitchen,
                    is_active=True
                ),
                Product(
                    name='Laptop Backpack',
                    slug='laptop-backpack',
                    description='Durable laptop backpack with multiple compartments and USB charging port.',
                    price=79.99,
                    compare_price=99.99,
                    cost_price=40.00,
                    sku='LB-001',
                    stock_quantity=8,  # Low stock
                    image_url='https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400',
                    category=accessories,
                    is_active=True
                ),
                Product(
                    name='Bluetooth Speaker',
                    slug='bluetooth-speaker',
                    description='Portable Bluetooth speaker with 360-degree sound and waterproof design.',
                    price=59.99,
                    cost_price=30.00,
                    sku='BS-001',
                    stock_quantity=100,
                    image_url='https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400',
                    category=electronics,
                    is_active=True
                ),
                Product(
                    name='Yoga Mat',
                    slug='yoga-mat',
                    description='Premium yoga mat with excellent grip and cushioning.',
                    price=34.99,
                    cost_price=15.00,
                    sku='YM-001',
                    stock_quantity=0,  # Out of stock
                    image_url='https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=400',
                    category=sports,
                    is_active=True
                )
            ]

            db.session.add_all(products)
            db.session.commit()

            print(f"✓ Created {len(products)} products")
            print("\n✓ Sample data created successfully!")

        except Exception as e:
            db.session.rollback()
            print(f"✗ Error creating sample data: {str(e)}")


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python init_products.py init     - Create tables")
        print("  python init_products.py sample   - Create sample data")
    elif sys.argv[1] == 'init':
        init_tables()
    elif sys.argv[1] == 'sample':
        create_sample_data()
    else:
        print(f"Unknown command: {sys.argv[1]}")