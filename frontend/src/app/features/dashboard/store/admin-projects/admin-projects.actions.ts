import { createAction, props } from '@ngrx/store';
import { AdminDataset, AdminDatasetsParams } from '../../models/admin-dataset.model';

export const loadAdminProjects = createAction(
  '[Admin Projects] Load',
  props<{ params?: AdminDatasetsParams }>(),
);
export const loadAdminProjectsSuccess = createAction(
  '[Admin Projects] Load Success',
  props<{ datasets: AdminDataset[]; total: number }>(),
);
export const loadAdminProjectsFailure = createAction(
  '[Admin Projects] Load Failure',
  props<{ error: string }>(),
);
export const clearAdminProjects = createAction('[Admin Projects] Clear');
