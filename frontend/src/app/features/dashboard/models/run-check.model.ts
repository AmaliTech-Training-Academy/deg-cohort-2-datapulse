export interface RunCheckFinding {
  id: string;
  rule: string;
  rule_type: string;
  column_name: string;
  rows_checked: number;
  rows_failed: number;
  failure_percentage: number;
  error_details: string | null;
}

export interface RunCheckResponse {
  id: string;
  dataset: string;
  dataset_file_title: string;
  dataset_file_version: number;
  status: string;
  overall_score: number;
  total_rows_passed: number;
  total_rows_failed: number;
  error_message: string | null;
  findings: RunCheckFinding[];
  generated_at: string;
  average_score: number | null;
  rules_applied: number;
  failing_checks: number;
  passing_checks: number;
  rule_type_scores: {
    null_check: number | null;
    type_check: number | null;
    range_check: number | null;
    uniqueness_check: number | null;
  };
}
