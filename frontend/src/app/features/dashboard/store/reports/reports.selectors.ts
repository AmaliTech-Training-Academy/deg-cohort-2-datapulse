import { createFeatureSelector, createSelector } from '@ngrx/store';
import { ReportsState, reportAdapter } from './reports.reducer';

const selectReportsState = createFeatureSelector<ReportsState>('reports');

const { selectAll } = reportAdapter.getSelectors();

export const selectAllReports = createSelector(selectReportsState, selectAll);
export const selectReportsLoading = createSelector(selectReportsState, (state) => state.loading);
export const selectReportsError = createSelector(selectReportsState, (state) => state.error);
export const selectReportsSummary = createSelector(selectReportsState, (state) => state.summary);
