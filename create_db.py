# create_db.py

import sqlite3
import pathlib

db_path = pathlib.Path("data/sample_kb.sqlite")
db_path.parent.mkdir(exist_ok=True)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS kb")
cur.execute("""
CREATE TABLE kb (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    content TEXT
)
""")

cur.execute(
    "INSERT INTO kb (title, content) VALUES (?, ?)",
    ("Login Issue", "User cannot log in. Steps: reset password, check email, clear browser cache.")
)

cur.execute(
    "INSERT INTO kb (title, content) VALUES (?, ?)",
    ("Payment Failure", "Payment failed. Steps: retry, verify card, update billing address.")
)

conn.commit()
conn.close()

print("Database created successfully at:", db_path)
