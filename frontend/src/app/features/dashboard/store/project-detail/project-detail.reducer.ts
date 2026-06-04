import { createReducer, on } from '@ngrx/store';
import { ApiDataset } from '../../models/project.model';
import * as ProjectDetailActions from './project-detail.actions';

export interface ProjectDetailState {
  dataset: ApiDataset | null;
  loading: boolean;
  error: string | null;
  uploadVersionLoading: boolean;
  uploadVersionError: string | null;
}

const initialState: ProjectDetailState = {
  dataset: null,
  loading: false,
  error: null,
  uploadVersionLoading: false,
  uploadVersionError: null,
};

export const projectDetailReducer = createReducer(
  initialState,
  on(ProjectDetailActions.loadProjectDetail, (state) => ({
    ...state,
    loading: true,
    error: null,
  })),
  on(ProjectDetailActions.loadProjectDetailSuccess, (state, { dataset }) => ({
    ...state,
    dataset,
    loading: false,
  })),
  on(ProjectDetailActions.loadProjectDetailFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error,
  })),
  on(ProjectDetailActions.clearProjectDetail, () => initialState),

  on(ProjectDetailActions.uploadVersion, (state) => ({
    ...state,
    uploadVersionLoading: true,
    uploadVersionError: null,
  })),
  on(ProjectDetailActions.uploadVersionSuccess, (state) => ({
    ...state,
    uploadVersionLoading: false,
  })),
  on(ProjectDetailActions.uploadVersionFailure, (state, { error }) => ({
    ...state,
    uploadVersionLoading: false,
    uploadVersionError: error,
  })),
);
