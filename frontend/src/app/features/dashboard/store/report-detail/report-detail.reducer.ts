import { createReducer, on } from '@ngrx/store';
import { ReportDetail } from '../../models/report-detail.model';
import * as ReportDetailActions from './report-detail.actions';

export interface ReportDetailState {
  report: ReportDetail | null;
  loading: boolean;
  error: string | null;
}

const initialState: ReportDetailState = {
  report: null,
  loading: false,
  error: null,
};

export const reportDetailReducer = createReducer(
  initialState,
  on(ReportDetailActions.loadReportDetail, (state) => ({
    ...state,
    loading: true,
    error: null,
  })),
  on(ReportDetailActions.loadReportDetailSuccess, (state, { report }) => ({
    ...state,
    report,
    loading: false,
  })),
  on(ReportDetailActions.loadReportDetailFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error,
  })),
  on(ReportDetailActions.clearReportDetail, () => initialState),
);
