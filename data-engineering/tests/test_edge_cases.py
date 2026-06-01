# data-engineering/tests/fixtures/generate_edge_cases.py

import csv
import json
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
COLUMNS = ["id", "name", "email", "age", "department", "salary", "hire_date"]


def save_csv(filename, rows):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  created  {filename}  ({len(rows)} rows)")


def save_json(filename, rows):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    print(f"  created  {filename}  ({len(rows)} rows)")


# Edge case 1: Empty file
# Header only — zero data rows
# Expected: engine handles gracefully, does not crash

def generate_empty():
    path = os.path.join(OUTPUT_DIR, "empty.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
    print(f"  created  empty.csv  (0 rows)")


# Edge case 2: Single row 
# Exactly one valid row
# Expected: engine runs normally, score = 100

def generate_single_row():
    rows = [
        {"id": 1, "name": "Alice Smith", "email": "alice@company.com",
         "age": 30, "department": "Engineering", "salary": 85000,
         "hire_date": "2020-01-15"},
    ]
    save_csv("single_row.csv", rows)


# Edge case 3: All nulls 
# Every value is empty — worst possible data
# Expected: all rules fail, score = 0

def generate_all_nulls():
    rows = [
        {"id": "", "name": "", "email": "", "age": "",
         "department": "", "salary": "", "hire_date": ""},
        {"id": "", "name": "", "email": "", "age": "",
         "department": "", "salary": "", "hire_date": ""},
        {"id": "", "name": "", "email": "", "age": "",
         "department": "", "salary": "", "hire_date": ""},
    ]
    save_csv("all_nulls.csv", rows)


# Edge case 4: Single column bad
# Everything clean except salary has wrong types
# Expected: only salary/value_range rule fails

def generate_one_bad_column():
    rows = [
        {"id": 1, "name": "Alice Smith",  "email": "alice@company.com",  "age": 30, "department": "Engineering", "salary": "abc",    "hire_date": "2020-01-15"},
        {"id": 2, "name": "Bob Jones",    "email": "bob@company.com",    "age": 28, "department": "Marketing",   "salary": "high",   "hire_date": "2020-03-20"},
        {"id": 3, "name": "Carol White",  "email": "carol@company.com",  "age": 35, "department": "Engineering", "salary": "N/A",    "hire_date": "2019-06-01"},
        {"id": 4, "name": "David Brown",  "email": "david@company.com",  "age": 42, "department": "HR",          "salary": 78000,    "hire_date": "2018-11-10"},
        {"id": 5, "name": "Eve Davis",    "email": "eve@company.com",    "age": 38, "department": "Finance",     "salary": 83000,    "hire_date": "2021-05-22"},
    ]
    save_csv("one_bad_column.csv", rows)


# Edge case 5: Duplicate emails
# All data valid except emails are duplicated
# Expected: unique rule fails on email column

def generate_duplicates():
    rows = [
        {"id": 1, "name": "Alice Smith",  "email": "alice@company.com", "age": 30, "department": "Engineering", "salary": 85000, "hire_date": "2020-01-15"},
        {"id": 2, "name": "Bob Jones",    "email": "alice@company.com", "age": 28, "department": "Marketing",   "salary": 72000, "hire_date": "2020-03-20"},
        {"id": 3, "name": "Carol White",  "email": "carol@company.com", "age": 35, "department": "Engineering", "salary": 95000, "hire_date": "2019-06-01"},
        {"id": 4, "name": "David Brown",  "email": "carol@company.com", "age": 42, "department": "HR",          "salary": 78000, "hire_date": "2018-11-10"},
        {"id": 5, "name": "Eve Davis",    "email": "eve@company.com",   "age": 38, "department": "Finance",     "salary": 83000, "hire_date": "2021-05-22"},
    ]
    save_csv("duplicates.csv", rows)


# Edge case 6: Out of range values 
# Age and salary outside valid range
# Expected: value_range rule fails

def generate_out_of_range():
    rows = [
        {"id": 1, "name": "Alice Smith", "email": "alice@company.com", "age": -5,  "department": "Engineering", "salary": -1000,   "hire_date": "2020-01-15"},
        {"id": 2, "name": "Bob Jones",   "email": "bob@company.com",   "age": 200, "department": "Marketing",   "salary": 9999999, "hire_date": "2020-03-20"},
        {"id": 3, "name": "Carol White", "email": "carol@company.com", "age": 0,   "department": "Engineering", "salary": 0,       "hire_date": "2019-06-01"},
        {"id": 4, "name": "David Brown", "email": "david@company.com", "age": 999, "department": "HR",          "salary": 78000,   "hire_date": "2018-11-10"},
        {"id": 5, "name": "Eve Davis",   "email": "eve@company.com",   "age": 38,  "department": "Finance",     "salary": 83000,   "hire_date": "2021-05-22"},
    ]
    save_csv("out_of_range.csv", rows)


# Edge case 7: JSON format
# Same as good_data but in JSON format
# Expected: engine handles JSON same as CSV

def generate_json():
    rows = [
        {"id": 1, "name": "Alice Smith", "email": "alice@company.com", "age": 30, "department": "Engineering", "salary": 85000, "hire_date": "2020-01-15"},
        {"id": 2, "name": "Bob Jones",   "email": "bob@company.com",   "age": 28, "department": "Marketing",   "salary": 72000, "hire_date": "2020-03-20"},
        {"id": 3, "name": "Carol White", "email": "carol@company.com", "age": 35, "department": "Engineering", "salary": 95000, "hire_date": "2019-06-01"},
        {"id": 4, "name": "David Brown", "email": "david@company.com", "age": 42, "department": "HR",          "salary": 78000, "hire_date": "2018-11-10"},
        {"id": 5, "name": "Eve Davis",   "email": "eve@company.com",   "age": 38, "department": "Finance",     "salary": 83000, "hire_date": "2021-05-22"},
    ]
    save_json("good_data.json", rows)


# Run all

if __name__ == "__main__":
    print("\nGenerating edge case fixture files...\n")
    generate_empty()
    generate_single_row()
    generate_all_nulls()
    generate_one_bad_column()
    generate_duplicates()
    generate_out_of_range()
    generate_json()
    print(f"\nAll edge case fixtures generated in: {OUTPUT_DIR}\n")