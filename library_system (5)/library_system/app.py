"""
College Library Availability & Reservation System
DE & VL Mini Project

Run with:  python app.py
Then open: http://127.0.0.1:5000
"""

from datetime import date, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'campus-library-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

ISSUE_PERIOD_DAYS = 14
FINE_PER_DAY = 5  # rupees


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(20))
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    publisher = db.Column(db.String(150))
    category = db.Column(db.String(80), default='General')
    total_copies = db.Column(db.Integer, default=1)
    available_copies = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, nullable=True)

    @property
    def status(self):
        if self.available_copies > 0:
            return 'Available'
        return 'Issued'


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    issue_date = db.Column(db.Date, default=date.today)
    due_date = db.Column(db.Date)
    return_date = db.Column(db.Date, nullable=True)
    fine = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='Issued')  # Issued / Returned

    book = db.relationship('Book')
    student = db.relationship('Student')


class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    reservation_date = db.Column(db.Date, default=date.today)
    status = db.Column(db.String(20), default='Waiting')  # Waiting / Notified / Fulfilled / Cancelled

    book = db.relationship('Book')
    student = db.relationship('Student')


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def student_login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('student_id'):
            flash('Please log in to continue.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


def admin_login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin_id'):
            flash('Please log in as admin to continue.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return wrapper


def current_student():
    sid = session.get('student_id')
    return Student.query.get(sid) if sid else None


@app.context_processor
def inject_globals():
    return dict(current_student=current_student())


# ---------------------------------------------------------------------------
# Public / student routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 24

    query = Book.query
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(Book.title.ilike(like), Book.author.ilike(like), Book.isbn.ilike(like)))
    if category:
        query = query.filter(Book.category == category)

    total_count = query.count()
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))

    books = query.order_by(Book.title).offset((page - 1) * per_page).limit(per_page).all()
    categories = sorted(c[0] for c in db.session.query(Book.category).distinct() if c[0])

    overall_total = Book.query.count()
    overall_available = db.session.query(db.func.count(Book.id)).filter(Book.available_copies > 0).scalar() or 0
    overall_categories = len(categories)

    featured = None
    if page == 1 and not q and not category and overall_total:
        pick_index = date.today().toordinal() % overall_total
        featured = Book.query.order_by(Book.id).offset(pick_index).limit(1).first()

    return render_template('index.html', books=books, q=q, categories=categories,
                            active_category=category, page=page, total_pages=total_pages,
                            total_count=total_count, overall_total=overall_total,
                            overall_available=overall_available, overall_categories=overall_categories,
                            featured=featured)


