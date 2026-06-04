import { createAction, props } from '@ngrx/store';
import { Report, ReportsSummary } from '../../models/report.model';

export const loadReports = createAction(
  '[Reports] Load Reports',
  props<{ datasetId: string }>(),
);
export const loadReportsSuccess = createAction(
  '[Reports] Load Reports Success',
  props<{ reports: Report[]; summary: ReportsSummary }>(),
);
export const loadReportsFailure = createAction(
  '[Reports] Load Reports Failure',
  props<{ error: string }>(),
);
export const clearReports = createAction('[Reports] Clear');
