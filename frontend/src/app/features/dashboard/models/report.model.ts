import { ProjectStatus } from './project.model';

// ── Raw API types (from backend ReportListItemSerializer / ReportListSerializer) ──

export interface ApiReportListItem {
  readonly id: string;
  readonly dataset: string;
  readonly dataset_file_title: string;
  readonly dataset_file_version: number;
  readonly status: ProjectStatus;
  readonly overall_score: number | null;
  readonly total_rows_passed: number | null;
  readonly total_rows_failed: number | null;
  readonly file_rows_analyzed: number | null;
  readonly error_message: string;
  readonly generated_at: string;
}

export interface ApiReportsListResponse {
  readonly total_active_reports: number;
  readonly total_active_rules: number;
  readonly last_rule_check_time: string | null;
  readonly average_score: number | null;
  readonly total_passing_rows: number;
  readonly total_passing_columns: number;
  readonly count: number;
  readonly next: string | null;
  readonly previous: string | null;
  readonly results: ApiReportListItem[];
}

// ── Frontend view models ──────────────────────────────────────────────────────

export interface Report {
  readonly id: string;
  readonly datasetId: string;
  readonly datasetFileTitle: string;
  readonly datasetFileVersion: number;
  readonly status: ProjectStatus;
  readonly overallScore: number | null;
  readonly totalRowsPassed: number | null;
  readonly totalRowsFailed: number | null;
  readonly fileRowsAnalyzed: number | null;
  readonly errorMessage: string;
  readonly generatedAt: string;
}

export interface ReportsSummary {
  readonly totalActiveReports: number;
  readonly totalActiveRules: number;
  readonly lastRuleCheckTime: string | null;
  readonly averageScore: number | null;
  readonly totalPassingRows: number;
  readonly totalPassingColumns: number;
}

// ── Mapping functions ────────────────────────────────────────────────────────

export function mapReportListItem(item: ApiReportListItem): Report {
  return {
    id: item.id,
    datasetId: item.dataset,
    datasetFileTitle: item.dataset_file_title,
    datasetFileVersion: item.dataset_file_version,
    status: item.status,
    overallScore: item.overall_score,
    totalRowsPassed: item.total_rows_passed,
    totalRowsFailed: item.total_rows_failed,
    fileRowsAnalyzed: item.file_rows_analyzed,
    errorMessage: item.error_message,
    generatedAt: item.generated_at,
  };
}

export function mapReportsSummary(response: ApiReportsListResponse): ReportsSummary {
  return {
    totalActiveReports: response.total_active_reports,
    totalActiveRules: response.total_active_rules,
    lastRuleCheckTime: response.last_rule_check_time,
    averageScore: response.average_score,
    totalPassingRows: response.total_passing_rows,
    totalPassingColumns: response.total_passing_columns,
  };
}
