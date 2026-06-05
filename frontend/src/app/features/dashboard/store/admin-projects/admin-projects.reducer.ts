import { createReducer, on } from '@ngrx/store';
import { AdminDataset } from '../../models/admin-dataset.model';
import * as AdminProjectsActions from './admin-projects.actions';

export interface AdminProjectsState {
  datasets: AdminDataset[];
  total: number;
  loading: boolean;
  error: string | null;
}

const initialState: AdminProjectsState = {
  datasets: [],
  total: 0,
  loading: false,
  error: null,
};

export const adminProjectsReducer = createReducer(
  initialState,
  on(AdminProjectsActions.loadAdminProjects, (state) => ({ ...state, loading: true, error: null })),
  on(AdminProjectsActions.loadAdminProjectsSuccess, (state, { datasets, total }) => ({
    ...state,
    datasets,
    total,
    loading: false,
  })),
  on(AdminProjectsActions.loadAdminProjectsFailure, (state, { error }) => ({
    ...state,
    loading: false,
    error,
  })),
  on(AdminProjectsActions.clearAdminProjects, () => initialState),
);
