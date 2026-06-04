import { createFeatureSelector, createSelector } from '@ngrx/store';
import { ProjectDetailState } from './project-detail.reducer';

const selectProjectDetailState = createFeatureSelector<ProjectDetailState>('projectDetail');

export const selectProjectDetailDataset = createSelector(
  selectProjectDetailState,
  (state) => state.dataset,
);
export const selectProjectDetailLoading = createSelector(
  selectProjectDetailState,
  (state) => state.loading,
);
export const selectProjectDetailError = createSelector(
  selectProjectDetailState,
  (state) => state.error,
);
