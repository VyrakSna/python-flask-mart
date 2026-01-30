#!/usr/bin/env python3
"""
Database initialization and management script
"""
from app import app
from models import db
from models.user import User


def check_database():
    """Check database connection and existing tables"""
    with app.app_context():
        try:
            # Try to query users table
            user_count = User.query.count()
            print(f"✓ Database connection successful!")
            print(f"✓ Users table exists with {user_count} users")
            return True
        except Exception as e:
            print(f"✗ Database error: {str(e)}")
            return False


def list_users():
    """List all users in the database"""
    with app.app_context():
        users = User.query.all()

        if not users:
            print("No users found in database.")
            return

        print(f"\n{'ID':<5} {'Username':<20} {'Email':<30} {'Admin':<10} {'Created At'}")
        print("=" * 85)

        for user in users:
            created = user.created_at.strftime('%Y-%m-%d %H:%M')
            admin_status = "Yes" if user.is_admin else "No"
            print(f"{user.id:<5} {user.username:<20} {user.email:<30} {admin_status:<10} {created}")


def create_user(username, email, password, is_admin=False):
    """Create a new user"""
    with app.app_context():
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            print(f"✗ User with email '{email}' already exists!")
            return False

        if User.query.filter_by(username=username).first():
            print(f"✗ User with username '{username}' already exists!")
            return False

        # Create new user
        new_user = User(
            username=username,
            email=email,
            is_admin=is_admin
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        admin_text = " (Admin)" if is_admin else ""
        print(f"✓ User '{username}' created successfully{admin_text}!")
        return True


def make_admin(username_or_email):
    """Make a user an admin"""
    with app.app_context():
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if not user:
            print(f"✗ User '{username_or_email}' not found!")
            return False

        if user.is_admin:
            print(f"✓ User '{user.username}' is already an admin!")
            return True

        user.is_admin = True
        db.session.commit()

        print(f"✓ User '{user.username}' is now an admin!")
        return True


def remove_admin(username_or_email):
    """Remove admin privileges from a user"""
    with app.app_context():
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if not user:
            print(f"✗ User '{username_or_email}' not found!")
            return False

        if not user.is_admin:
            print(f"✓ User '{user.username}' is not an admin!")
            return True

        user.is_admin = False
        db.session.commit()

        print(f"✓ Admin privileges removed from '{user.username}'!")
        return True


def delete_user(username_or_email):
    """Delete a user"""
    with app.app_context():
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()

        if not user:
            print(f"✗ User '{username_or_email}' not found!")
            return False

        response = input(f"Are you sure you want to delete user '{user.username}'? (yes/no): ")
        if response.lower() == 'yes':
            db.session.delete(user)
            db.session.commit()
            print(f"✓ User '{user.username}' deleted successfully!")
            return True
        else:
            print("Delete cancelled.")
            return False


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Database Management Script")
        print("=" * 50)
        print("\nUsage:")
        print("  python init_db.py check                              - Check database connection")
        print("  python init_db.py list                               - List all users")
        print("  python init_db.py create <username> <email> <pass>   - Create a new user")
        print("  python init_db.py create-admin <user> <email> <pass> - Create an admin user")
        print("  python init_db.py make-admin <username/email>        - Make user an admin")
        print("  python init_db.py remove-admin <username/email>      - Remove admin privileges")
        print("  python init_db.py delete <username/email>            - Delete a user")
        print("\nExamples:")
        print("  python init_db.py create john john@email.com pass123")
        print("  python init_db.py create-admin admin admin@email.com admin123")
        print("  python init_db.py make-admin john")
        print("  python init_db.py list")

    elif sys.argv[1] == 'check':
        check_database()

    elif sys.argv[1] == 'list':
        list_users()

    elif sys.argv[1] == 'create':
        if len(sys.argv) != 5:
            print("Usage: python init_db.py create <username> <email> <password>")
        else:
            create_user(sys.argv[2], sys.argv[3], sys.argv[4])

    elif sys.argv[1] == 'create-admin':
        if len(sys.argv) != 5:
            print("Usage: python init_db.py create-admin <username> <email> <password>")
        else:
            create_user(sys.argv[2], sys.argv[3], sys.argv[4], is_admin=True)

    elif sys.argv[1] == 'make-admin':
        if len(sys.argv) != 3:
            print("Usage: python init_db.py make-admin <username/email>")
        else:
            make_admin(sys.argv[2])

    elif sys.argv[1] == 'remove-admin':
        if len(sys.argv) != 3:
            print("Usage: python init_db.py remove-admin <username/email>")
        else:
            remove_admin(sys.argv[2])

    elif sys.argv[1] == 'delete':
        if len(sys.argv) != 3:
            print("Usage: python init_db.py delete <username/email>")
        else:
            delete_user(sys.argv[2])

    else:
        print(f"Unknown command: {sys.argv[1]}")
        print("Run 'python init_db.py' without arguments to see available commands.")