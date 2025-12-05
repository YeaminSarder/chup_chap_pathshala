from flask import render_template
from flask_login import login_required
from app.main import bp
from app.models import Book

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/catalog')
def catalog():
    books = Book.query.all()
    return render_template('catalog.html', books=books)

@bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')
