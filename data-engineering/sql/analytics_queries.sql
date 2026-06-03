-- DataPulse Analytics Queries`
-- These queries answer business questions about data quality trends.


-- Query 1: Overall quality score per dataset 
-- Shows the latest quality score for each dataset
-- Used by: dashboard overview, dataset comparison table

SELECT
    d.name                          AS dataset_name,
    d.file_type,
    d.row_count,
    ROUND(AVG(f.score)::NUMERIC, 2) AS avg_score,
    MAX(f.checked_at)               AS last_checked,
    COUNT(f.id)                     AS total_checks
FROM fact_quality_checks f
JOIN dim_datasets d ON f.dataset_id = d.id
GROUP BY d.id, d.name, d.file_type, d.row_count
ORDER BY avg_score DESC;


-- Query 2: Quality score over time per dataset 
-- Shows how quality changes over time for each dataset
-- Used by: trend line chart on dashboard

SELECT
    d.name                          AS dataset_name,
    dt.full_date                    AS check_date,
    ROUND(AVG(f.score)::NUMERIC, 2) AS daily_score,
    COUNT(f.id)                     AS checks_run
FROM fact_quality_checks f
JOIN dim_datasets d  ON f.dataset_id = d.id
JOIN dim_date dt     ON DATE(f.checked_at) = dt.full_date
GROUP BY d.name, dt.full_date
ORDER BY d.name, dt.full_date;


-- Query 3: Most common failing rule types
-- Shows which rule types fail most often across all datasets
-- Used by: issues by type bar chart

SELECT
    f.rule_type,
    COUNT(*)                                    AS total_checks,
    SUM(CASE WHEN f.passed = FALSE THEN 1 END)  AS total_failures,
    ROUND(
        SUM(CASE WHEN f.passed = FALSE THEN 1 END)::NUMERIC
        / COUNT(*) * 100, 2
    )                                           AS failure_rate_pct
FROM fact_quality_checks f
GROUP BY f.rule_type
ORDER BY failure_rate_pct DESC;


-- Query 4: Datasets with declining quality 
-- Finds datasets where quality score is getting worse over time
-- Used by: alerts, dashboard warnings

SELECT
    d.name                                      AS dataset_name,
    ROUND(AVG(CASE WHEN f.checked_at >= NOW() - INTERVAL '7 days'
              THEN f.score END)::NUMERIC, 2)    AS score_last_7_days,
    ROUND(AVG(CASE WHEN f.checked_at < NOW() - INTERVAL '7 days'
              THEN f.score END)::NUMERIC, 2)    AS score_before_7_days,
    ROUND(
        AVG(CASE WHEN f.checked_at >= NOW() - INTERVAL '7 days'
            THEN f.score END)::NUMERIC -
        AVG(CASE WHEN f.checked_at < NOW() - INTERVAL '7 days'
            THEN f.score END)::NUMERIC
    , 2)                                        AS score_change
FROM fact_quality_checks f
JOIN dim_datasets d ON f.dataset_id = d.id
GROUP BY d.name
HAVING
    AVG(CASE WHEN f.checked_at >= NOW() - INTERVAL '7 days'
        THEN f.score END) IS NOT NULL
ORDER BY score_change ASC;


-- Query 5: Rule performance per dataset 
-- Shows pass/fail breakdown per rule per dataset
-- Used by: detailed report view

SELECT
    d.name                                      AS dataset_name,
    r.name                                      AS rule_name,
    f.rule_type,
    COUNT(*)                                    AS times_checked,
    SUM(CASE WHEN f.passed THEN 1 ELSE 0 END)  AS times_passed,
    SUM(CASE WHEN f.passed THEN 0 ELSE 1 END)  AS times_failed,
    ROUND(AVG(f.failed_rows)::NUMERIC, 1)       AS avg_failed_rows,
    ROUND(AVG(f.score)::NUMERIC, 2)             AS avg_score
FROM fact_quality_checks f
JOIN dim_datasets d ON f.dataset_id = d.id
JOIN dim_rules r    ON f.rule_id = r.id
GROUP BY d.name, r.name, f.rule_type
ORDER BY d.name, avg_score ASC;


-- Query 6: Monthly quality summary 
-- Monthly average scores per dataset
-- Used by: monthly report, trend analysis

SELECT
    d.name                          AS dataset_name,
    dt.year,
    dt.month,
    ROUND(AVG(f.score)::NUMERIC, 2) AS monthly_avg_score,
    COUNT(f.id)                     AS total_checks,
    SUM(f.failed_rows)              AS total_failed_rows
FROM fact_quality_checks f
JOIN dim_datasets d ON f.dataset_id = d.id
JOIN dim_date dt    ON DATE(f.checked_at) = dt.full_date
GROUP BY d.name, dt.year, dt.month
ORDER BY d.name, dt.year, dt.month;


-- Query 7: Top 5 worst datasets right now 
-- Quick view of which datasets need the most attention
-- Used by: dashboard summary card

SELECT
    d.name                          AS dataset_name,
    ROUND(AVG(f.score)::NUMERIC, 2) AS avg_score,
    SUM(f.failed_rows)              AS total_failed_rows,
    MAX(f.checked_at)               AS last_checked
FROM fact_quality_checks f
JOIN dim_datasets d ON f.dataset_id = d.id
GROUP BY d.name
ORDER BY avg_score ASC
LIMIT 5;