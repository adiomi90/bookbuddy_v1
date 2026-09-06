import random
from faker import Faker
from datetime import datetime, timedelta, timezone

fake = Faker()

# --- Configuration ---
NUM_BOOKS = 50
NUM_LOANS = 150
USER_IDS = list(range(7, 105))  # Matches the users we just imported

# --- Generate Books SQL ---
books_sql = []
for i in range(1, NUM_BOOKS + 1):
    isbn = f"978{random.randint(1000000000, 9999999999)}"
    title = fake.catch_phrase().replace("'", "''")
    author = fake.name().replace("'", "''")
    publisher = fake.company().replace("'", "''")
    pub_year = random.randint(1990, 2025)
    summary = fake.paragraph(nb_sentences=3).replace("'", "''")
    quantity = random.randint(3, 10)
    created_at = fake.date_time_between(start_date="-2y", end_date="now").strftime("%Y-%m-%d %H:%M:%S")
    
    sql = (
        f"INSERT INTO books (id, isbn, title, author, publisher, publisher_year, summary, quantity, created_at, updated_at) "
        f"VALUES ({i}, '{isbn}', '{title}', '{author}', '{publisher}', {pub_year}, '{summary}', {quantity}, '{created_at}', '{created_at}');"
    )
    books_sql.append(sql)

with open("insert_books.sql", "w") as f:
    f.write("\n".join(books_sql))
print(f"Generated {NUM_BOOKS} books in insert_books.sql")

# --- Generate Loans SQL ---
loans_sql = []
for i in range(1, NUM_LOANS + 1):
    user_id = random.choice(USER_IDS)
    book_id = random.randint(1, NUM_BOOKS)
    
    # Borrowed date within the last 6 months (perfect for your monthly trends endpoint!)
    borrowed_date = fake.date_time_between(start_date="-6M", end_date="now")
    
    # Status logic
    status = random.choices(
        ["borrowed", "returned", "overdue"], 
        weights=[0.4, 0.4, 0.2]
    )[0]
    
    # Due date is usually 7, 14, or 30 days after borrowed_date
    due_date = borrowed_date + timedelta(days=random.choice([7, 14, 30]))
    
    renewal_count = random.randint(0, 2)
    fine_amount = 0.0
    payment_status = None
    payment_submitted_date = None
    returned_date = None
    
    if status == "returned":
        # Returned a few days before or after due_date
        days_diff = random.randint(-5, 10)
        returned_date = due_date + timedelta(days=days_diff)
        if returned_date > due_date:
            fine_amount = round(random.uniform(2.0, 25.0), 2)
            payment_status = random.choice(["unpaid", "pending", "paid"])
            if payment_status == "paid":
                payment_submitted_date = returned_date + timedelta(days=random.randint(1, 10))
    elif status == "overdue":
        # Overdue means due_date MUST be in the past
        if due_date > datetime.now():
            due_date = datetime.now() - timedelta(days=random.randint(1, 20))
        fine_amount = round(random.uniform(2.0, 25.0), 2)
        payment_status = random.choice(["unpaid", "pending"])
        
    # Format dates for PostgreSQL
    def fmt(dt):
        return f"'{dt.strftime('%Y-%m-%d %H:%M:%S')}'" if dt else "NULL"
        
    payment_status_sql = f"'{payment_status}'" if payment_status else "NULL"

    sql = (
        f"INSERT INTO loans (id, user_id, book_id, status, due_date, renewal_count, fine_amount, "
        f"payment_status, payment_submitted_date, returned_date, borrowed_date, created_at, updated_at) "
        f"VALUES ({i}, {user_id}, {book_id}, '{status}', {fmt(due_date)}, {renewal_count}, {fine_amount}, "
        f"{payment_status_sql}, {fmt(payment_submitted_date)}, {fmt(returned_date)}, {fmt(borrowed_date)}, {fmt(borrowed_date)}, {fmt(borrowed_date)});"
    )
    loans_sql.append(sql)

with open("insert_loans.sql", "w") as f:
    f.write("\n".join(loans_sql))
print(f"Generated {NUM_LOANS} loans in insert_loans.sql")