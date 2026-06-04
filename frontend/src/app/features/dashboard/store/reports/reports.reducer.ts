import { createReducer, on } from '@ngrx/store';
import { EntityState, EntityAdapter, createEntityAdapter } from '@ngrx/entity';
import { Report, ReportsSummary } from '../../models/report.model';
import * as ReportsActions from './reports.actions';

export interface ReportsState extends EntityState<Report> {
  loading: boolean;
  error: string | null;
  summary: ReportsSummary | null;
}

export const reportAdapter: EntityAdapter<Report> = createEntityAdapter<Report>();

export const initialState: ReportsState = reportAdapter.getInitialState({
  loading: false,
  error: null,
  summary: null,
});

export const reportsReducer = createReducer(
  initialState,
  on(ReportsActions.loadReports, (state) => ({ ...state, loading: true, error: null })),
  on(ReportsActions.loadReportsSuccess, (state, { reports, summary }) =>
    reportAdapter.setAll(reports, { ...state, loading: false, summary }),
  ),
  on(ReportsActions.loadReportsFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error,
  })),
  on(ReportsActions.clearReports, () => initialState),
);
