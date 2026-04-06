import os
import random
import sqlite3
import pathlib
import time
import dotenv
import gspread
from google.oauth2.service_account import Credentials

dotenv.load_dotenv()

MEDIA_PATH = os.getenv("MEDIA_PATH")
SHEETS_CREDENTIALS = os.getenv("SHEETS_CREDENTIALS")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _spreadsheet():
    creds = Credentials.from_service_account_file(SHEETS_CREDENTIALS, scopes=SCOPES)
    gc = gspread.authorize(creds)
    return gc.open_by_key(SPREADSHEET_ID)


def _cursor():
    db_path = pathlib.Path(MEDIA_PATH) / "data.db"
    return sqlite3.connect(db_path).cursor()


def _write_sheet(spreadsheet, sheet_name, rows):
    try:
        sheet = spreadsheet.worksheet(sheet_name)
        sheet.clear()
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows=50, cols=20)
    sheet.update(rows, "A1")


def _build_rows(columns):
    labels = ["User ID", "Completed (unix)"] + [f"Q{q}" for q in range(1, 45)]
    return [
        [label] + list(row)
        for label, row in zip(labels, zip(*columns))
    ]


def export_test(t_id):
    cursor = _cursor()
    user_ids = [row[0] for row in cursor.execute(
        f"select distinct id from answers where t_id = {t_id} order by id"
    ).fetchall()]

    if not user_ids:
        return f"Test {t_id}: no answers found, skipping."

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

    columns.append(["Answer Key", ""] + [""] * 44)

    _write_sheet(_spreadsheet(), f"Test {t_id}", _build_rows(columns))
    return f"Test {t_id}: exported {len(user_ids)} student(s)."


def export_all():
    cursor = _cursor()
    test_ids = [row[0] for row in cursor.execute(
        "select distinct t_id from answers order by t_id"
    ).fetchall()]
    return [export_test(t_id) for t_id in test_ids]


def export_dummy():
    options = ["a", "b", "c", "d"]
    columns = [
        [uid, round(time.time())] + [random.choice(options) for _ in range(44)]
        for uid in [111111111, 222222222, 333333333]
    ]
    columns.append(["Answer Key", ""] + [random.choice(options) for _ in range(44)])

    _write_sheet(_spreadsheet(), "TEST (delete me)", _build_rows(columns))
    return "Test sheet written — check 'TEST (delete me)' in your spreadsheet."
