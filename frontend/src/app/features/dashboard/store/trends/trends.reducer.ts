import { createReducer, on } from '@ngrx/store';
import { TrendPoint } from '../../models/trend.model';
import * as TrendsActions from './trends.actions';

export interface TrendsState {
  data: TrendPoint[];
  loading: boolean;
  error: string | null;
}

const initialState: TrendsState = {
  data: [],
  loading: false,
  error: null,
};

export const trendsReducer = createReducer(
  initialState,
  on(TrendsActions.loadTrends, (state) => ({ ...state, loading: true, error: null })),
  on(TrendsActions.loadTrendsSuccess, (state, { data }) => ({ ...state, data, loading: false })),
  on(TrendsActions.loadTrendsFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error,
  })),
  on(TrendsActions.clearTrends, () => initialState),
);
