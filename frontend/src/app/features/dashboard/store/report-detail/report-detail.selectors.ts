import { createFeatureSelector, createSelector } from '@ngrx/store';
import { ReportDetailState } from './report-detail.reducer';

const selectReportDetailState = createFeatureSelector<ReportDetailState>('reportDetail');

export const selectReportDetail = createSelector(
  selectReportDetailState,
  (state) => state.report,
);
export const selectReportDetailLoading = createSelector(
  selectReportDetailState,
  (state) => state.loading,
);
export const selectReportDetailError = createSelector(
  selectReportDetailState,
  (state) => state.error,
);
