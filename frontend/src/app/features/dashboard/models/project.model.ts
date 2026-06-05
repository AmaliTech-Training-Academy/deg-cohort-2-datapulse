export type ProjectStatus = 'healthy' | 'warning' | 'failing';

// ── Raw API types (from backend serializers) ─────────────────────────────────

export interface ApiDataset {
  readonly id: string;
  readonly file_name: string;
  readonly file_type: 'csv' | 'json';
  readonly file_title: string;
  readonly description: string;
  readonly row_count: number | null;
  readonly columns: string[];
  readonly file_version: number;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface ApiLatestReport {
  readonly id: string;
  readonly dataset_file_title: string;
  readonly dataset_file_version: number;
  readonly status: ProjectStatus;
  readonly overall_score: number;
  readonly total_rows_passed: number;
  readonly total_rows_failed: number;
  readonly generated_at: string;
}

export interface ApiDashboardItem {
  readonly dataset: ApiDataset;
  readonly status: ProjectStatus | null;
  readonly latest_score: number | null;
  readonly latest_score_date: string | null;
  readonly latest_report: ApiLatestReport | null;
}

export interface ApiDashboardResponse {
  readonly total_datasets: number;
  readonly total_active_datasets: number;
  readonly count: number;
  readonly next: string | null;
  readonly previous: string | null;
  readonly results: ApiDashboardItem[];
}

// ── Frontend view model (backend "dataset" renamed to "project") ──────────────

export interface Project {
  readonly id: string;
  readonly name: string;             // ← file_title (or file_name fallback)
  readonly description: string;
  readonly fileType: 'csv' | 'json';
  readonly fileVersion: number;
  readonly rowCount: number | null;
  readonly columns: string[];
  readonly status: ProjectStatus;
  readonly avgScore: number;         // ← latest_score (0 when null)
  readonly lastRunAt: string;        // ← latest_score_date or created_at
  readonly datasetCount: number;     // ← file_version (version count proxy)
  readonly iconKey: string;          // derived from fileType
  readonly latestReportId: string | null;
  readonly createdAt: string;
}

// ── Mapping functions ────────────────────────────────────────────────────────

function deriveStatus(score: number): ProjectStatus {
  if (score >= 85) return 'healthy';
  if (score >= 70) return 'warning';
  return 'failing';
}

export function mapDashboardItem(item: ApiDashboardItem): Project {
  const { dataset, status, latest_score, latest_score_date, latest_report } = item;
  const avgScore = Math.round(latest_score ?? 0);
  return {
    id: dataset.id,
    name: dataset.file_title || dataset.file_name,
    description: dataset.description,
    fileType: dataset.file_type,
    fileVersion: dataset.file_version,
    rowCount: dataset.row_count,
    columns: dataset.columns,
    status: status ?? deriveStatus(avgScore),
    avgScore,
    lastRunAt: latest_score_date ?? dataset.created_at,
    datasetCount: dataset.file_version,
    iconKey: dataset.file_type === 'json' ? 'layers' : 'database',
    latestReportId: latest_report?.id ?? null,
    createdAt: dataset.created_at,
  };
}

export function mapDashboardItems(items: ApiDashboardItem[]): Project[] {
  return items.map(mapDashboardItem);
}
