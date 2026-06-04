import { createAction, props } from '@ngrx/store';
import { ReportDetail } from '../../models/report-detail.model';

export const loadReportDetail = createAction(
  '[Report Detail] Load Report Detail',
  props<{ reportId: string }>(),
);
export const loadReportDetailSuccess = createAction(
  '[Report Detail] Load Report Detail Success',
  props<{ report: ReportDetail }>(),
);
export const loadReportDetailFailure = createAction(
  '[Report Detail] Load Report Detail Failure',
  props<{ error: string }>(),
);
export const clearReportDetail = createAction('[Report Detail] Clear');
