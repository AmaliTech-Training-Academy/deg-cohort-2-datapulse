from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date
import os

from data_models import AnalyticsBase, DimDataset, DimRule, DimDate, FactQualityCheck


DB_URL = os.getenv(
    "TARGET_DB_URL",
    "postgresql://analytics_user:analytics_pass@db:5432/datapulse_analytics"
)

engine = create_engine(DB_URL)

def create_tables():
    print("Creating analytics tables...")
    AnalyticsBase.metadata.create_all(engine)
    print("Tables created successfully.")


def seed_dummy_data():
    print("Seeding sample data...")

    Session = sessionmaker(bind=engine)
    session = Session()

    # --- DimDataset ---
    dataset = DimDataset(
        source_id="00000000-0000-0000-0000-000000000001",
        name="sample_dataset.csv",
        file_type="csv",
        row_count=1000,
        uploaded_at=datetime.utcnow()
    )

    # --- DimRule ---
    rule = DimRule(
        source_id="00000000-0000-0000-0000-000000000002",
        name="no_nulls",
        field_name="age",
        rule_type="completeness",
        severity="high"
    )

    session.add(dataset)
    session.add(rule)
    session.commit()

    # --- DimDate ---
    session.add(DimDate(
        date_key=20260602,
        full_date=date.today(),
        day_of_week=date.today().weekday(),
        month=date.today().month,
        year=date.today().year
    ))

    session.commit()

    # --- Fact ---
    fact = FactQualityCheck(
        dataset_id=dataset.id,
        rule_id=rule.id,
        rule_type="completeness",
        passed=True,
        failed_rows=0,
        total_rows=1000,
        score=1.0,
        severity="high",
        checked_at=datetime.utcnow()
    )

    session.add(fact)
    session.commit()

    session.close()
    print("Dummy data inserted.")


if __name__ == "__main__":
    create_tables()
    seed_dummy_data()