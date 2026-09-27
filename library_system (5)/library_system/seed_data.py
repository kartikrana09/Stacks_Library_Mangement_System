"""Real dataset — run with: flask seed
Loads the actual PCCOE Computer Department book list (data_books.csv,
1,370 titles) plus a demo student and the admin account, so the system
demos with the real catalog instead of typed-in sample data.
"""

import os

DATA_CSV = os.path.join(os.path.dirname(__file__), 'data_books.csv')


def run_seed(db):
    from app import Book, Student, Admin
    from book_import import import_books_csv

    if not Admin.query.filter_by(username='admin').first():
        a = Admin(username='admin')
        a.set_password('admin123')
        db.session.add(a)

    if not Student.query.filter_by(roll_no='DEMO001').first():
        s = Student(roll_no='DEMO001', name='Demo Student', email='demo@student.pccoe.edu')
        s.set_password('demo123')
        db.session.add(s)

    db.session.commit()

    if Book.query.count() == 0 and os.path.exists(DATA_CSV):
        added, skipped, errors = import_books_csv(db, Book, DATA_CSV)
        print(f'Imported {added} books from data_books.csv ({skipped} skipped).')
