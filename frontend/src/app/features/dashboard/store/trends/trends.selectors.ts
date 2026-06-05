import { createFeatureSelector, createSelector } from '@ngrx/store';
import { TrendsState } from './trends.reducer';

const selectTrendsState = createFeatureSelector<TrendsState>('trends');

export const selectTrendsData = createSelector(selectTrendsState, (state) => state.data);
export const selectTrendsLoading = createSelector(selectTrendsState, (state) => state.loading);
export const selectTrendsError = createSelector(selectTrendsState, (state) => state.error);
