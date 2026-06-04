// ── Raw API type (from backend TrendMetricSerializer) ────────────────────────

export interface ApiTrendPoint {
  readonly snapshot_date: string;    // ISO 8601 date (YYYY-MM-DD)
  readonly aggregated_score: number; // 0-100
}

// ── Frontend view model ───────────────────────────────────────────────────────

export interface TrendPoint {
  readonly snapshotDate: string;
  readonly aggregatedScore: number;
}

// ── Mapping ───────────────────────────────────────────────────────────────────

export function mapTrendPoint(point: ApiTrendPoint): TrendPoint {
  return {
    snapshotDate: point.snapshot_date,
    aggregatedScore: point.aggregated_score,
  };
}

export function mapTrendPoints(points: ApiTrendPoint[]): TrendPoint[] {
  return points.map(mapTrendPoint);
}
