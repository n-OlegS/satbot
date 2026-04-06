import sqlite3
import os
import pathlib
import argparse
import dotenv
import gspread
from google.oauth2.service_account import Credentials

dotenv.load_dotenv()

MEDIA_PATH = os.getenv("MEDIA_PATH")
SHEETS_CREDENTIALS = os.getenv("SHEETS_CREDENTIALS")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

if MEDIA_PATH is None:
    quit("Unspecified media folder path!")
if SHEETS_CREDENTIALS is None:
    quit("No Google Sheets credentials path specified!")
if SPREADSHEET_ID is None:
    quit("No spreadsheet ID specified!")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

parser = argparse.ArgumentParser()
parser.add_argument("--all", action="store_true", help="Export all tests, not just the current one")
parser.add_argument("--test", action="store_true", help="Write dummy data to a test sheet to verify connectivity")
args = parser.parse_args()

db_path = pathlib.Path(MEDIA_PATH) / "data.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

creds = Credentials.from_service_account_file(SHEETS_CREDENTIALS, scopes=SCOPES)
gc = gspread.authorize(creds)
spreadsheet = gc.open_by_key(SPREADSHEET_ID)


def export_test(t_id):
    user_ids = [row[0] for row in cursor.execute(
        f"select distinct id from answers where t_id = {t_id} order by id"
    ).fetchall()]

    if not user_ids:
        print(f"Test {t_id}: no answers found, skipping.")
        return

    columns = []
    for uid in user_ids:
        completed_at = cursor.execute(
            f"select start_t from users where id = {uid}"
        ).fetchone()
        completed_at = round(completed_at[0]) if completed_at else ""

        answers_rows = cursor.execute(
            f"select q_id, answer from answers where t_id = {t_id} and id = {uid} order by q_id"
        ).fetchall()
        answers = {q_id: ans for q_id, ans in answers_rows}

        col = [uid, completed_at] + [answers.get(q, "") for q in range(1, 45)]
        columns.append(col)

    # Append empty answer key column for manual filling
    columns.append(["Answer Key", ""] + [""] * 44)

    # Transpose columns -> rows, then prepend row labels
    labels = ["User ID", "Completed (unix)"] + [f"Q{q}" for q in range(1, 45)]
    rows = [
        [label] + list(row)
        for label, row in zip(labels, zip(*columns))
    ]

    sheet_name = f"Test {t_id}"
    try:
        sheet = spreadsheet.worksheet(sheet_name)
        sheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows=50, cols=20)

    sheet.update(rows, "A1")
    print(f"Test {t_id}: exported {len(user_ids)} student(s).")


if args.test:
    import random
    import time as time_module

    fake_users = [111111111, 222222222, 333333333]
    options = ["a", "b", "c", "d"]

    columns = []
    for uid in fake_users:
        col = [uid, round(time_module.time())] + [random.choice(options) for _ in range(44)]
        columns.append(col)
    columns.append(["Answer Key", ""] + [random.choice(options) for _ in range(44)])

    labels = ["User ID", "Completed (unix)"] + [f"Q{q}" for q in range(1, 45)]
    rows = [
        [label] + list(row)
        for label, row in zip(labels, zip(*columns))
    ]

    sheet_name = "TEST (delete me)"
    try:
        sheet = spreadsheet.worksheet(sheet_name)
        sheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows=50, cols=20)

    sheet.update(rows, "A1")
    print(f"Test sheet written successfully — check '{sheet_name}' in your spreadsheet.")

elif args.all:
    test_ids = [row[0] for row in cursor.execute(
        "select distinct t_id from answers order by t_id"
    ).fetchall()]
    for t_id in test_ids:
        export_test(t_id)
else:
    row = cursor.execute('select val from kv where key = "current_tid"').fetchone()
    if row:
        export_test(int(row[0]))

conn.close()
