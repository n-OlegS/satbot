import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
import sheets

parser = argparse.ArgumentParser()
parser.add_argument("--all", action="store_true", help="Export all tests")
parser.add_argument("--test", action="store_true", help="Write dummy data to verify connectivity")
args = parser.parse_args()

if args.test:
    print(sheets.export_dummy())
elif args.all:
    for msg in sheets.export_all():
        print(msg)
else:
    print(sheets.export_test(sheets._cursor().execute(
        'select val from kv where key = "current_tid"'
    ).fetchone()[0]))
