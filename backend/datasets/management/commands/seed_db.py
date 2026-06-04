"""
datasets/management/commands/seed_db.py
────────────────────────────────────────────────────────────────────────────────
Management command: python manage.py seed_db

Creates default users AND three sample datasets for development and demo:

    Dataset               Target score   Purpose
    ──────────────────    ────────────   ─────────────────────────────
    Employee Records      ~95            Clean data — few issues
    Sales Orders          ~40            Messy data — many failures
    Customer Records      ~70            Mixed data — moderate issues

Each dataset gets:
  • The CSV file saved to MEDIA_ROOT/uploads/<user_id>/
  • A Dataset record with row_count and columns populated
  • Validation rules covering all 4 rule types across the three datasets
  • One full quality check run (QualityReport + RuleFinding) for today
  • 6 days of historical TrendMetric records so trend charts have data

The command is IDEMPOTENT — safe to run multiple times.
It skips any record that already exists.

Run automatically by docker-compose on every container start.
"""

import csv
import io
import logging
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with default users and 3 sample datasets."

    def handle(self, *args, **options) -> None:
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding database..."))
        self._seed_users()
        self._seed_datasets()
        self.stdout.write(self.style.SUCCESS("Database seeded successfully."))

    # ── Users ─────────────────────────────────────────────────────────────────

    def _seed_users(self) -> None:
        admin, created = User.objects.get_or_create(
            email="admin@amalitech.com",
            defaults={
                "username": "admin",
                "role": "admin",
                "is_staff": True,
                "is_superuser": True,
                "is_email_verified": True,
            },
        )
        if created:
            admin.set_password("password123")
            admin.save()
            self.stdout.write(f"  Created admin:  {admin.email}")
        else:
            if not admin.is_email_verified:
                admin.is_email_verified = True
                admin.save(update_fields=["is_email_verified"])
            self.stdout.write(f"  Skipped admin:  {admin.email} (already exists)")

        user, created = User.objects.get_or_create(
            email="user@amalitech.com",
            defaults={
                "username": "testuser",
                "role": "user",
                "is_email_verified": True,
            },
        )
        if created:
            user.set_password("password123")
            user.save()
            self.stdout.write(f"  Created user:   {user.email}")
        else:
            if not user.is_email_verified:
                user.is_email_verified = True
                user.save(update_fields=["is_email_verified"])
            self.stdout.write(f"  Skipped user:   {user.email} (already exists)")

    # ── Datasets ──────────────────────────────────────────────────────────────

    def _seed_datasets(self) -> None:
        from datasets.models import Dataset

        user = User.objects.get(email="user@amalitech.com")

        titles = ["Employee Records", "Sales Orders", "Customer Records"]
        already = Dataset.objects.filter(user=user, file_title__in=titles).count()
        if already == 3:
            self.stdout.write("  Sample datasets already seeded, skipping.")
            return

        # ── Dataset 1: Employee Records (~95 score) ───────────────────────────
        # 100 rows — rows 96-100 have empty email → 5 rows fail null_check
        # Union of failed rows = 5 → score = 95
        self._build_dataset(
            user=user,
            file_title="Employee Records",
            description=(
                "Clean HR dataset with 100 employee rows. "
                "5 rows have a missing email address. "
                "Expected quality score: ~95."
            ),
            filename="employee_records.csv",
            csv_content=self._employee_csv(),
            rules=[
                {
                    "column_name": "email",
                    "rule_type": "null_check",
                    "rule_config": {},
                },
                {
                    "column_name": "name",
                    "rule_type": "null_check",
                    "rule_config": {},
                },
                {
                    "column_name": "age",
                    "rule_type": "type_check",
                    "rule_config": {"expected_type": "integer"},
                },
                {
                    "column_name": "age",
                    "rule_type": "range_check",
                    "rule_config": {"min": 18, "max": 65},
                },
            ],
            # Scores for days -6 through -1 (today is produced by the real run)
            history_scores=[88, 90, 91, 92, 93, 94],
        )

        # ── Dataset 2: Sales Orders (~40 score) ───────────────────────────────
        # 100 rows:
        #   Rows  1-30: empty customer_email → fail null_check
        #   Rows 31-50: price = "N/A"        → fail type_check (float)
        #   Rows 51-60: quantity = 9999      → fail range_check (1-1000)
        # Union of failed rows = 60 → score = 40
        self._build_dataset(
            user=user,
            file_title="Sales Orders",
            description=(
                "Messy sales dataset with 100 order rows. "
                "30 rows missing customer email, 20 rows have bad price values, "
                "10 rows have out-of-range quantities. "
                "Expected quality score: ~40."
            ),
            filename="sales_orders.csv",
            csv_content=self._sales_csv(),
            rules=[
                {
                    "column_name": "customer_email",
                    "rule_type": "null_check",
                    "rule_config": {},
                },
                {
                    "column_name": "price",
                    "rule_type": "type_check",
                    "rule_config": {"expected_type": "float"},
                },
                {
                    "column_name": "quantity",
                    "rule_type": "range_check",
                    "rule_config": {"min": 1, "max": 1000},
                },
            ],
            history_scores=[25, 28, 32, 35, 37, 39],
        )

        # ── Dataset 3: Customer Records (~70 score) ───────────────────────────
        # 100 rows:
        #   Rows  1-10: empty name       → fail null_check
        #   Rows 11-25: age = "unknown"  → fail type_check (integer)
        #   Rows 26-30: score = 150      → fail range_check (0-100)
        # Union of failed rows = 30 → score = 70
        self._build_dataset(
            user=user,
            file_title="Customer Records",
            description=(
                "Mixed-quality customer dataset with 100 rows. "
                "10 rows missing name, 15 rows have invalid age, "
                "5 rows have out-of-range scores. "
                "Expected quality score: ~70."
            ),
            filename="customer_records.csv",
            csv_content=self._customer_csv(),
            rules=[
                {
                    "column_name": "name",
                    "rule_type": "null_check",
                    "rule_config": {},
                },
                {
                    "column_name": "age",
                    "rule_type": "type_check",
                    "rule_config": {"expected_type": "integer"},
                },
                {
                    "column_name": "score",
                    "rule_type": "range_check",
                    "rule_config": {"min": 0, "max": 100},
                },
            ],
            history_scores=[55, 58, 61, 65, 67, 69],
        )

    # ── Core builder ──────────────────────────────────────────────────────────

    def _build_dataset(
        self,
        user,
        file_title: str,
        description: str,
        filename: str,
        csv_content: str,
        rules: list,
        history_scores: list,
    ) -> None:
        """
        Write CSV → Dataset → ValidationRules → QualityReport → TrendMetrics.

        history_scores: list of 6 ints [oldest … most_recent_yesterday].
        Today's score comes from the real engine run.
        """
        from datasets.models import Dataset
        from datasets.services.file_service import FileUploadService
        from checks.services.scoring_service import QualityScoreCalculator
        from checks.services.validation_engine import ValidationEngine
        from reports.models import QualityReport, RuleFinding, TrendMetric
        from rules.models import ValidationRule

        # 1. Write CSV to MEDIA_ROOT/uploads/<user_id>/
        upload_dir = Path(settings.MEDIA_ROOT) / "uploads" / str(user.id)
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / filename
        file_path.write_text(csv_content, encoding="utf-8")

        # 2. Parse into DataFrame to get row_count and column list
        service = FileUploadService()
        df = service._parse(str(file_path), "csv")

        # 3. Create Dataset record
        dataset = Dataset.objects.create(
            user=user,
            file_name=filename,
            file_type="csv",
            file_path=str(file_path),
            file_title=file_title,
            description=description,
            row_count=len(df),
            columns=list(df.columns),
        )

        # 4. Create ValidationRules (idempotent via get_or_create)
        rule_objs = []
        for r in rules:
            rule_obj, _ = ValidationRule.objects.get_or_create(
                dataset=dataset,
                column_name=r["column_name"],
                rule_type=r["rule_type"],
                defaults={"rule_config": r["rule_config"]},
            )
            rule_objs.append(rule_obj)

        # 5. Run validation engine against the DataFrame
        engine = ValidationEngine(df)
        results, failed_union = engine.run(rule_objs)

        # 6. Compute quality score
        calculator = QualityScoreCalculator()
        score = calculator.calculate(total_rows=len(df), failed_union=failed_union)

        # 7. Save today's QualityReport
        report = QualityReport.objects.create(
            dataset=dataset,
            status=QualityReport.status_from_score(score.overall_score),
            overall_score=score.overall_score,
            total_rows_passed=score.total_rows_passed,
            total_rows_failed=score.total_rows_failed,
        )

        # 8. Save RuleFinding per rule
        RuleFinding.objects.bulk_create(
            [
                RuleFinding(
                    quality_report=report,
                    rule_id=result.rule_id,
                    rows_checked=result.rows_checked,
                    rows_failed=result.rows_failed,
                    failure_percentage=result.failure_percentage,
                    error_details=result.error_details,
                )
                for result in results
            ]
        )

        # 9. Upsert today's TrendMetric
        today = timezone.now().date()
        TrendMetric.objects.update_or_create(
            dataset=dataset,
            snapshot_date=today,
            defaults={"aggregated_score": score.overall_score},
        )

        # 10. Seed 6 historical TrendMetric entries (day -6 through day -1)
        #     history_scores is ordered oldest → most recent
        for i, hist_score in enumerate(history_scores):
            days_ago = len(history_scores) - i  # 6, 5, 4, 3, 2, 1
            past_date = today - timedelta(days=days_ago)
            TrendMetric.objects.update_or_create(
                dataset=dataset,
                snapshot_date=past_date,
                defaults={"aggregated_score": hist_score},
            )

        self.stdout.write(
            f"  Created '{file_title}' | "
            f"{len(df)} rows | score={score.overall_score} | "
            f"{len(rule_objs)} rules | 7 trend points"
        )

    # ── CSV generators ────────────────────────────────────────────────────────

    def _employee_csv(self) -> str:
        """
        100 rows of HR data.
        Rows 1-95:  all valid.
        Rows 96-100: empty email → fail null_check(email) → 5 rows fail → score=95.
        """
        departments = [
            "Engineering",
            "Sales",
            "Marketing",
            "Finance",
            "HR",
            "Operations",
        ]
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "name", "email", "age", "department", "salary"])

        for i in range(1, 101):
            email = "" if i > 95 else f"employee{i}@company.com"
            writer.writerow(
                [
                    i,
                    f"Employee {i}",
                    email,
                    22 + (i % 43),  # ages 22–64
                    departments[i % len(departments)],
                    40000 + (i * 350),
                ]
            )

        return output.getvalue()

    def _sales_csv(self) -> str:
        """
        100 rows of sales order data.
        Rows  1-30: empty customer_email → fail null_check(customer_email)
        Rows 31-50: price = 'N/A'        → fail type_check(price, float)
        Rows 51-60: quantity = 9999      → fail range_check(quantity, 1-1000)
        Union = rows 1-60 → 60 rows fail → score = 40.
        """
        products = [
            "Widget A",
            "Widget B",
            "Gadget X",
            "Device Pro",
            "Tool Kit",
            "Module Z",
        ]
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["order_id", "product", "price", "quantity", "customer_email"])

        for i in range(1, 101):
            product = products[i % len(products)]
            normal_price = round(9.99 + (i * 1.5), 2)
            normal_qty = 1 + (i % 49)  # 1–49
            normal_email = f"customer{i}@shop.com"

            if i <= 30:
                writer.writerow([i, product, normal_price, normal_qty, ""])
            elif i <= 50:
                writer.writerow([i, product, "N/A", normal_qty, normal_email])
            elif i <= 60:
                writer.writerow([i, product, normal_price, 9999, normal_email])
            else:
                writer.writerow([i, product, normal_price, normal_qty, normal_email])

        return output.getvalue()

    def _customer_csv(self) -> str:
        """
        100 rows of customer data.
        Rows  1-10: empty name       → fail null_check(name)
        Rows 11-25: age = 'unknown'  → fail type_check(age, integer)
        Rows 26-30: score = 150      → fail range_check(score, 0-100)
        Union = rows 1-30 → 30 rows fail → score = 70.
        """
        cities = [
            "Kigali",
            "Nairobi",
            "Accra",
            "Lagos",
            "Kampala",
            "Dar es Salaam",
        ]
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["customer_id", "name", "age", "city", "score"])

        for i in range(1, 101):
            city = cities[i % len(cities)]
            normal_age = 20 + (i % 45)  # 20–64
            normal_score = i % 100  # 0–99

            if i <= 10:
                writer.writerow([i, "", normal_age, city, normal_score])
            elif i <= 25:
                writer.writerow([i, f"Customer {i}", "unknown", city, normal_score])
            elif i <= 30:
                writer.writerow([i, f"Customer {i}", normal_age, city, 150])
            else:
                writer.writerow([i, f"Customer {i}", normal_age, city, normal_score])

        return output.getvalue()
