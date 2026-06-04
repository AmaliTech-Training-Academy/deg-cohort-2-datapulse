import { createFeatureSelector, createSelector } from '@ngrx/store';
import { ProjectCreationState } from './project-creation.reducer';

const selectProjectCreationState =
  createFeatureSelector<ProjectCreationState>('projectCreation');

export const selectCurrentStep = createSelector(
  selectProjectCreationState,
  (s) => s.currentStep,
);
export const selectDatasetId = createSelector(
  selectProjectCreationState,
  (s) => s.datasetId,
);
export const selectUploadedColumns = createSelector(
  selectProjectCreationState,
  (s) => s.uploadedColumns,
);
export const selectConfirmedRules = createSelector(
  selectProjectCreationState,
  (s) => s.confirmedRules,
);

export const selectUploadLoading = createSelector(
  selectProjectCreationState,
  (s) => s.upload.loading,
);
export const selectUploadError = createSelector(
  selectProjectCreationState,
  (s) => s.upload.error,
);

export const selectRulesLoading = createSelector(
  selectProjectCreationState,
  (s) => s.rules.loading,
);
export const selectRulesError = createSelector(
  selectProjectCreationState,
  (s) => s.rules.error,
);

export const selectRunCheckLoading = createSelector(
  selectProjectCreationState,
  (s) => s.runCheck.loading,
);
export const selectRunCheckError = createSelector(
  selectProjectCreationState,
  (s) => s.runCheck.error,
);
export const selectRunCheckScore = createSelector(
  selectProjectCreationState,
  (s) => s.runCheck.score,
);
