import { createFeatureSelector, createSelector } from '@ngrx/store';
import { ProjectsState, projectAdapter } from './projects.reducer';

const selectProjectsState = createFeatureSelector<ProjectsState>('projects');

const { selectAll, selectEntities } = projectAdapter.getSelectors();

export const selectAllProjects = createSelector(selectProjectsState, selectAll);
export const selectProjectEntities = createSelector(selectProjectsState, selectEntities);
export const selectProjectsLoading = createSelector(
  selectProjectsState,
  (state) => state.loading,
);
export const selectProjectsError = createSelector(selectProjectsState, (state) => state.error);
