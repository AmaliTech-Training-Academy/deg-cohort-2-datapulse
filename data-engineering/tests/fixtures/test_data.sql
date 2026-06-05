INSERT INTO dim_datasets (source_id, name, file_type, row_count, uploaded_at) VALUES
    ('00000000-0000-0000-0000-000000000001', 'clean_data',  'csv', 100, NOW()),
    ('00000000-0000-0000-0000-000000000002', 'messy_data',  'csv', 100, NOW()),
    ('00000000-0000-0000-0000-000000000003', 'mixed_data',  'csv', 100, NOW());

INSERT INTO dim_rules (source_id, name, field_name, rule_type, severity) VALUES
    ('00000000-0000-0000-0000-000000000001', 'not_null_check', 'value', 'not_null', 'high');

INSERT INTO fact_quality_checks (dataset_id, rule_id, rule_type, passed, failed_rows, total_rows, score, severity, checked_at) VALUES
    (1, 1, 'not_null', true,  0,  100, 1.00, 'high', NOW()),
    (2, 1, 'not_null', false, 40, 100, 0.60, 'high', NOW()),
    (3, 1, 'not_null', false, 20, 100, 0.80, 'high', NOW());

INSERT INTO fact_trend_metrics (dataset_id, snapshot_date, aggregated_score) VALUES
    (1, CURRENT_DATE - 1, 95.0),
    (2, CURRENT_DATE - 1, 60.0),
    (3, CURRENT_DATE - 1, 80.0);
