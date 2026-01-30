from functools import wraps
from flask import session, redirect, url_for, flash
from models.user import User


def login_required(f):
    """Decorator to require login for a route"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """Decorator to require admin privileges for a route"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))

        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('You need administrator privileges to access this page.', 'error')
            return redirect(url_for('catalog'))

        return f(*args, **kwargs)

    return decorated_function