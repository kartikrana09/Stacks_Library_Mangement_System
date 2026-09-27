"""Shared CSV → Book import logic.

Expected columns (case-insensitive): title, author, publisher, category,
total_copies, price. Only title and author are required; everything else
is optional and falls back to a sensible default. Used by both the one-time
`flask seed` command and the librarian's "Bulk upload" admin feature, so a
real library CSV and the seed dataset go through the exact same path.
"""

import csv
import io


def import_books_csv(db, Book, file_obj):
    """file_obj: any file-like object opened in text mode, or a path string.
    Returns (added_count, skipped_count, errors) where errors is a list of
    short strings describing rows that couldn't be imported.
    """
    if isinstance(file_obj, str):
        f = open(file_obj, newline='', encoding='utf-8-sig')
        owns_file = True
    else:
        # Werkzeug file uploads give bytes; decode to text for csv.DictReader.
        stream = file_obj.stream if hasattr(file_obj, 'stream') else file_obj
        raw = stream.read()
        if isinstance(raw, bytes):
            raw = raw.decode('utf-8-sig', errors='replace')
        f = io.StringIO(raw)
        owns_file = False

    added, skipped, errors = 0, 0, []
    try:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            errors.append('The file appears to be empty or not a valid CSV.')
            return added, skipped, errors

        headers = {h.strip().lower(): h for h in reader.fieldnames}
        if 'title' not in headers or 'author' not in headers:
            errors.append('CSV must have at least "title" and "author" columns.')
            return added, skipped, errors

        for i, row in enumerate(reader, start=2):  # row 1 is the header
            title = (row.get(headers['title']) or '').strip()
            author = (row.get(headers['author']) or '').strip()
            if not title or not author:
                skipped += 1
                errors.append(f'Row {i}: missing title or author, skipped.')
                continue

            publisher = (row.get(headers.get('publisher', ''), '') or '').strip()
            category = (row.get(headers.get('category', ''), '') or '').strip() or 'General'
            isbn = (row.get(headers.get('isbn', ''), '') or '').strip()

            try:
                copies_raw = (row.get(headers.get('total_copies', ''), '') or '').strip()
                copies = int(float(copies_raw)) if copies_raw else 1
                if copies < 1:
                    copies = 1
            except ValueError:
                copies = 1

            price = None
            price_raw = (row.get(headers.get('price', ''), '') or '').strip()
            if price_raw:
                try:
                    price = round(float(price_raw), 2)
                except ValueError:
                    price = None

            db.session.add(Book(
                title=title, author=author, isbn=isbn, publisher=publisher,
                category=category, total_copies=copies, available_copies=copies,
                price=price
            ))
            added += 1

        db.session.commit()
    finally:
        if owns_file:
            f.close()

    return added, skipped, errors
