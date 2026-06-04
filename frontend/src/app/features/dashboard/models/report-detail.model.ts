import { ProjectStatus } from './project.model';

// ── Raw API types (from backend ReportDetailSerializer / RuleFindingSerializer) ──

export interface ApiRuleFinding {
  readonly id: string;
  readonly rule: string;
  readonly rule_type: string;
  readonly column_name: string;
  readonly rows_checked: number;
  readonly rows_failed: number;
  readonly failure_percentage: number;
  readonly error_details: object[];
}

export interface ApiReportDetail {
  readonly id: string;
  readonly dataset: string;
  readonly dataset_file_title: string;
  readonly dataset_file_version: number;
  readonly dataset_file_name: string;
  readonly status: ProjectStatus;
  readonly overall_score: number | null;
  readonly total_rows_passed: number | null;
  readonly total_rows_failed: number | null;
  readonly error_message: string;
  readonly generated_at: string;
  readonly rules_applied: number;
  readonly rows_analyzed: number | null;
  readonly rule_type_scores: {
    readonly null_check: number | null;
    readonly type_check: number | null;
    readonly range_check: number | null;
    readonly uniqueness_check: number | null;
  };
  readonly findings: ApiRuleFinding[];
}

// ── Frontend view models ──────────────────────────────────────────────────────

export interface RuleFinding {
  readonly id: string;
  readonly ruleId: string;
  readonly ruleType: string;
  readonly columnName: string;
  readonly rowsChecked: number;
  readonly rowsFailed: number;
  readonly failurePercentage: number;
}

export interface ReportDetail {
  readonly id: string;
  readonly datasetId: string;
  readonly datasetFileTitle: string;
  readonly datasetFileVersion: number;
  readonly datasetFileName: string;
  readonly status: ProjectStatus;
  readonly overallScore: number | null;
  readonly totalRowsPassed: number | null;
  readonly totalRowsFailed: number | null;
  readonly errorMessage: string;
  readonly generatedAt: string;
  readonly rulesApplied: number;
  readonly rowsAnalyzed: number | null;
  readonly categoryScores: {
    nullChecks: number | null;
    typeChecks: number | null;
    rangeChecks: number | null;
    uniqueness: number | null;
  };
  readonly findings: RuleFinding[];
}

// ── Mapping ───────────────────────────────────────────────────────────────────

export function mapReportDetail(api: ApiReportDetail): ReportDetail {
  return {
    id: api.id,
    datasetId: api.dataset,
    datasetFileTitle: api.dataset_file_title,
    datasetFileVersion: api.dataset_file_version,
    datasetFileName: api.dataset_file_name,
    status: api.status,
    overallScore: api.overall_score,
    totalRowsPassed: api.total_rows_passed,
    totalRowsFailed: api.total_rows_failed,
    errorMessage: api.error_message,
    generatedAt: api.generated_at,
    rulesApplied: api.rules_applied,
    rowsAnalyzed: api.rows_analyzed,
    categoryScores: {
      nullChecks: api.rule_type_scores.null_check,
      typeChecks: api.rule_type_scores.type_check,
      rangeChecks: api.rule_type_scores.range_check,
      uniqueness: api.rule_type_scores.uniqueness_check,
    },
    findings: api.findings.map((f) => ({
      id: f.id,
      ruleId: f.rule,
      ruleType: f.rule_type,
      columnName: f.column_name,
      rowsChecked: f.rows_checked,
      rowsFailed: f.rows_failed,
      failurePercentage: f.failure_percentage,
    })),
  };
}
