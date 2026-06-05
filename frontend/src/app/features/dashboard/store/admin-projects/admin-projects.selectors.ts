import { createFeatureSelector, createSelector } from '@ngrx/store';
import { AdminProjectsState } from './admin-projects.reducer';

const selectState = createFeatureSelector<AdminProjectsState>('adminProjects');

export const selectAdminDatasets = createSelector(selectState, (s) => s.datasets);
export const selectAdminProjectsTotal = createSelector(selectState, (s) => s.total);
export const selectAdminProjectsLoading = createSelector(selectState, (s) => s.loading);
export const selectAdminProjectsError = createSelector(selectState, (s) => s.error);