@app.route('/book/<int:book_id>')
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    already_reserved = False
    student = current_student()
    if student:
        already_reserved = Reservation.query.filter_by(
            book_id=book.id, student_id=student.id, status='Waiting').first() is not None
    queue_len = Reservation.query.filter_by(book_id=book.id, status='Waiting').count()
    return render_template('book_detail.html', book=book, already_reserved=already_reserved, queue_len=queue_len)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        roll_no = request.form['roll_no'].strip()
        name = request.form['name'].strip()
        email = request.form.get('email', '').strip()
        password = request.form['password']

        if Student.query.filter_by(roll_no=roll_no).first():
            flash('That roll number is already registered.', 'error')
            return redirect(url_for('register'))

        student = Student(roll_no=roll_no, name=name, email=email)
        student.set_password(password)
        db.session.add(student)
        db.session.commit()
        flash('Account created. You can log in now.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        roll_no = request.form['roll_no'].strip()
        password = request.form['password']
        student = Student.query.filter_by(roll_no=roll_no).first()
        if student and student.check_password(password):
            session['student_id'] = student.id
            flash(f'Welcome back, {student.name.split()[0]}.', 'success')
            return redirect(url_for('index'))
        flash('Incorrect roll number or password.', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('student_id', None)
    flash('Logged out.', 'success')
    return redirect(url_for('index'))


@app.route('/dashboard')
@student_login_required
def dashboard():
    student = current_student()
    issued = Transaction.query.filter_by(student_id=student.id, status='Issued').all()
    history = Transaction.query.filter_by(student_id=student.id, status='Returned').order_by(
        Transaction.return_date.desc()).all()
    reservations = Reservation.query.filter(
        Reservation.student_id == student.id,
        Reservation.status.in_(['Waiting', 'Notified'])
    ).order_by(Reservation.status.desc()).all()
    today = date.today()
    return render_template('dashboard.html', issued=issued, history=history,
                            reservations=reservations, today=today)


@app.route('/reserve/<int:book_id>', methods=['POST'])
@student_login_required
def reserve(book_id):
    student = current_student()
    book = Book.query.get_or_404(book_id)

    existing = Reservation.query.filter_by(book_id=book.id, student_id=student.id, status='Waiting').first()
    if existing:
        flash('You already have a reservation on this title.', 'error')
    elif book.available_copies > 0:
        flash('This copy is available right now — no need to reserve, go issue it.', 'error')
    else:
        r = Reservation(book_id=book.id, student_id=student.id)
        db.session.add(r)
        db.session.commit()
        flash(f'Reserved "{book.title}". You are #{Reservation.query.filter_by(book_id=book.id, status="Waiting").count()} in line.', 'success')

    return redirect(url_for('book_detail', book_id=book.id))


@app.route('/reserve/<int:res_id>/cancel', methods=['POST'])
@student_login_required
def cancel_reservation(res_id):
    student = current_student()
    r = Reservation.query.get_or_404(res_id)
    if r.student_id != student.id:
        flash('Not your reservation.', 'error')
    else:
        r.status = 'Cancelled'
        db.session.commit()
        flash('Reservation cancelled.', 'success')
    return redirect(url_for('dashboard'))


# ---------------------------------------------------------------------------
# Admin routes
# ---------------------------------------------------------------------------

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            flash('Welcome back, librarian.', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Incorrect credentials.', 'error')
    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    return redirect(url_for('index'))


@app.route('/admin')
@admin_login_required
def admin_dashboard():
    total_books = Book.query.count()
    total_copies = db.session.query(db.func.sum(Book.total_copies)).scalar() or 0
    issued_count = Transaction.query.filter_by(status='Issued').count()
    overdue = [t for t in Transaction.query.filter_by(status='Issued').all() if t.due_date < date.today()]
    pending_reservations = Reservation.query.filter_by(status='Waiting').count()

    most_borrowed = db.session.query(
        Book.title, db.func.count(Transaction.id).label('cnt')
    ).join(Transaction, Transaction.book_id == Book.id).group_by(Book.id).order_by(
        db.desc('cnt')).limit(5).all()

    return render_template('admin_dashboard.html', total_books=total_books, total_copies=total_copies,
                            issued_count=issued_count, overdue=overdue,
                            pending_reservations=pending_reservations, most_borrowed=most_borrowed,
                            today=date.today())


@app.route('/admin/books')
@admin_login_required
def admin_books():
    books = Book.query.order_by(Book.title).all()
    return render_template('admin_books.html', books=books)


@app.route('/admin/books/add', methods=['GET', 'POST'])
@admin_login_required
def admin_add_book():
    if request.method == 'POST':
        title = request.form['title'].strip()
        author = request.form['author'].strip()
        isbn = request.form.get('isbn', '').strip()
        publisher = request.form.get('publisher', '').strip()
        category = request.form.get('category', 'General').strip() or 'General'
        copies = int(request.form.get('total_copies', 1) or 1)

        book = Book(title=title, author=author, isbn=isbn, publisher=publisher,
                    category=category, total_copies=copies, available_copies=copies)
        db.session.add(book)
        db.session.commit()
        flash(f'Added "{title}" to the catalog.', 'success')
        return redirect(url_for('admin_books'))

    return render_template('admin_add_book.html')


@app.route('/admin/books/bulk-upload', methods=['GET', 'POST'])
@admin_login_required
def admin_bulk_upload():
    if request.method == 'POST':
        file = request.files.get('csv_file')
        if not file or file.filename == '':
            flash('Please choose a CSV file to upload.', 'error')
            return redirect(url_for('admin_bulk_upload'))
        if not file.filename.lower().endswith('.csv'):
            flash('Please upload a .csv file.', 'error')
            return redirect(url_for('admin_bulk_upload'))

        from book_import import import_books_csv
        added, skipped, errors = import_books_csv(db, Book, file)

        msg = f'Imported {added} book{"s" if added != 1 else ""}.'
        if skipped:
            msg += f' Skipped {skipped} row{"s" if skipped != 1 else ""} with missing data.'
        flash(msg, 'success' if added else 'error')
        for e in errors[:10]:
            flash(e, 'error')

        return redirect(url_for('admin_books'))

    return render_template('admin_bulk_upload.html')


@app.route('/admin/books/<int:book_id>/delete', methods=['POST'])
@admin_login_required
def admin_delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash('Book removed from catalog.', 'success')
    return redirect(url_for('admin_books'))


@app.route('/admin/issue', methods=['GET', 'POST'])
@admin_login_required
def admin_issue():
    if request.method == 'POST':
        roll_no = request.form['roll_no'].strip()
        book_id = int(request.form['book_id'])

        student = Student.query.filter_by(roll_no=roll_no).first()
        book = Book.query.get(book_id)

        if not student:
            flash('No student with that roll number.', 'error')
        elif not book:
            flash('Book not found.', 'error')
        elif book.available_copies <= 0:
            flash('No copies available to issue.', 'error')
        else:
            book.available_copies -= 1
            t = Transaction(book_id=book.id, student_id=student.id,
                             issue_date=date.today(),
                             due_date=date.today() + timedelta(days=ISSUE_PERIOD_DAYS),
                             status='Issued')
            db.session.add(t)
            db.session.commit()
            flash(f'Issued "{book.title}" to {student.name}. Due {t.due_date.strftime("%d %b %Y")}.', 'success')
        return redirect(url_for('admin_issue'))

    books = Book.query.filter(Book.available_copies > 0).order_by(Book.title).all()
    return render_template('admin_issue.html', books=books)


@app.route('/admin/return/<int:transaction_id>', methods=['POST'])
@admin_login_required
def admin_return(transaction_id):
    t = Transaction.query.get_or_404(transaction_id)
    t.return_date = date.today()
    t.status = 'Returned'

    if t.return_date > t.due_date:
        days_late = (t.return_date - t.due_date).days
        t.fine = days_late * FINE_PER_DAY

    t.book.available_copies += 1

    next_res = Reservation.query.filter_by(book_id=t.book_id, status='Waiting').order_by(
        Reservation.reservation_date).first()
    if next_res:
        next_res.status = 'Notified'

    db.session.commit()
    msg = f'Marked "{t.book.title}" returned.'
    if t.fine:
        msg += f' Fine: Rs {t.fine}.'
    if next_res:
        msg += f' {next_res.student.name} has been notified — it was on their reserve list.'
    flash(msg, 'success')
    return redirect(url_for('admin_transactions'))


@app.route('/admin/transactions')
@admin_login_required
def admin_transactions():
    issued = Transaction.query.filter_by(status='Issued').order_by(Transaction.due_date).all()
    returned = Transaction.query.filter_by(status='Returned').order_by(Transaction.return_date.desc()).limit(20).all()
    today = date.today()
    return render_template('admin_transactions.html', issued=issued, returned=returned, today=today)


@app.route('/admin/reservations')
@admin_login_required
def admin_reservations():
    reservations = Reservation.query.filter(Reservation.status.in_(['Waiting', 'Notified'])).order_by(
        Reservation.reservation_date).all()
    return render_template('admin_reservations.html', reservations=reservations)


# ---------------------------------------------------------------------------
# CLI bootstrap
# ---------------------------------------------------------------------------

@app.cli.command('seed')
def seed():
    """Create tables (if needed) and populate sample books + demo accounts."""
    from seed_data import run_seed
    db.create_all()
    run_seed(db)
    print('Seeded database.')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Admin.query.filter_by(username='admin').first():
            a = Admin(username='admin')
            a.set_password('admin123')
            db.session.add(a)
            db.session.commit()
    app.run(debug=True)
