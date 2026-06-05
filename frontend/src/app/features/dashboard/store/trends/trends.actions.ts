import { createAction, props } from '@ngrx/store';
import { TrendPoint } from '../../models/trend.model';

export const loadTrends = createAction(
  '[Trends] Load Trends',
  props<{ datasetId: string }>(),
);
export const loadTrendsSuccess = createAction(
  '[Trends] Load Trends Success',
  props<{ data: TrendPoint[] }>(),
);
export const loadTrendsFailure = createAction(
  '[Trends] Load Trends Failure',
  props<{ error: string }>(),
);
export const clearTrends = createAction('[Trends] Clear');
