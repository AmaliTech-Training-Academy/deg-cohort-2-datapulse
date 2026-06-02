"""
checks/migrations/0002_remove_moved_models.py
────────────────────────────────────────────────────────────────────────────────
Removes QualityCheck and RuleFinding from the checks app's ORM state.
Ownership has been transferred to reports/models.py.

database_operations=[] — the DB tables are NOT dropped.
The tables (quality_reports, rule_findings) continue to exist and are now
managed by reports/migrations/0001_initial.py.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("checks", "0001_initial"),
        ("reports", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel("QualityCheck"),
                migrations.DeleteModel("RuleFinding"),
            ],
            database_operations=[],
        ),
    ]
