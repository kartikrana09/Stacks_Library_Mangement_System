# Stacks — College Library Availability & Reservation System

A DE & VL mini project: a Flask + SQLite web app that solves the "is this
book available?" problem for a fully manual, paper-based college library.

Seeded with PCCOE's real Computer Department book list — **1,370 actual
titles**, not sample data.

## Features

**Students**
- Search the catalog by title, author, or ISBN; filter by category
- See real-time availability for every title
- Reserve a book that's currently issued — auto-notified when it's returned
  ("Ready for pickup" shows right on their dashboard)
- "My shelf" dashboard: currently issued books (with due dates), active
  reservations, and past return history

**Librarian / admin**
- Add books one at a time, or **bulk-upload a whole CSV** at once
- Issue a book to a student (14-day loan, tracked automatically)
- Mark a book returned — auto-calculates late fines and auto-notifies the
  next person in the reservation queue
- Dashboard: total titles/copies, currently issued, overdue list, most
  borrowed books, pending reservations

## Setup

```bash
cd library_system
pip install -r requirements.txt
flask seed
python app.py
```

Open **http://127.0.0.1:5000** in your browser. `flask seed` creates the
database and imports the full 1,370-book catalog from `data_books.csv` in
one step, plus the demo accounts below.

### Demo accounts
| Role | Login | Password |
|---|---|---|
| Student | roll no `DEMO001` | `demo123` |
| Librarian | username `admin` | `admin123` |

## Adding more books later

Two ways, both in the librarian dashboard under "Manage catalog":
- **Add a book** — one title at a time, via a form
- **Bulk upload CSV** — upload a `.csv` file with columns `title`, `author`
  (required) and `publisher`, `category`, `isbn`, `total_copies`, `price`
  (all optional). This is exactly how `data_books.csv` was loaded, and it's
  the same path `flask seed` uses — so any future book list export from the
  library just needs the right column headers to import cleanly.

## Project structure

```
library_system/
├── app.py              # Flask app: models, routes, business logic
├── book_import.py       # Shared CSV → Book import logic (seed + bulk upload)
├── seed_data.py         # Loads data_books.csv + demo accounts via `flask seed`
├── data_books.csv        # The real 1,370-title Computer Department catalog
├── requirements.txt
├── templates/            # Jinja2 templates
└── static/
    ├── css/style.css     # Design system (see comments at top of file)
    └── js/main.js        # Cursor-tilt cards, magnetic buttons, count-up stats
```

## Database schema

- **Book** — title, author, ISBN, publisher, category, total/available copies, price
- **Student** — roll no, name, email, password (hashed)
- **Admin** — username, password (hashed)
- **Transaction** — one row per issue; issue/due/return dates, fine, status
- **Reservation** — one row per reservation; status (Waiting / Notified /
  Fulfilled / Cancelled)

## Future scope

- ISBN-lookup API (Open Library / Google Books) to auto-fill details when
  adding a book by ISBN alone
- Real email/SMS delivery for reservation and due-date notifications
- "Similar book" recommendations when a title is unavailable
- Exportable issue/return reports for library records
