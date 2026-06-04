import { createReducer, on } from '@ngrx/store';
import { SuggestedRule } from '../../../../shared/models/dashboard.models';
import * as ProjectCreationActions from './project-creation.actions';

export interface ProjectCreationState {
  currentStep: 1 | 2 | 3;
  datasetId: string | null;
  uploadedColumns: string[];
  confirmedRules: SuggestedRule[];
  upload: { loading: boolean; error: string | null };
  rules: { loading: boolean; error: string | null };
  runCheck: { loading: boolean; error: string | null; score: number | null };
}

export const initialState: ProjectCreationState = {
  currentStep: 1,
  datasetId: null,
  uploadedColumns: [],
  confirmedRules: [],
  upload: { loading: false, error: null },
  rules: { loading: false, error: null },
  runCheck: { loading: false, error: null, score: null },
};

export const projectCreationReducer = createReducer(
  initialState,
  on(ProjectCreationActions.uploadDataset, (state) => ({
    ...state,
    upload: { loading: true, error: null },
  })),
  on(ProjectCreationActions.uploadDatasetSuccess, (state, { datasetId, columns }) => ({
    ...state,
    currentStep: 2 as const,
    datasetId,
    uploadedColumns: columns,
    upload: { loading: false, error: null },
  })),
  on(ProjectCreationActions.uploadDatasetFailure, (state, { error }) => ({
    ...state,
    upload: { loading: false, error },
  })),
  on(ProjectCreationActions.saveRules, (state, { rules }) => ({
    ...state,
    confirmedRules: rules.filter((r) => r.enabled),
    rules: { loading: true, error: null },
  })),
  on(ProjectCreationActions.saveRulesSuccess, (state) => ({
    ...state,
    currentStep: 3 as const,
    rules: { loading: false, error: null },
  })),
  on(ProjectCreationActions.saveRulesFailure, (state, { error }) => ({
    ...state,
    rules: { loading: false, error },
  })),
  on(ProjectCreationActions.runChecks, (state) => ({
    ...state,
    runCheck: { loading: true, error: null, score: null },
  })),
  on(ProjectCreationActions.runChecksSuccess, (state, { score }) => ({
    ...state,
    runCheck: { loading: false, error: null, score },
  })),
  on(ProjectCreationActions.runChecksFailure, (state, { error }) => ({
    ...state,
    runCheck: { loading: false, error, score: null },
  })),
  on(ProjectCreationActions.goBackToUpload, (state) => ({
    ...state,
    currentStep: 1 as const,
    upload: { loading: false, error: null },
  })),
  on(ProjectCreationActions.goBackToRules, (state) => ({
    ...state,
    currentStep: 2 as const,
    runCheck: { loading: false, error: null, score: null },
  })),
  on(ProjectCreationActions.resetProjectCreation, () => initialState),
);
