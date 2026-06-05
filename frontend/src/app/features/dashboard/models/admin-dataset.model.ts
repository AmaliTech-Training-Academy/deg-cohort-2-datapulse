import { ProjectStatus } from '../../../shared/models/dashboard.models';

// ── Raw API types (from AdminDatasetResponseSerializer) ───────────────────────

export interface ApiAdminDatasetOwner {
  readonly id: string;
  readonly email: string;
  readonly first_name: string;
  readonly last_name: string;
}

export interface ApiAdminDatasetLatestReport {
  readonly overall_score: number | null;
  readonly status: ProjectStatus;
  readonly generated_at: string;
}

export interface ApiAdminDataset {
  readonly id: string;
  readonly file_name: string;
  readonly file_type: 'csv' | 'json';
  readonly file_title: string;
  readonly description: string;
  readonly row_count: number;
  readonly columns: string[];
  readonly file_version: number;
  readonly created_at: string;
  readonly updated_at: string;
  readonly user: ApiAdminDatasetOwner;
  readonly reports_count: number;
  readonly latest_report: ApiAdminDatasetLatestReport | null;
}

export interface ApiAdminDatasetsResponse {
  readonly count: number;
  readonly next: string | null;
  readonly previous: string | null;
  readonly results: ApiAdminDataset[];
}

// ── Frontend view model ───────────────────────────────────────────────────────

export interface AdminDataset {
  readonly id: string;
  readonly name: string;
  readonly fileType: 'csv' | 'json';
  readonly ownerName: string;
  readonly ownerEmail: string;
  readonly reportsCount: number;
  readonly score: number;
  readonly status: ProjectStatus;
  readonly lastRunAt: string | null;
  readonly createdAt: string;
}

// ── Query params ──────────────────────────────────────────────────────────────

export interface AdminDatasetsParams {
  search?: string;
  file_type?: 'csv' | 'json';
  created_from?: string;
  created_to?: string;
  page?: number;
  page_size?: number;
}

// ── Mapping ───────────────────────────────────────────────────────────────────

export function mapAdminDataset(raw: ApiAdminDataset): AdminDataset {
  const score = raw.latest_report?.overall_score ?? 0;
  const ownerName =
    `${raw.user.first_name} ${raw.user.last_name}`.trim() || raw.user.email;

  return {
    id: raw.id,
    name: raw.file_title || raw.file_name,
    fileType: raw.file_type,
    ownerName,
    ownerEmail: raw.user.email,
    reportsCount: raw.reports_count,
    score,
    status: raw.latest_report?.status ?? (score >= 85 ? 'healthy' : score >= 70 ? 'warning' : 'failing'),
    lastRunAt: raw.latest_report?.generated_at ?? null,
    createdAt: raw.created_at,
  };
}
