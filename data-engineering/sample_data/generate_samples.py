"""Generate sample datasets with configurable error rate - DE2 Odile."""

import random
import csv
import os
from datetime import datetime, timedelta

DEPARTMENTS = ["Engineering", "Marketing", "Sales", "HR", "Finance"]
FIRST_NAMES = ["Alice", "Bob", "Carol", "David", "Eve", "Frank",
               "Grace", "Henry", "Ivy", "Jack", "Kate", "Leo",
               "Mia", "Nathan", "Olivia", "Paul", "Quinn", "Rachel"]
LAST_NAMES  = ["Smith", "Jones", "White", "Brown", "Davis", "Miller",
               "Wilson", "Taylor", "Anderson", "Thomas", "Jackson", "Martin"]


def make_clean_row(i):
    """Generate one perfectly valid row."""
    name  = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
    email = f"{name.split()[0].lower()}_{i}@company.com"
    age   = random.randint(22, 60)
    dept  = random.choice(DEPARTMENTS)
    sal   = random.randint(50000, 150000)
    days  = random.randint(30, 2000)
    hire  = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return [i, name, email, age, dept, sal, hire]


def corrupt_row(row):
    """Randomly corrupt one field in a row."""
    row = list(row)
    choice = random.randint(0, 5)
    if   choice == 0: row[1] = ""                          # null name
    elif choice == 1: row[2] = "not-valid-email"           # bad email
    elif choice == 2: row[3] = random.choice([-5, 0, 200]) # bad age
    elif choice == 3: row[4] = ""                          # null dept
    elif choice == 4: row[5] = "abc"                       # bad salary
    elif choice == 5: row[6] = ""                          # null hire_date
    return row


def save_csv(rows, output_path):
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "email", "age",
                         "department", "salary", "hire_date"])
        writer.writerows(rows)
    print(f"  saved → {os.path.basename(output_path)} ({len(rows)} rows)")


def compute_score(rows):
    """
    Score = % of rows where ALL fields are valid.
    Matches the DataPulse scoring spec: % of rows passing all rules.
    """
    passed = 0
    for row in rows:
        _, name, email, age, dept, salary, hire = row
        try:
            age_ok    = isinstance(age, int) and 18 <= age <= 65
            sal_ok    = str(salary).lstrip("-").isdigit() and int(float(str(salary))) > 0
            name_ok   = bool(str(name).strip())
            email_ok  = bool(str(email).strip()) and "@" in str(email)
            dept_ok   = bool(str(dept).strip())
            hire_ok   = bool(str(hire).strip())
            if all([name_ok, email_ok, age_ok, dept_ok, sal_ok, hire_ok]):
                passed += 1
        except Exception:
            pass
    return round(passed / len(rows) * 100, 1) if rows else 0


def generate_dataset(num_rows=100, error_rate=0.0, output_path="generated.csv"):
    """
    Generate a dataset with a given error rate.

    error_rate=0.00 → ~100% rows clean  → score ~100
    error_rate=0.05 → ~95%  rows clean  → score ~95
    error_rate=0.30 → ~70%  rows clean  → score ~70
    error_rate=0.60 → ~40%  rows clean  → score ~40
    """
    rows = []
    for i in range(1, num_rows + 1):
        row = make_clean_row(i)
        if random.random() < error_rate:
            row = corrupt_row(row)
        rows.append(row)

    save_csv(rows, output_path)
    score = compute_score(rows)
    print(f"  score  → {score}/100  (error_rate={error_rate})")
    return rows


if __name__ == "__main__":
    d = os.path.dirname(os.path.abspath(__file__))
    print("\nGenerating sample datasets...\n")

    # Small datasets (used directly in tests) 

    print("good_data.csv   — target score ~95")
    generate_dataset(
        num_rows=100,
        error_rate=0.05,
        output_path=os.path.join(d, "good_data.csv")
    )

    print("\nbad_data.csv    — target score ~40")
    generate_dataset(
        num_rows=100,
        error_rate=0.60,
        output_path=os.path.join(d, "bad_data.csv")
    )

    print("\nmixed_data.csv  — target score ~70")
    generate_dataset(
        num_rows=100,
        error_rate=0.30,
        output_path=os.path.join(d, "mixed_data.csv")
    )

    # Large datasets (for scale testing) 

    print("\nlarge_clean.csv  — target score ~95 (500 rows)")
    generate_dataset(
        num_rows=500,
        error_rate=0.05,
        output_path=os.path.join(d, "large_clean.csv")
    )

    print("\nlarge_dirty.csv  — target score ~40 (500 rows)")
    generate_dataset(
        num_rows=500,
        error_rate=0.60,
        output_path=os.path.join(d, "large_dirty.csv")
    )

    print("\nlarge_mixed.csv  — target score ~70 (500 rows)")
    generate_dataset(
        num_rows=500,
        error_rate=0.30,
        output_path=os.path.join(d, "large_mixed.csv")
    )

    print("\nAll datasets generated successfully.\n")