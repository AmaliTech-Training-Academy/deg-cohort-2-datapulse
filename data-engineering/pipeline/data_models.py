# """SQLAlchemy ORM for analytics tables."""

# from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date
# from sqlalchemy import ForeignKey, create_engine
# from sqlalchemy.dialects.postgresql import UUID
# from sqlalchemy.orm import declarative_base

# AnalyticsBase = declarative_base()


# class DimDataset(AnalyticsBase):
#     __tablename__ = "dim_datasets"
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     source_id = Column(UUID(as_uuid=True), unique=True, nullable=False)  # maps to datasets.id (uuid)
#     name = Column(String(255))       # maps to datasets.file_name
#     file_type = Column(String(10))
#     row_count = Column(Integer)
#     uploaded_at = Column(DateTime)   # maps to datasets.created_at


# class DimRule(AnalyticsBase):
#     __tablename__ = "dim_rules"
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     source_id = Column(UUID(as_uuid=True), unique=True, nullable=False)  # maps to validation_rules.id (uuid)
#     name = Column(String(255))       # maps to validation_rules.column_name
#     field_name = Column(String(255)) # maps to validation_rules.column_name
#     rule_type = Column(String(20))   # maps to validation_rules.rule_type
#     severity = Column(String(10))    # derived from rule_config json


# class DimDate(AnalyticsBase):
#     __tablename__ = "dim_date"
#     date_key = Column(Integer, primary_key=True)
#     full_date = Column(Date)
#     day_of_week = Column(Integer)
#     month = Column(Integer)
#     year = Column(Integer)


# class FactQualityCheck(AnalyticsBase):
#     __tablename__ = "fact_quality_checks"
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     dataset_id = Column(Integer, ForeignKey("dim_datasets.id"))
#     rule_id = Column(Integer, ForeignKey("dim_rules.id"))
#     rule_type = Column(String(20))   # from validation_rules.rule_type
#     passed = Column(Boolean)         # derived: failure_percentage == 0
#     failed_rows = Column(Integer)    # from rule_findings.rows_failed
#     total_rows = Column(Integer)     # from rule_findings.rows_checked
#     score = Column(Float)            # derived: 1 - (rows_failed / rows_checked)
#     severity = Column(String(10))    # from dim_rules.severity
#     checked_at = Column(DateTime)    # from quality_reports.generated_at

"""SQLAlchemy ORM for analytics tables."""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

AnalyticsBase = declarative_base()


class DimDataset(AnalyticsBase):
    __tablename__ = "dim_datasets"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    source_id   = Column(UUID(as_uuid=True), unique=True, nullable=False)  # datasets.id
    name        = Column(String(255))       # datasets.file_name
    file_type   = Column(String(10))
    row_count   = Column(Integer)
    uploaded_at = Column(DateTime)          # datasets.created_at


class DimRule(AnalyticsBase):
    __tablename__ = "dim_rules"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    source_id  = Column(UUID(as_uuid=True), unique=True, nullable=False)  # validation_rules.id
    name       = Column(String(255))        # validation_rules.column_name
    field_name = Column(String(255))        # validation_rules.column_name
    rule_type  = Column(String(20))         # validation_rules.rule_type
    severity   = Column(String(10))         # derived from rule_config json


class DimDate(AnalyticsBase):
    __tablename__ = "dim_date"

    date_key    = Column(Integer, primary_key=True)   # format: YYYYMMDD
    full_date   = Column(Date)
    day_of_week = Column(Integer)                     # 0=Monday … 6=Sunday
    month       = Column(Integer)
    year        = Column(Integer)


class FactQualityCheck(AnalyticsBase):
    __tablename__ = "fact_quality_checks"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id  = Column(Integer, ForeignKey("dim_datasets.id"))
    rule_id     = Column(Integer, ForeignKey("dim_rules.id"))
    rule_type   = Column(String(20))        # validation_rules.rule_type (denormalised)
    passed      = Column(Boolean)           # derived: failure_percentage == 0
    failed_rows = Column(Integer)           # rule_findings.rows_failed
    total_rows  = Column(Integer)           # rule_findings.rows_checked
    score       = Column(Float)             # derived: 1 - (rows_failed / rows_checked)
    severity    = Column(String(10))        # from dim_rules.severity
    checked_at  = Column(DateTime(timezone=True))  # quality_reports.generated_at


class FactTrendMetric(AnalyticsBase):
    __tablename__ = "fact_trend_metrics"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id       = Column(Integer, ForeignKey("dim_datasets.id"), nullable=False)
    source_id        = Column(UUID(as_uuid=True), unique=True, nullable=False)  # trend_metrics.id
    snapshot_date    = Column(Date, nullable=False)    # trend_metrics.snapshot_date
    aggregated_score = Column(Integer)                 # trend_metrics.aggregated_score